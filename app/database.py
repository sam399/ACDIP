from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import MetaData, event, inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)


if "sqlite" in settings.DATABASE_URL:
    @event.listens_for(engine.sync_engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Create async session factory
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Declarative base class for models
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

Base = declarative_base(metadata=MetaData(naming_convention=NAMING_CONVENTION))


class DatabaseMigrationError(RuntimeError):
    """Raised when the database is not at the application's migration head."""


def migration_head() -> str:
    config = Config(str(settings.PROJECT_ROOT / "alembic.ini"))
    return ScriptDirectory.from_config(config).get_current_head()


async def verify_database_revision() -> None:
    """Fail fast when migrations have not been applied; never mutate schema."""
    expected = migration_head()
    async with engine.connect() as connection:
        tables = await connection.run_sync(lambda sync: inspect(sync).get_table_names())
        if "alembic_version" not in tables:
            raise DatabaseMigrationError(
                "Database is not managed by Alembic. Run `python -m alembic upgrade head`."
            )
        current = await connection.scalar(text("SELECT version_num FROM alembic_version"))
    if current != expected:
        raise DatabaseMigrationError(
            f"Database revision is {current or 'unset'}; expected {expected}. "
            "Run `python -m alembic upgrade head`."
        )

# Dependency to get db session in routes
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

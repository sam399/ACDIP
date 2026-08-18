# RESPOND-ER Architecture

The application is organized by responsibility while preserving the existing
SQLite schema and public HTTP endpoints.

## Package boundaries

- `app/main.py` assembles FastAPI, static files, lifespan, and routers only.
- `app/routers/` owns HTTP parsing, responses, and domain-specific endpoints.
- `app/services/` owns calculations and workflows independent of HTML.
- `app/models/` owns SQLAlchemy persistence models grouped by domain.
- `app/web.py` owns template paths and file-upload handling.
- `app/presenters.py` owns small HTML fragments returned directly to HTMX.
- `app/database.py` owns the engine, sessions, and schema initialization.

Routes should not create engines, parse environment variables, or implement
scoring algorithms. Models should not perform HTTP work or call external APIs.
Services should not return FastAPI response objects.

## Model organization

- `disasters.py`: disasters and infrastructure damage
- `emergencies.py`: citizen emergency requests and dispatch data
- `people.py`: missing people, family updates, personnel, and volunteers
- `resources.py`: inventory, donations, shelters, resources, and distributions
- `intelligence.py`: normalized HVI assessments and priority override history
- `common.py`: shared model helpers such as UTC timestamp creation

`app/models/__init__.py` is the stable public import surface. Callers should use
`from app.models import EmergencyRequest`, not import domain modules directly.

## Database policy

- `python seed.py` initializes only a new database and refuses existing tables.
- `python seed.py --reset` is explicitly destructive.
- `python seed_module2.py` is additive and idempotent.
- Pytest uses `.test_respond_er.db` and `.test_uploads`, deleting both afterward.
- Existing tables are never renamed or split without a migration and backup.

Alembic is the only schema-change mechanism. Application startup verifies that
the database revision matches migration head and fails with an actionable error
instead of changing tables automatically.

## Known schema debt

Shelter legacy capacity/contact columns were reconciled and removed in revision
`0003_shelters`. Revision `0004_f14_expand` added normalized one-to-one household
vulnerability assessments and append-only priority override history. Legacy F14
columns remain temporarily as a dual-write rollback mirror; a later contract
migration may remove them after the normalized path has been observed in use.

## Compatibility modules

`app/ai_service.py` and `app/vulnerability_service.py` re-export the new service
locations. New code should import `app.services.triage` and
`app.services.vulnerability`; the wrappers protect existing integrations.

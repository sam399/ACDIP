"""normalize shelter columns

Revision ID: 0003_shelters
Revises: 0002_reconcile
Create Date: 2026-08-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003_shelters"
down_revision: Union[str, None] = "0002_reconcile"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    conflicts = connection.execute(sa.text("""
        SELECT id FROM shelters
        WHERE (COALESCE(capacity_total, 0) > 0 AND COALESCE(capacity_beds, 0) > 0
               AND capacity_total != capacity_beds)
           OR (COALESCE(capacity_available, 0) > 0 AND COALESCE(available_beds, 0) > 0
               AND capacity_available != available_beds)
           OR (NULLIF(TRIM(contact_details), '') IS NOT NULL
               AND NULLIF(TRIM(contact_number), '') IS NOT NULL
               AND contact_details != contact_number)
           OR (NULLIF(TRIM(food_stock), '') IS NOT NULL AND COALESCE(food_stock_days, 0) > 0)
    """)).fetchall()
    if conflicts:
        raise RuntimeError(
            "Conflicting canonical and legacy shelter values must be reconciled before migration."
        )

    connection.execute(sa.text("""
        UPDATE shelters
        SET capacity_total = capacity_beds
        WHERE COALESCE(capacity_total, 0) = 0 AND COALESCE(capacity_beds, 0) > 0
    """))
    connection.execute(sa.text("""
        UPDATE shelters
        SET capacity_available = available_beds
        WHERE COALESCE(capacity_available, 0) = 0 AND COALESCE(available_beds, 0) > 0
    """))
    connection.execute(sa.text("""
        UPDATE shelters
        SET contact_details = contact_number
        WHERE NULLIF(TRIM(contact_details), '') IS NULL
          AND NULLIF(TRIM(contact_number), '') IS NOT NULL
    """))
    connection.execute(sa.text("""
        UPDATE shelters
        SET food_stock = CAST(food_stock_days AS TEXT) || ' days'
        WHERE NULLIF(TRIM(food_stock), '') IS NULL AND COALESCE(food_stock_days, 0) > 0
    """))

    with op.batch_alter_table("shelters", schema=None) as batch_op:
        batch_op.drop_column("capacity_beds")
        batch_op.drop_column("available_beds")
        batch_op.drop_column("food_stock_days")
        batch_op.drop_column("contact_number")


def downgrade() -> None:
    with op.batch_alter_table("shelters", schema=None) as batch_op:
        batch_op.add_column(sa.Column("contact_number", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("food_stock_days", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("available_beds", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("capacity_beds", sa.Integer(), nullable=True))

    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE shelters
        SET capacity_beds = capacity_total,
            available_beds = capacity_available,
            contact_number = contact_details,
            food_stock_days = 0
    """))

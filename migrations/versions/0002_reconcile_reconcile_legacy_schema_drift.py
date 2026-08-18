"""reconcile legacy schema drift

Revision ID: 0002_reconcile
Revises: 0001_baseline
Create Date: 2026-08-18 21:09:08.798013
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0002_reconcile'
down_revision: Union[str, None] = '0001_baseline'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    connection = op.get_bind()
    duplicate_roles = connection.execute(sa.text(
        "SELECT role_name FROM personnel_statuses GROUP BY role_name HAVING COUNT(*) > 1"
    )).fetchall()
    duplicate_items = connection.execute(sa.text(
        "SELECT item_name FROM supply_inventories GROUP BY item_name HAVING COUNT(*) > 1"
    )).fetchall()
    if duplicate_roles or duplicate_items:
        raise RuntimeError(
            "Cannot add unique constraints until duplicate personnel roles and inventory items are resolved."
        )

    with op.batch_alter_table('donations', schema=None) as batch_op:
        batch_op.alter_column('item_name',
               existing_type=sa.VARCHAR(),
               nullable=True)

    with op.batch_alter_table('personnel_statuses', schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f('uq_personnel_statuses_role_name'), ['role_name'])

    with op.batch_alter_table('shelters', schema=None) as batch_op:
        batch_op.alter_column('location',
               existing_type=sa.VARCHAR(),
               nullable=True)

    with op.batch_alter_table('supply_inventories', schema=None) as batch_op:
        batch_op.create_unique_constraint(batch_op.f('uq_supply_inventories_item_name'), ['item_name'])



def downgrade() -> None:
    connection = op.get_bind()
    null_donations = connection.scalar(sa.text(
        "SELECT COUNT(*) FROM donations WHERE item_name IS NULL"
    ))
    null_shelters = connection.scalar(sa.text(
        "SELECT COUNT(*) FROM shelters WHERE location IS NULL"
    ))
    if null_donations or null_shelters:
        raise RuntimeError(
            "Cannot restore legacy NOT NULL columns while donations or shelters contain null values."
        )

    with op.batch_alter_table('supply_inventories', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('uq_supply_inventories_item_name'), type_='unique')

    with op.batch_alter_table('shelters', schema=None) as batch_op:
        batch_op.alter_column('location',
               existing_type=sa.VARCHAR(),
               nullable=False)

    with op.batch_alter_table('personnel_statuses', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('uq_personnel_statuses_role_name'), type_='unique')

    with op.batch_alter_table('donations', schema=None) as batch_op:
        batch_op.alter_column('item_name',
               existing_type=sa.VARCHAR(),
               nullable=False)

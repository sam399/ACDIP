"""add support tickets table

Revision ID: bad524bb968f
Revises: ac5005b05cba
Create Date: 2026-08-18 22:36:07.097750
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'bad524bb968f'
down_revision: Union[str, None] = 'ac5005b05cba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'support_tickets',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='Open'),
        sa.Column('created_at', sa.DateTime(), nullable=False)
    )


def downgrade() -> None:
    op.drop_table('support_tickets')


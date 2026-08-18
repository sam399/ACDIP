"""add trust columns

Revision ID: ac5005b05cba
Revises: 0005_f16_recovery
Create Date: 2026-08-18 22:11:27.256695
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'ac5005b05cba'
down_revision: Union[str, None] = '0005_f16_recovery'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('emergency_requests', sa.Column('trust_score', sa.Integer(), nullable=False, server_default='100'))
    op.add_column('emergency_requests', sa.Column('trust_breakdown', sa.Text(), nullable=True))
    op.add_column('damage_reports', sa.Column('trust_score', sa.Integer(), nullable=False, server_default='100'))
    op.add_column('damage_reports', sa.Column('trust_breakdown', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('emergency_requests', 'trust_score')
    op.drop_column('emergency_requests', 'trust_breakdown')
    op.drop_column('damage_reports', 'trust_score')
    op.drop_column('damage_reports', 'trust_breakdown')


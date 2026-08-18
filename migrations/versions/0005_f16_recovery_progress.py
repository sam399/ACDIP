"""add Feature 16 recovery progress tables

Revision ID: 0005_f16_recovery
Revises: 0004_f14_expand
Create Date: 2026-08-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0005_f16_recovery"
down_revision: Union[str, None] = "0004_f14_expand"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "recovery_baselines",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("disaster_id", sa.Integer(), nullable=False),
        sa.Column("district", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("estimated_total", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("estimated_total > 0", name="positive_estimated_total"),
        sa.ForeignKeyConstraint(["disaster_id"], ["disasters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("disaster_id", "district", "category"),
    )
    op.create_index(op.f("ix_recovery_baselines_id"), "recovery_baselines", ["id"])
    op.create_table(
        "recovery_milestones",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("disaster_id", sa.Integer(), nullable=False),
        sa.Column("district", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("completed_count", sa.Integer(), nullable=False),
        sa.Column("milestone_date", sa.Date(), nullable=False),
        sa.Column("affected_area", sa.String(), nullable=False),
        sa.Column("verification_notes", sa.Text(), nullable=True),
        sa.Column("evidence_photo_url", sa.String(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("completed_count > 0", name="positive_completed_count"),
        sa.ForeignKeyConstraint(["disaster_id"], ["disasters.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_recovery_milestones_id"), "recovery_milestones", ["id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_recovery_milestones_id"), table_name="recovery_milestones")
    op.drop_table("recovery_milestones")
    op.drop_index(op.f("ix_recovery_baselines_id"), table_name="recovery_baselines")
    op.drop_table("recovery_baselines")

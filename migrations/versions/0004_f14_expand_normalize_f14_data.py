"""expand normalized Feature 14 data

Revision ID: 0004_f14_expand
Revises: 0003_shelters
Create Date: 2026-08-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004_f14_expand"
down_revision: Union[str, None] = "0003_shelters"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "household_vulnerability_assessments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("elderly_members", sa.Integer(), nullable=False),
        sa.Column("children", sa.Integer(), nullable=False),
        sa.Column("pregnant_women", sa.Integer(), nullable=False),
        sa.Column("members_with_disabilities", sa.Integer(), nullable=False),
        sa.Column("members_with_chronic_illness", sa.Integer(), nullable=False),
        sa.Column("raw_score", sa.Integer(), nullable=False),
        sa.Column("normalized_score", sa.Integer(), nullable=False),
        sa.Column("breakdown", sa.Text(), nullable=True),
        sa.Column("ai_priority", sa.String(), nullable=False),
        sa.Column("ai_urgency_score", sa.Integer(), nullable=False),
        sa.Column("final_priority_score", sa.Float(), nullable=False),
        sa.Column("calculated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["request_id"], ["emergency_requests.id"],
            name=op.f("fk_household_vulnerability_assessments_request_id_emergency_requests"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_household_vulnerability_assessments")),
        sa.UniqueConstraint(
            "request_id", name=op.f("uq_household_vulnerability_assessments_request_id")
        ),
    )
    op.create_table(
        "priority_overrides",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("request_id", sa.Integer(), nullable=False),
        sa.Column("previous_priority", sa.String(), nullable=True),
        sa.Column("new_priority", sa.String(), nullable=False),
        sa.Column("justification", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["request_id"], ["emergency_requests.id"],
            name=op.f("fk_priority_overrides_request_id_emergency_requests"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_priority_overrides")),
    )
    with op.batch_alter_table("priority_overrides") as batch_op:
        batch_op.create_index(batch_op.f("ix_priority_overrides_request_id"), ["request_id"])

    connection = op.get_bind()
    connection.execute(sa.text("""
        INSERT INTO household_vulnerability_assessments (
            request_id, elderly_members, children, pregnant_women,
            members_with_disabilities, members_with_chronic_illness,
            raw_score, normalized_score, breakdown, ai_priority,
            ai_urgency_score, final_priority_score, calculated_at
        )
        SELECT id, COALESCE(elderly_members, 0), COALESCE(children, 0),
               COALESCE(pregnant_women, 0), COALESCE(members_with_disabilities, 0),
               COALESCE(members_with_chronic_illness, 0), COALESCE(hvi_raw_score, 0),
               COALESCE(hvi_score, 0), hvi_breakdown, COALESCE(ai_priority, 'Medium'),
               COALESCE(ai_urgency_score, 50), COALESCE(final_priority_score, 30.0),
               COALESCE(override_updated_at, created_at, CURRENT_TIMESTAMP)
        FROM emergency_requests
    """))
    connection.execute(sa.text("""
        INSERT INTO priority_overrides (
            request_id, previous_priority, new_priority, justification, created_at
        )
        SELECT id, ai_priority, priority_override, override_justification,
               COALESCE(override_updated_at, created_at, CURRENT_TIMESTAMP)
        FROM emergency_requests
        WHERE priority_override IS NOT NULL AND override_justification IS NOT NULL
    """))

    request_count = connection.scalar(sa.text("SELECT COUNT(*) FROM emergency_requests"))
    assessment_count = connection.scalar(sa.text(
        "SELECT COUNT(*) FROM household_vulnerability_assessments"
    ))
    if request_count != assessment_count:
        raise RuntimeError("F14 backfill did not create exactly one assessment per request.")


def downgrade() -> None:
    with op.batch_alter_table("priority_overrides") as batch_op:
        batch_op.drop_index(batch_op.f("ix_priority_overrides_request_id"))
    op.drop_table("priority_overrides")
    op.drop_table("household_vulnerability_assessments")

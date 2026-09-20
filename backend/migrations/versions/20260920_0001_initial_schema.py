from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260920_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")

    op.create_table(
        "entities",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("kind", sa.String()),
        sa.Column("label", sa.String()),
        sa.Column("data", sa.JSON()),
    )
    op.create_index("ix_entities_kind", "entities", ["kind"])
    op.create_table(
        "edges",
        sa.Column("source", sa.String(), primary_key=True),
        sa.Column("relation", sa.String(), primary_key=True),
        sa.Column("target", sa.String(), primary_key=True),
    )
    op.create_table(
        "event_receipts",
        sa.Column("event_id", sa.String(), primary_key=True),
        sa.Column("digest", sa.String()),
        sa.Column("received_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "telemetry",
        sa.Column("device_timestamp", sa.DateTime(timezone=True), primary_key=True),
        sa.Column("event_id", sa.String(), primary_key=True),
        sa.Column("point_id", sa.String()),
        sa.Column("value", sa.Float()),
        sa.Column("unit", sa.String()),
        sa.Column("quality", sa.String()),
        sa.Column("source", sa.JSON()),
        sa.Column("received_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_telemetry_point_id", "telemetry", ["point_id"])
    op.create_index("ix_telemetry_point_time", "telemetry", ["point_id", "device_timestamp"])
    op.create_table(
        "current_values",
        sa.Column("point_id", sa.String(), primary_key=True),
        sa.Column("data", sa.JSON()),
    )
    op.create_table(
        "evaluation_outbox",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("data", sa.JSON()),
        sa.Column("done", sa.Boolean()),
    )
    op.create_index("ix_evaluation_outbox_done", "evaluation_outbox", ["done"])
    op.create_table(
        "rule_versions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("rule_id", sa.String()),
        sa.Column("version", sa.Integer()),
        sa.Column("config", sa.JSON()),
        sa.Column("status", sa.String()),
        sa.Column("created_at", sa.String()),
        sa.Column("activation", sa.JSON()),
    )
    op.create_index("ix_rule_versions_rule_id", "rule_versions", ["rule_id"])
    op.create_table(
        "evaluation_states",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("data", sa.JSON()),
    )
    op.create_table(
        "issues",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("version_id", sa.String()),
        sa.Column("equipment_id", sa.String()),
        sa.Column("status", sa.String()),
        sa.Column("data", sa.JSON()),
    )
    op.create_index("ix_issues_version_id", "issues", ["version_id"])
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("at", sa.String()),
        sa.Column("action", sa.String()),
        sa.Column("data", sa.JSON()),
    )
    op.create_table(
        "ai_requests",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("data", sa.JSON()),
    )
    op.create_table(
        "service_health",
        sa.Column("service", sa.String(), primary_key=True),
        sa.Column("data", sa.JSON()),
    )

    if bind.dialect.name == "postgresql":
        op.execute(
            "SELECT create_hypertable('telemetry', 'device_timestamp', "
            "if_not_exists => TRUE, migrate_data => TRUE)"
        )


def downgrade() -> None:
    op.drop_table("service_health")
    op.drop_table("ai_requests")
    op.drop_table("audit_events")
    op.drop_index("ix_issues_version_id", table_name="issues")
    op.drop_table("issues")
    op.drop_table("evaluation_states")
    op.drop_index("ix_rule_versions_rule_id", table_name="rule_versions")
    op.drop_table("rule_versions")
    op.drop_index("ix_evaluation_outbox_done", table_name="evaluation_outbox")
    op.drop_table("evaluation_outbox")
    op.drop_table("current_values")
    op.drop_index("ix_telemetry_point_time", table_name="telemetry")
    op.drop_index("ix_telemetry_point_id", table_name="telemetry")
    op.drop_table("telemetry")
    op.drop_table("event_receipts")
    op.drop_table("edges")
    op.drop_index("ix_entities_kind", table_name="entities")
    op.drop_table("entities")

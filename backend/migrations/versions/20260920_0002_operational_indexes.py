from collections.abc import Sequence

from alembic import op

revision: str = "20260920_0002"
down_revision: str | None = "20260920_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("ix_edges_source_relation", "edges", ["source", "relation"])
    op.create_index("ix_edges_target_relation", "edges", ["target", "relation"])
    op.drop_index("ix_evaluation_outbox_done", table_name="evaluation_outbox")
    op.create_index("ix_evaluation_outbox_pending_id", "evaluation_outbox", ["done", "id"])
    op.create_index("ix_rule_versions_status", "rule_versions", ["status"])
    op.create_index("ix_issues_status_equipment", "issues", ["status", "equipment_id"])
    op.create_index("ix_audit_events_action_id", "audit_events", ["action", "id"])


def downgrade() -> None:
    op.drop_index("ix_audit_events_action_id", table_name="audit_events")
    op.drop_index("ix_issues_status_equipment", table_name="issues")
    op.drop_index("ix_rule_versions_status", table_name="rule_versions")
    op.drop_index("ix_evaluation_outbox_pending_id", table_name="evaluation_outbox")
    op.create_index("ix_evaluation_outbox_done", "evaluation_outbox", ["done"])
    op.drop_index("ix_edges_target_relation", table_name="edges")
    op.drop_index("ix_edges_source_relation", table_name="edges")

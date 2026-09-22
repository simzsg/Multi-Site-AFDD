from collections.abc import Sequence

from alembic import op

revision: str = "20260920_0003"
down_revision: str | None = "20260920_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_index("ix_telemetry_point_time", table_name="telemetry")
    op.create_index(
        "uq_telemetry_point_time",
        "telemetry",
        ["point_id", "device_timestamp"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_telemetry_point_time", table_name="telemetry")
    op.create_index("ix_telemetry_point_time", "telemetry", ["point_id", "device_timestamp"])

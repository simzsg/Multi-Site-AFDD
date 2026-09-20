from alembic import context
from app.db import metadata


def run_migrations() -> None:
    connection = context.config.attributes["connection"]
    context.configure(connection=connection, target_metadata=metadata, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


run_migrations()

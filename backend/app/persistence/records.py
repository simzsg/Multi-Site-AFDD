from typing import Any

from sqlalchemy import Table
from sqlalchemy.engine import Connection


class RecordNotFound(LookupError):
    pass


def require_record(conn: Connection, table: Table, identity: str) -> dict[str, Any]:
    key = next(iter(table.primary_key))
    row = conn.execute(table.select().where(key == identity)).mappings().first()
    if row is None:
        raise RecordNotFound("Not found")
    return dict(row)

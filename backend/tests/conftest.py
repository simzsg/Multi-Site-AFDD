import pytest
from app import db, schema
from app.seed import seed


@pytest.fixture
def engine():
    engine = db.connect("sqlite:///:memory:")
    schema.upgrade(engine)
    seed(engine)
    yield engine
    engine.dispose()

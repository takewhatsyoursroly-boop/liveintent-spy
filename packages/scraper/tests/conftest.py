import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from liveintent_shared.models import Base

@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s

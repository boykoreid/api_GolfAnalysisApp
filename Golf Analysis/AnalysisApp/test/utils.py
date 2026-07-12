from fastapi.testclient import TestClient
from fastapi import status
from sqlalchemy import StaticPool, create_engine, text
from sqlalchemy.orm import sessionmaker
import pytest
from ..database import Base, get_db
from ..main import app
from ..models import Users, Rounds, Holes
from ..routers.auth import get_current_user, bcrypt_context
import datetime


SQLALCHEMY_DATABASE_URL = "sqlite:///./testdb.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={'check_same_thread': False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_current_user():
    return {'username': 'reidboykotest', 'id': 1, 'admin': True}


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    db = TestingSessionLocal()

    db.query(Holes).delete()
    db.query(Rounds).delete()
    db.query(Users).delete()

    db.commit()

    yield

    db.close()


@pytest.fixture
def test_user():
    user = Users(
        username='reidboykotest',
        email='reidboykotest@email.com',
        first_name='Reid',
        last_name='Boyko',
        hashed_password=bcrypt_context.hash('testpassword'),
        admin=True
    )

    db = TestingSessionLocal()
    db.add(user)
    db.commit()
    db.refresh(user)

    yield user #test runs here

    #teardown after test finishes
    db.delete(user)
    db.commit()
    db.close()


@pytest.fixture
def test_non_admin():
    user = Users(
        username='otherusertest',
        email='otherusertest@email.com',
        first_name='Reid',
        last_name='Boyko',
        hashed_password=bcrypt_context.hash('testpassword'),
        admin=False
    )

    db = TestingSessionLocal()
    db.add(user)
    db.commit()
    db.refresh(user)

    yield user #test runs here

    #teardown after test finishes
    db.delete(user)
    db.commit()
    db.close()


@pytest.fixture
def test_round(test_user):
    round = Rounds(
        user_id=test_user.id,
        date=datetime.date.today(),
        course_name='Edmonton Country Club',
        is_front_nine=True
    )

    db = TestingSessionLocal()
    db.add(round)
    db.commit()
    db.refresh(round)

    yield round

    db.delete(round)
    db.commit()
    db.close()

@pytest.fixture
def test_hole(test_round):
    hole = Holes(
        round_id=test_round.id,
        hole_number=1,
        par=4,
        score=4,
        putts=2,
        gir=True
    )

    db = TestingSessionLocal()
    db.add(hole)
    db.commit()
    db.refresh(hole)

    yield hole

    db.delete(hole)
    db.commit()
    db.close()


@pytest.fixture
def non_admin_override(test_non_admin):
    app.dependency_overrides[get_current_user] = lambda: {
        'username': test_non_admin.username,
        'id': test_non_admin.id,
        'admin': False
    }

    yield

    app.dependency_overrides[get_current_user] = override_get_current_user


@pytest.fixture
def no_user_override():
    app.dependency_overrides[get_current_user] = lambda: None

    yield

    app.dependency_overrides[get_current_user] = override_get_current_user
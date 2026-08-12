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
        season=datetime.date.today().year,
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
        gir=True,
        fairway_hit=True,
        penalty_strokes=0
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


### STATS FIXTURES
@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def stats_user(db):
    """
    Main user used for stats tests.
    """

    user = Users(
        username="statsuser",
        email="stats@test.com",
        first_name="Stats",
        last_name="User",
        hashed_password="hashedpassword",
        admin=False
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def stats_user_override(stats_user):

    app.dependency_overrides[get_current_user] = lambda: {
        "username": stats_user.username,
        "id": stats_user.id,
        "admin": False
    }

    yield

    app.dependency_overrides[get_current_user] = override_get_current_user


@pytest.fixture
def other_stats_user(db):
    """
    Second user used to make sure stats don't leak between users.
    """

    user = Users(
        username="otherstatsuser",
        email="otherstats@test.com",
        first_name="Other",
        last_name="User",
        hashed_password="hashedpassword",
        admin=False
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@pytest.fixture
def stats_rounds(db, stats_user):
    """
    Creates a fake golf history.

    Seasons:
        2025:
            Round 1 -> 45
            Round 2 -> 54

        2026:
            Round 3 -> 36

    Used for:
        - averages
        - season grouping
        - GIR %
        - putting stats
        - scoring trends
    """


    # ---------------------
    # 2025 ROUND 1
    # ---------------------

    round1 = Rounds(
        user_id=stats_user.id,
        date=datetime.date(2025, 5, 1),
        season=2025,
        course_name="Test Course",
        is_front_nine=True
    )


    # ---------------------
    # 2025 ROUND 2
    # ---------------------

    round2 = Rounds(
        user_id=stats_user.id,
        date=datetime.date(2025, 6, 1),
        season=2025,
        course_name="Test Course",
        is_front_nine=True
    )


    # ---------------------
    # 2026 ROUND 3
    # ---------------------

    round3 = Rounds(
        user_id=stats_user.id,
        date=datetime.date(2026, 5, 1),
        season=2026,
        course_name="Test Course",
        is_front_nine=True
    )


    # ---------------------
    # 2026 ROUND 4
    # ---------------------

    round4 = Rounds(
        user_id=stats_user.id,
        date=datetime.date(2026, 5, 1),
        season=2026,
        course_name="Test Course",
        is_front_nine=True
    )


    db.add_all([round1, round2, round3, round4])
    db.commit()

    db.refresh(round1)
    db.refresh(round2)
    db.refresh(round3)
    db.refresh(round4)


    # ---------------------
    # ROUND 1 HOLES
    #
    # Total:
    # score = 45
    # putts = 18
    # GIR = 1/9
    # Fairways Hit = 4/9
    # Penalty Strokes = 0
    # ---------------------

    round1_holes = [

    #The := (walrus) operator allows us to assign a variable within another expression. So it sets par, score and putts so we can calculate GIR
    Holes(
        round_id=round1.id,
        hole_number=i,
        par=(par := 5 if i == 5 else 4),
        score=(score := 5),
        putts=(putts := 2),
        gir=(score - putts) <= (par - 2),
        fairway_hit=i % 2 == 0,
        penalty_strokes=0,
    )

    for i in range(1, 10)

    ]


    # ---------------------
    # ROUND 2 HOLES
    #
    # Total:
    # score = 54
    # putts = 20
    # GIR = 0/9
    # Fairways Hit = 4/9
    # ---------------------

    round2_holes = [

        Holes(
            round_id=round2.id,
            hole_number=i,
            par=(par := 4),
            score=(score := 6),
            putts=(putts := 2 if i < 8 else 3),
            gir=(score - putts) <= (par - 2),
            fairway_hit=i <= 4,
            penalty_strokes=1 if i == 9 else 0
        )

        for i in range(1, 10)
    ]


    # ---------------------
    # ROUND 3 HOLES
    #
    # Total:
    # score = 36
    # putts = 13
    # GIR = 4/9
    # Fairways Hit = 9/9
    # ---------------------

    round3_holes = [

        Holes(
            round_id=round3.id,
            hole_number=i,
            par=(par := 4),
            score=(score := 4),
            putts=(putts := 1 if i <= 5 else 2),
            gir=(score - putts) <= (par - 2),
            fairway_hit=True,
            penalty_strokes=0
        )

        for i in range(1, 10)
    ]


    # ---------------------
    # ROUND 4 HOLES
    #
    # Total:
    # score = 36
    # putts = 14
    # GIR = 5/9
    # Fairways Hit = 1/1
    # ---------------------

    round4_holes = [

        Holes(
            round_id=round4.id,
            hole_number=i,
            par=(par := 4),
            score=(score := 4),
            putts=(putts := 1 if i <= 4 else 2),
            gir=(score - putts) <= (par - 2),
            fairway_hit=None if i != 4 else True,
            penalty_strokes=None if i != 4 else 1
        )

        for i in range(1, 10)
    ]


    holes = (
        round1_holes
        + round2_holes
        + round3_holes
        + round4_holes
    )


    db.add_all(holes)
    db.commit()


    return {
        "user": stats_user,
        "rounds": [
            round1,
            round2,
            round3,
            round4
        ],
        "holes": holes
    }

@pytest.fixture
def stats_round(stats_rounds):
    return stats_rounds['rounds'][0]


@pytest.fixture
def no_fairways_penalties_round(stats_rounds):
    return stats_rounds['rounds'][3]



@pytest.fixture
def other_user_round(db, other_stats_user):
    """
    Creates a round belonging to another user.

    Used to test that stats only include
    the authenticated user's data.
    """

    golf_round = Rounds(
        user_id=other_stats_user.id,
        date=datetime.date(2026, 5, 1),
        season=2026,
        course_name="Other Course",
        is_front_nine=True
    )

    db.add(golf_round)
    db.commit()

    db.refresh(golf_round)


    holes = [

        Holes(
            round_id=golf_round.id,
            hole_number=i,
            par=4,
            score=10,
            putts=4,
            gir=False,
            fairway_hit=False,
            penalty_strokes=5
        )

        for i in range(1,10)
    ]


    db.add_all(holes)
    db.commit()


    return {
        "user": other_stats_user,
        "round": golf_round,
        "holes": holes
    }
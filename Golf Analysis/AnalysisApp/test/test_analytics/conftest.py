from ..utils import *
import datetime
import pytest
from sqlalchemy import select, func
from ...routers.analytics import MIN_FAIRWAYS_TRACKED, MIN_PENALTIES_TRACKED, MIN_VECTOR_CONTRIBUTION, VARIANCE_THRESHOLD
from fastapi import HTTPException
import numpy as np
import random

def create_analytics_round(
    db,
    user_id,
    round_number,
    season=2026,
    ):

    golf_round = Rounds(
        user_id=user_id,
        date=datetime.date(2026, 5, round_number),
        season=season,
        course_name="Analytics Test Course",
        is_front_nine=True
    )

    db.add(golf_round)
    db.commit()
    db.refresh(golf_round)

    num_gir = random.randint(2, 7)
    gir_holes = random.sample(range(1, 10), num_gir)

    num_penalties = random.randint(0, 2)
    penalty_holes = random.sample(range(1, 10), num_penalties)

    num_fairways = random.randint(6, 9)
    fairway_holes = random.sample(range(1, 10), num_fairways)

    holes = []

    for hole_number in range(1, 10):

        par = 4

        score = random.randint(3,7)

        putts = random.randint(0, 4)

        gir = hole_number in gir_holes

        fairway_hit = hole_number in fairway_holes

        penalty_strokes = 1 if hole_number in penalty_holes else 0

        hole = Holes(
            round_id=golf_round.id,
            hole_number=hole_number,
            par=par,
            score=score,
            putts=putts,
            gir=gir,
            fairway_hit=fairway_hit,
            penalty_strokes=penalty_strokes
        )

        holes.append(hole)

    db.add_all(holes)
    db.commit()

    return golf_round


@pytest.fixture
def analytics_rounds(db, stats_user):
    rounds = []

    for round_number in range(1, 21):
        golf_round = create_analytics_round(
            db=db,
            user_id=stats_user.id,
            round_number=round_number
        )

        rounds.append(golf_round)

    return rounds


@pytest.fixture
def incomplete_fairway_rounds(db, stats_user):
    rounds = []

    for round_number in range(1, 21):
        golf_round = create_analytics_round(
            db=db,
            user_id=stats_user.id,
            round_number=round_number
        )

        rounds.append(golf_round)

    # Get the holes belonging to the 20th round
    holes = (
        db.query(Holes)
        .filter(Holes.round_id == rounds[-1].id)
        .all()
    )

    # Leave only 5 fairway values
    for hole in holes[5:]:
        hole.fairway_hit = None

    db.commit()

    return rounds


@pytest.fixture
def incomplete_penalty_rounds(db, stats_user):
    rounds = []

    for round_number in range(1, 21):
        golf_round = create_analytics_round(
            db=db,
            user_id=stats_user.id,
            round_number=round_number
        )

        rounds.append(golf_round)

    # Get the holes belonging to the 20th round
    holes = (
        db.query(Holes)
        .filter(Holes.round_id == rounds[-1].id)
        .all()
    )

    # Leave only 7 penalty values
    for hole in holes[7:]:
        hole.penalty_strokes = None

    db.commit()

    return rounds
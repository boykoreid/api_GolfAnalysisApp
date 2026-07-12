'''
Statistics and predictive analytics endpoints.

This module is currently under development and will eventually include:
- Round and user analytics
- GIR and putting trends
- Linear algebra based predictive models
'''


from fastapi import APIRouter, Depends, status, HTTPException, Path, Query
from ..models import Users, Rounds, Holes
from ..database import SessionLocal, get_db
from .auth import get_current_user
from typing import Annotated
from sqlalchemy.orm import Session
from sqlalchemy import Integer, case, func
from pydantic import BaseModel, Field
import datetime
from typing import Optional
from enum import Enum



router = APIRouter(
    prefix='/stats',
    tags=['stats']
)


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]   


class RoundStatsResponse(BaseModel):
    score: int
    holes_played: int
    gir: int
    gir_rate: float
    putts: int
    average_putts: float
    birdies: int
    pars: int
    bogeys: int
    double_or_worse: int
    par3_average: float | None # Bar means that we can either except a float or None
    par4_average: float | None
    par5_average: float | None


class TrendMetric(str, Enum):
    # Enum gives you a drop down option and str means that the dropdown is automatically formatted as a string when we use it

    gir = 'gir'
    putts = 'putts'
    avg_putts = 'avg_putts'



@router.get('/rounds/{round_id}', response_model=RoundStatsResponse)
async def round_stats_summary(db: db_dependency, user: user_dependency, round_id: int):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    round_model = db.query(Rounds).filter(Rounds.id == round_id, Rounds.user_id == user.get('id')).first()

    if round_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Round not found')
    
    #stats is a sqlalchemy row object. one() means sqlalchemy should expect one row, and to raise an exception if we do not get that
    stats = (
        db.query(
            # GENERAL
            func.sum(Holes.score).label('score'),
            func.count(Holes.id).label('holes_played'),

            # GIR
            func.sum(func.cast(Holes.gir, Integer)).label('gir'),
            (func.sum(func.cast(Holes.gir, Integer)) / func.count(Holes.id)).label('gir_rate'),

            # PUTTING
            func.sum(Holes.putts).label('putts'),
            (func.sum(Holes.putts) / func.count(Holes.id)).label('average_putts'),

            # SCORING
            func.sum(
                case((Holes.score - Holes.par == -1, 1), else_=0)).label('birdies'),
            func.sum(
                case((Holes.score - Holes.par == 0, 1), else_=0)).label('pars'),
            func.sum(
                case((Holes.score - Holes.par == 1, 1), else_=0)).label('bogeys'),
            func.sum(
                case((Holes.score - Holes.par > 1, 1), else_=0)).label('double_or_worse'),

            # BY PAR
            func.avg(Holes.score).filter(Holes.par == 3).label('par3_average'),
            func.avg(Holes.score).filter(Holes.par == 4).label('par4_average'),
            func.avg(Holes.score).filter(Holes.par == 5).label('par5_average')
        )
        .filter(Holes.round_id == round_id)
        .one()
    )

    return RoundStatsResponse(
        score=stats.score,
        holes_played=stats.holes_played,
        gir=stats.gir,
        gir_rate=stats.gir_rate,
        putts=stats.putts,
        average_putts=stats.average_putts,
        birdies=stats.birdies,
        pars=stats.pars,
        bogeys=stats.bogeys,
        double_or_worse=stats.double_or_worse,
        par3_average=stats.par3_average,
        par4_average=stats.par4_average,
        par5_average=stats.par5_average
    )



@router.get('/summary')
async def user_stats_summary(db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    rounds_played = (
        db.query(
            func.count(Rounds.id)
            .filter(Rounds.user_id == user.get('id'))
        ).scalar()
    )

    avg_score = (
        db.query(func.avg(Holes.score))
        .join(Rounds, Rounds.id == Holes.round_id)
        .filter(Rounds.user_id == user.get('id'))
        .scalar()
    )

    avg_putts = (
        db.query(func.avg(Holes.putts))
        .join(Rounds, Rounds.id == Holes.round_id)
        .filter(Rounds.user_id == user.get('id'))
        .scalar()
    )

    gir_rate = (
        db.query(func.sum(func.cast(Holes.gir, Integer)) / func.count(Holes.id))
        .join(Rounds, Rounds.id == Holes.round_id)
        .filter(Rounds.user_id == user.get('id'))
        .scalar()
    )

    best_round = (
        db.query(func.min(Rounds.score))
        .join(Rounds, Rounds.id == Holes.round_id)
        .filter(Rounds.user_id == user.get('id'))
        .scalar()
    )

    worst_round = (
        db.query(func.max(Rounds.score))
        .join(Rounds, Rounds.id == Holes.round_id)
        .filter(Rounds.user_id == user.get('id'))
        .scalar()
    )


@router.get('/par_breakdown')
async def user_stats_by_par(db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)


@router.get('/trends')
async def get_user_trends(db: db_dependency, 
                     user: user_dependency, 
                     metric: TrendMetric = Query(description='Specific x value metric that is used for graphing')):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
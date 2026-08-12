from fastapi import APIRouter, Depends, status, HTTPException, Query
from ..models import Rounds, Holes
from ..database import get_db
from .auth import get_current_user
from typing import Annotated
from sqlalchemy.orm import Session
from sqlalchemy import case, func, select
from pydantic import BaseModel
import datetime
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
    gir_percentage: float
    putts: int
    average_putts: float
    fairways_hit: int
    fairway_percentage: float | None
    penalty_strokes: int | None
    birdies: int
    pars: int
    bogeys: int
    double_or_worse: int
    par_3_average: float | None # Bar means that we can either except a float or None
    par_4_average: float | None
    par_5_average: float | None


class UserStatsSummaryResponse(BaseModel):
    season: int
    avg_score: float | None
    best_score: int | None
    worst_score: int | None
    rounds_played: int
    avg_putts: float | None
    fairway_percentage: float | None
    avg_penalty_strokes: float | None
    gir_percentage: float | None


class ByParStats(BaseModel):
    holes_played: int
    avg_score: float | None
    avg_putts: float | None
    gir_percentage: float | None
    fairway_percentage: float | None
    avg_penalty_strokes: float | None
    birdies: int
    pars: int
    bogeys: int
    double_or_worse: int


class SeasonParBreakdown(BaseModel):
    season: int
    par_3: ByParStats
    par_4: ByParStats
    par_5: ByParStats


class TrendMetric(str, Enum):
    # Enum gives you a drop down option and str means that the dropdown is automatically formatted as a string when we use it

    gir = "gir"
    avg_putts = "avg_putts"
    fairway_pct = 'fairway_pct'
    normalized_penalty_strokes = 'normalized_penalty_strokes'
    birdies = "birdies"
    pars = "pars"
    bogeys = "bogeys"
    double_or_worse = "double_or_worse"


class TrendResponse(BaseModel):
    round_date: datetime.date
    metric_value: float | None
    round_score_to_par: int
    num_recorded_holes: int



@router.get('/rounds/{round_id}', response_model=RoundStatsResponse, status_code=status.HTTP_200_OK)
async def round_stats_summary(db: db_dependency, user: user_dependency, round_id: int):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    round_model = db.query(Rounds).filter(Rounds.id == round_id, Rounds.user_id == user.get('id')).first()

    if round_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Round not found')
    
    query = (
        select(
            func.sum(Holes.score).label('score'),
            func.count(Holes.id).label('holes_played'),

            func.sum(case((Holes.gir == True, 1), else_=0)).label('gir'),
            (func.avg(case((Holes.gir == True, 1), else_=0)) * 100).label('gir_percentage'),

            func.avg(Holes.putts).label('avg_putts'),
            func.sum(Holes.putts).label('putts'),

            func.sum(case((Holes.fairway_hit == True, 1), else_=0)).label('fairways_hit'),
            (func.sum(case((Holes.fairway_hit == True, 1), else_=0)) 
             / func.nullif(func.count(Holes.fairway_hit), 0) * 100).label('fairway_pct'),

            func.sum(Holes.penalty_strokes).label('penalty_strokes'),

            func.sum(case((Holes.score - Holes.par == -1, 1), else_=0)).label('birdies'),
            func.sum(case((Holes.score - Holes.par == 0, 1), else_=0)).label('pars'),
            func.sum(case((Holes.score - Holes.par == 1, 1), else_=0)).label('bogeys'),
            func.sum(case((Holes.score - Holes.par >= 2, 1), else_=0)).label('double_or_worse'),

            func.avg(case((Holes.par == 3, Holes.score), else_=None)).label('par_3_avg'),
            func.avg(case((Holes.par == 4, Holes.score), else_=None)).label('par_4_avg'),
            func.avg(case((Holes.par == 5, Holes.score), else_=None)).label('par_5_avg')
        )
        .select_from(Rounds)
        .join(Holes, Holes.round_id == Rounds.id)
        .where(Rounds.id == round_id, Rounds.user_id == user.get('id'))
    )

    stats = db.execute(query).first()

    return RoundStatsResponse(
            score=stats.score,
            holes_played=stats.holes_played,
            gir=stats.gir,
            gir_percentage=round(stats.gir_percentage, 1),
            putts=stats.putts,
            average_putts=round(stats.avg_putts, 1),
            fairways_hit=stats.fairways_hit,
            fairway_percentage=round(stats.fairway_pct, 1) if stats.fairway_pct is not None else None,
            penalty_strokes=stats.penalty_strokes,
            birdies=stats.birdies,
            pars=stats.pars,
            bogeys=stats.bogeys,
            double_or_worse=stats.double_or_worse,
            par_3_average=round(stats.par_3_avg, 1) if stats.par_3_avg is not None else None,
            par_4_average=round(stats.par_4_avg, 1) if stats.par_4_avg is not None else None,
            par_5_average=round(stats.par_5_avg, 1) if stats.par_5_avg is not None else None
            )


@router.get('/summary', status_code=status.HTTP_200_OK, response_model=list[UserStatsSummaryResponse])
async def user_stats_summary(db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    #The subquery for the query below
    inner = (
        select(
                Rounds.season.label('season'),
                Rounds.id.label('round_id'),
                func.sum(Holes.score).label('round_score'),
                func.sum(Holes.putts).label('round_putts'),
                func.sum(case((Holes.gir == True, 1), else_=0)).label('girs_per_round'),
                func.sum(case((Holes.fairway_hit == True, 1), else_=0)).label('fairways_per_round'),
                func.count(Holes.fairway_hit).label('fairway_opportunities'),

                (
                    func.sum(Holes.penalty_strokes) #penalty strokes in the round
                    / 
                    func.nullif(
                        func.sum(case((Holes.penalty_strokes != None, 1), else_=0)), 0
                     ) #number of holes with recorded penalty strokes
                * func.count(Holes.id) #multiply it back by the number of holes to get the normalized penalty strokes per round
                ).label('normalized_penalties_per_round'),

                func.count(Holes.id).label('holes_played')
            )
            .select_from(Rounds)
            .join(Holes, Holes.round_id == Rounds.id)
            .where(Rounds.user_id == user.get('id'))
            .group_by(Rounds.season, Rounds.id)
            .subquery()
        )


    query = (
        select(
            inner.c.season.label('season'),
            func.avg(inner.c.round_score).label('avg_score'), #inner.c.round_score means 'use the column round_score from the inner subquery'
            func.min(inner.c.round_score).label('best_score'),
            func.max(inner.c.round_score).label('worst_score'),
            func.count(inner.c.round_id).label('rounds_played'),
            func.avg(inner.c.round_putts).label('avg_putts'),
            ((func.sum(inner.c.girs_per_round) / func.sum(inner.c.holes_played)) * 100).label('gir_percentage'),
            (func.sum(inner.c.fairways_per_round) / func.nullif(func.sum(inner.c.fairway_opportunities), 0) * 100).label('fairway_percentage'),
            func.avg(inner.c.normalized_penalties_per_round).label('avg_penalty_strokes')
        )
        .select_from(inner)
        .group_by(inner.c.season)
    )

    stats = db.execute(query).all()

    seasons = []

    for row in stats:
        season = UserStatsSummaryResponse(
            season = row.season,
            avg_score = round(row.avg_score, 1) if row.avg_score is not None else None,
            best_score = row.best_score,
            worst_score = row.worst_score,
            rounds_played = row.rounds_played,
            avg_putts = round(row.avg_putts, 1) if row.avg_putts is not None else None,
            gir_percentage = round(row.gir_percentage, 1) if row.gir_percentage is not None else None,
            fairway_percentage = round(row.fairway_percentage, 1) if row.fairway_percentage is not None else None,
            avg_penalty_strokes = round(row.avg_penalty_strokes, 2) if row.avg_penalty_strokes is not None else None
            )
        seasons.append(season)


    return seasons


@router.get('/summary/{season}', status_code=status.HTTP_200_OK, response_model=UserStatsSummaryResponse)
async def user_stats_summary_by_season(db: db_dependency, user: user_dependency, season: int):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    season_model = db.query(Rounds).filter(Rounds.season == season, Rounds.user_id == user.get('id')).all()

    if not season_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Season not found')
    
    #The subquery for the query below
    inner = (
        select(
                Rounds.season.label('season'),
                Rounds.id.label('round_id'),
                func.sum(Holes.score).label('round_score'),
                func.sum(Holes.putts).label('round_putts'),
                func.sum(case((Holes.gir == True, 1), else_=0)).label('girs_per_round'),
                func.sum(case((Holes.fairway_hit == True, 1), else_=0)).label('fairways_per_round'),
                func.sum(case((Holes.fairway_hit != None, 1), else_=0)).label('fairway_opportunities'),

                (
                    func.sum(Holes.penalty_strokes) #penalty strokes in the round
                    / 
                    func.nullif(
                        func.sum(case((Holes.penalty_strokes != None, 1), else_=0)), 0
                        ) #number of holes with recorded penalty strokes
                * func.count(Holes.id).label('holes_played') #multiply it back by the number of holes to get the normalized penalty strokes per round
                ).label('normalized_penalties_per_round'),

                func.count(Holes.id).label('holes_played')
            )
            .select_from(Rounds)
            .join(Holes, Holes.round_id == Rounds.id)
            .where(Rounds.user_id == user.get('id'), Rounds.season == season)
            .group_by(Rounds.id)
            .subquery()
        )


    query = (
        select(
            inner.c.season.label('season'),
            func.avg(inner.c.round_score).label('avg_score'), #inner.c.round_score means 'use the column round_score from the inner subquery'
            func.min(inner.c.round_score).label('best_score'),
            func.max(inner.c.round_score).label('worst_score'),
            func.count(inner.c.round_id).label('rounds_played'),
            func.avg(inner.c.round_putts).label('avg_putts'),
            ((func.sum(inner.c.girs_per_round) / func.sum(inner.c.holes_played)) * 100).label('gir_percentage'),
            (func.sum(inner.c.fairways_per_round) / func.nullif(func.sum(inner.c.fairway_opportunities), 0) * 100).label('fairway_percentage'),
            func.avg(inner.c.normalized_penalties_per_round).label('avg_penalty_strokes')
        )
        .select_from(inner)
        .group_by(inner.c.season)
    )

    stats = db.execute(query).one()

    return UserStatsSummaryResponse(
        season = stats.season,
        avg_score = round(stats.avg_score, 1) if stats.avg_score is not None else None,
        best_score = stats.best_score,
        worst_score = stats.worst_score,
        rounds_played = stats.rounds_played,
        avg_putts = round(stats.avg_putts, 1) if stats.avg_putts is not None else None,
        gir_percentage = round(stats.gir_percentage, 1) if stats.gir_percentage is not None else None,
        fairway_percentage = round(stats.fairway_percentage, 1) if stats.fairway_percentage is not None else None,
        avg_penalty_strokes = round(stats.avg_penalty_strokes, 2) if stats.avg_penalty_strokes is not None else None
        )


@router.get('/par_breakdown', status_code=status.HTTP_200_OK, response_model=list[SeasonParBreakdown])
async def user_stats_by_par(db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    query = (
        select(
            Rounds.season.label('season'),
            Holes.par.label('par'),
            func.count(Holes.id).label('holes_played'),
            func.avg(Holes.score).label('avg_score'),
            func.avg(Holes.putts).label('avg_putts'),
            ((func.sum(case((Holes.gir == True, 1), else_=0)) / func.count(Holes.id)) * 100).label('gir_percentage'),

            (
                (func.sum(case((Holes.fairway_hit == True, 1), else_=0)) 
                / 
                func.nullif(func.sum(case((Holes.fairway_hit != None, 1), else_=0)), 0)) * 100
            )
            .label('fairway_percentage'),

            (
                func.sum(Holes.penalty_strokes) 
                / 
                func.nullif(func.sum(case((Holes.penalty_strokes != None, 1), else_=0)), 0)
            )
            .label('avg_penalty_strokes'),

            func.sum(case((Holes.score - Holes.par == -1, 1), else_=0)).label('birdies'),
            func.sum(case((Holes.score - Holes.par == 0, 1), else_=0)).label('pars'),
            func.sum(case((Holes.score - Holes.par == 1, 1), else_=0)).label('bogeys'),
            func.sum(case((Holes.score - Holes.par >= 2, 1), else_=0)).label('double_or_worse')
        )
        .select_from(Rounds)
        .join(Holes, Holes.round_id == Rounds.id)
        .where(Rounds.user_id == user.get('id'))
        .group_by(Rounds.season, Holes.par)
    )

    stats = db.execute(query).all()

    season_stats = {}

    for row in stats:
        if row.season not in season_stats:
            season_stats[row.season] = {}

        season_stats[row.season][row.par] = ByParStats(
            holes_played=row.holes_played,
            avg_score=round(row.avg_score, 1) if row.avg_score is not None else None,
            avg_putts=round(row.avg_putts, 1) if row.avg_putts is not None else None,
            gir_percentage=round(row.gir_percentage, 1) if row.gir_percentage is not None else None,
            fairway_percentage=round(row.fairway_percentage, 1) if row.fairway_percentage is not None else None,
            avg_penalty_strokes=round(row.avg_penalty_strokes, 2) if row.avg_penalty_strokes is not None else None,
            birdies=row.birdies,
            pars=row.pars,
            bogeys=row.bogeys,
            double_or_worse=row.double_or_worse
        )

    empty_par_stats = lambda: ByParStats(
        holes_played=0,
        avg_score=None,
        avg_putts=None,
        gir_percentage=None,
        fairway_percentage=None,
        avg_penalty_strokes=None,
        birdies=0,
        pars=0,
        bogeys=0,
        double_or_worse=0
    )

    responses = []

    for season, pars in season_stats.items():
        responses.append(
            SeasonParBreakdown(
                season=season,
                par_3=pars.get(3, empty_par_stats()),
                par_4=pars.get(4, empty_par_stats()),
                par_5=pars.get(5, empty_par_stats())
            )
        )

    return responses


@router.get('/par_breakdown/{season}', status_code=status.HTTP_200_OK, response_model=SeasonParBreakdown)
async def user_stats_by_par_by_season(db: db_dependency, user: user_dependency, season: int):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    season_model = db.query(Rounds).filter(Rounds.season == season, Rounds.user_id == user.get('id')).all()

    if not season_model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Season not found')
    
    query = (
        select(
            Rounds.season.label('season'),
            Holes.par.label('par'),
            func.count(Holes.id).label('holes_played'),
            func.avg(Holes.score).label('avg_score'),
            func.avg(Holes.putts).label('avg_putts'),
            ((func.sum(case((Holes.gir == True, 1), else_=0)) / func.count(Holes.id)) * 100).label('gir_percentage'),

            (
                (func.sum(case((Holes.fairway_hit == True, 1), else_=0)) 
                / 
                func.nullif(func.sum(case((Holes.fairway_hit != None, 1), else_=0)), 0)) * 100
            ).label('fairway_percentage'),

            (
                func.sum(Holes.penalty_strokes) 
                / 
                func.nullif(func.sum(case((Holes.penalty_strokes != None, 1), else_=0)), 0)
            ).label('avg_penalty_strokes'),

            func.sum(case((Holes.score - Holes.par == -1, 1), else_=0)).label('birdies'),
            func.sum(case((Holes.score - Holes.par == 0, 1), else_=0)).label('pars'),
            func.sum(case((Holes.score - Holes.par == 1, 1), else_=0)).label('bogeys'),
            func.sum(case((Holes.score - Holes.par >= 2, 1), else_=0)).label('double_or_worse')
        )
        .select_from(Rounds)
        .join(Holes, Holes.round_id == Rounds.id)
        .where(Rounds.user_id == user.get('id'), Rounds.season == season)
        .group_by(Holes.par)
    )

    stats = db.execute(query).all()

    empty_par_stats = lambda: ByParStats(
            holes_played=0,
            avg_score=None,
            avg_putts=None,
            gir_percentage=None,
            fairway_percentage=None,
            avg_penalty_strokes=None,
            birdies=0,
            pars=0,
            bogeys=0,
            double_or_worse=0
        )

    season_stats = {}

    season_stats['season'] = season

    for row in stats:    
        season_stats[row.par] = ByParStats(
            holes_played=row.holes_played,
            avg_score=round(row.avg_score, 1) if row.avg_score is not None else None,
            avg_putts=round(row.avg_putts, 1) if row.avg_putts is not None else None,
            gir_percentage=round(row.gir_percentage, 1) if row.gir_percentage is not None else None,
            fairway_percentage=round(row.fairway_percentage, 1) if row.fairway_percentage is not None else None,
            avg_penalty_strokes=round(row.avg_penalty_strokes, 2) if row.avg_penalty_strokes is not None else None,
            birdies=row.birdies,
            pars=row.pars,
            bogeys=row.bogeys,
            double_or_worse=row.double_or_worse
        )

    return SeasonParBreakdown(
        season=season_stats.get('season'),
        par_3=season_stats.get(3, empty_par_stats()),
        par_4=season_stats.get(4, empty_par_stats()),
        par_5=season_stats.get(5, empty_par_stats())
        )


@router.get('/trends', status_code=status.HTTP_200_OK, response_model=list[TrendResponse])
async def get_user_trends(db: db_dependency, 
                     user: user_dependency, 
                     metric: TrendMetric = Query(description='Specific x value metric that is used for graphing'),
                     season: int | None = Query(default=None)
                     ):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    if metric == TrendMetric.gir:
        metric_column = func.sum(case((Holes.gir == True, 1), else_=0))
        num_recorded_holes = func.count(Holes.id)
    
    elif metric == TrendMetric.avg_putts:
        metric_column = func.avg(Holes.putts)
        num_recorded_holes = func.count(Holes.id)

    elif metric == TrendMetric.fairway_pct:
        metric_column = (
                (
                    func.sum(case((Holes.fairway_hit == True, 1), else_=0))
                    /
                    func.nullif(
                        func.sum(case((Holes.fairway_hit != None, 1), else_=0)), 
                        0
                    )
                )
                * 100
            )
        num_recorded_holes = func.sum(case((Holes.fairway_hit != None, 1), else_=0))

    elif metric == TrendMetric.normalized_penalty_strokes:
        metric_column = (
            (
                func.sum(Holes.penalty_strokes)
                /
                func.nullif(
                    func.sum(case((Holes.penalty_strokes != None, 1), else_=0)),
                    0
                )
            )
            * func.count(Holes.id)
        )
        num_recorded_holes = func.sum(case((Holes.penalty_strokes != None, 1), else_=0))

    elif metric == TrendMetric.birdies:
        metric_column = func.sum(case((Holes.score - Holes.par == -1, 1), else_=0))
        num_recorded_holes = func.count(Holes.id)

    elif metric == TrendMetric.pars:
        metric_column = func.sum(case((Holes.score - Holes.par == 0, 1), else_=0))
        num_recorded_holes = func.count(Holes.id)

    elif metric == TrendMetric.bogeys:
        metric_column = func.sum(case((Holes.score - Holes.par == 1, 1), else_=0))
        num_recorded_holes = func.count(Holes.id)

    elif metric == TrendMetric.double_or_worse:
        metric_column = func.sum(case((Holes.score - Holes.par >= 2, 1), else_=0))
        num_recorded_holes = func.count(Holes.id)

    query = (
        select(
            Rounds.date.label('round_date'),
            metric_column.label('metric_value'),
            (func.sum(Holes.score) - func.sum(Holes.par)).label('round_score_to_par'),
            num_recorded_holes.label('num_recorded_holes')

        )
        .select_from(Rounds)
        .join(Holes, Holes.round_id == Rounds.id)
        .where(Rounds.user_id == user.get('id'))
        .group_by(Rounds.id)
        .having(num_recorded_holes >= 6) #filter out rounds which have too many missing values
    )

    if season is not None:
        query = query.where(Rounds.season == season)

    stats = db.execute(query).all()

    trend_response = []

    for row in stats:
        trend_response.append(TrendResponse(
            round_date=row.round_date,
            metric_value=round(row.metric_value, 1),
            round_score_to_par=row.round_score_to_par,
            num_recorded_holes=row.num_recorded_holes
        ))

    return trend_response



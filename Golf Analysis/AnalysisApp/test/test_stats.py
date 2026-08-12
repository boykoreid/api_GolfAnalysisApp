from .utils import *
from pprint import pprint

def test_round_stats_summary(stats_user_override, stats_round):
    response = client.get(f'stats/rounds/{stats_round.id}')

    assert response.status_code == status.HTTP_200_OK

    assert response.json() == {
            'score': 45,
            'holes_played': 9,
            'gir': 1,
            'gir_percentage': 11.1,
            'putts': 18,
            'average_putts': 2.0,
            'fairways_hit': 4,
            'fairway_percentage': 44.4,
            'penalty_strokes': 0,
            'birdies': 0,
            'pars': 1,
            'bogeys': 8,
            'double_or_worse': 0,
            'par_3_average': None,
            'par_4_average': 5.0,
            'par_5_average': 5.0
    }


def test_round_stats_summary_null_value_handling(stats_user_override, no_fairways_penalties_round):
    response = client.get(f'stats/rounds/{no_fairways_penalties_round.id}')
    
    assert response.status_code == status.HTTP_200_OK

    assert response.json() == {
            'score': 36,
            'holes_played': 9,
            'gir': 5,
            'gir_percentage': 55.6,
            'putts': 14,
            'average_putts': 1.6,
            'fairways_hit': 1,
            'fairway_percentage': 100.0,
            'penalty_strokes': 1,
            'birdies': 0,
            'pars': 9,
            'bogeys': 0,
            'double_or_worse': 0,
            'par_3_average': None,
            'par_4_average': 4.0,
            'par_5_average': None
    }


def test_round_stats_summary_not_authenticated(no_user_override, stats_round):
    response = client.get(f'stats/rounds/{stats_round.id}')
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_round_stats_summary_round_not_found(stats_user_override, stats_round):
    response = client.get(f'stats/rounds/999')
        
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Round not found'}


def test_user_stats_summary(stats_user_override, stats_rounds):
    response = client.get('/stats/summary')

    assert response.status_code == status.HTTP_200_OK

    assert response.json() == [
        {
            'season': 2025,
            'avg_score': 49.5,
            'best_score': 45,
            'worst_score': 54,
            'rounds_played': 2,
            'avg_putts': 19.0,
            'gir_percentage': 5.6,
            'fairway_percentage': 44.4,
            'avg_penalty_strokes': 0.50
        },
        {
            'season': 2026,
            'avg_score': 36.0,
            'best_score': 36,
            'worst_score': 36,
            'rounds_played': 2,
            'avg_putts': 13.5,
            'gir_percentage': 50.0,
            'fairway_percentage': 100.0,
            'avg_penalty_strokes': 4.50
        }
    ]


def test_user_stats_summary_not_authenticated(no_user_override, stats_rounds):
    response = client.get('/stats/summary')
   
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_user_stats_summary_empty_history(stats_user_override):
    response = client.get('/stats/summary')

    assert response.json() == []


def test_user_stats_summary_only_current_user(stats_user_override, stats_rounds, other_user_round):
    response = client.get('/stats/summary')
    
    assert response.status_code == status.HTTP_200_OK

    assert response.json() == [
        {
            'season': 2025,
            'avg_score': 49.5,
            'best_score': 45,
            'worst_score': 54,
            'rounds_played': 2,
            'avg_putts': 19.0,
            'gir_percentage': 5.6,
            'fairway_percentage': 44.4,
            'avg_penalty_strokes': 0.50
        },
        {
            'season': 2026,
            'avg_score': 36.0,
            'best_score': 36,
            'worst_score': 36,
            'rounds_played': 2,
            'avg_putts': 13.5,
            'gir_percentage': 50.0,
            'fairway_percentage': 100.0,
            'avg_penalty_strokes': 4.50
        }
    ]


def test_user_stats_summary_by_season(stats_user_override, stats_rounds):
    response = client.get('/stats/summary/2025')

    assert response.status_code == status.HTTP_200_OK

    assert response.json() == {
        'season': 2025,
        'avg_score': 49.5,
        'best_score': 45,
        'worst_score': 54,
        'rounds_played': 2,
        'avg_putts': 19.0,
        'gir_percentage': 5.6,
        'fairway_percentage': 44.4,
        'avg_penalty_strokes': 0.50
    }


def test_user_stats_summary_by_season_only_current_user(stats_user_override, stats_rounds, other_user_round):
    response = client.get('/stats/summary/2025')
    
    assert response.status_code == status.HTTP_200_OK

    assert response.json() == {
        'season': 2025,
        'avg_score': 49.5,
        'best_score': 45,
        'worst_score': 54,
        'rounds_played': 2,
        'avg_putts': 19.0,
        'gir_percentage': 5.6,
        'fairway_percentage': 44.4,
        'avg_penalty_strokes': 0.50
    }


def test_user_stats_summary_by_season_not_authenticated(no_user_override, stats_rounds):
    response = client.get('/stats/summary/2025')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_user_stats_summary_by_season_season_not_found(stats_user_override, stats_rounds):
    response = client.get('/stats/summary/9999')
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Season not found'}


def test_user_stats_by_par(stats_user_override, stats_rounds):
    response = client.get('/stats/par_breakdown')

    assert response.status_code == status.HTTP_200_OK

    pprint(response.json())

    assert response.json() == [
        {
            'season': 2025,

            'par_3': {
                'holes_played': 0,
                'avg_score': None,
                'avg_putts': None,
                'gir_percentage': None,
                'fairway_percentage': None,
                'avg_penalty_strokes': None,
                'birdies': 0,
                'pars': 0,
                'bogeys': 0,
                'double_or_worse': 0
                },

            'par_4': {
                'holes_played': 17,
                'avg_score': 5.5,
                'avg_putts': 2.1,
                'gir_percentage': 0.0,
                'fairway_percentage': 47.1,
                'avg_penalty_strokes': 0.06,
                'birdies': 0,
                'pars': 0,
                'bogeys': 8,
                'double_or_worse': 9
                },

            'par_5': {
                'holes_played': 1,
                'avg_score': 5.0,
                'avg_putts': 2.0,
                'gir_percentage': 100.0,
                'fairway_percentage': 0.0,
                'avg_penalty_strokes': 0.00,
                'birdies': 0,
                'pars': 1,
                'bogeys': 0,
                'double_or_worse': 0
                }
        },
        {
            'season': 2026,

            'par_3':{
                'holes_played': 0,
                'avg_score': None,
                'avg_putts': None,
                'gir_percentage': None,
                'fairway_percentage': None,
                'avg_penalty_strokes': None,
                'birdies': 0,
                'pars': 0,
                'bogeys': 0,
                'double_or_worse': 0
                },

            'par_4':{
                'holes_played': 18,
                'avg_score': 4.0,
                'avg_putts': 1.5,
                'gir_percentage': 50.0,
                'fairway_percentage': 100.0,
                'avg_penalty_strokes': 0.10,
                'birdies': 0,
                'pars': 18,
                'bogeys': 0,
                'double_or_worse': 0
                },

            'par_5':{
                'holes_played': 0,
                'avg_score': None,
                'avg_putts': None,
                'gir_percentage': None,
                'fairway_percentage': None,
                'avg_penalty_strokes': None,
                'birdies': 0,
                'pars': 0,
                'bogeys': 0,
                'double_or_worse': 0
                }
        }
    ]


def test_user_stats_by_par_not_authenticated(no_user_override, stats_rounds):
    response = client.get('/stats/par_breakdown')
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_user_stats_by_par_empty_history(stats_user_override):
    response = client.get('/stats/par_breakdown')

    assert response.json() == []


def test_user_stats_by_par_by_season(stats_user_override, stats_rounds):
    response = client.get(f'stats/par_breakdown/2025')

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        'season': 2025,

        'par_3': {
            'holes_played': 0,
            'avg_score': None,
            'avg_putts': None,
            'gir_percentage': None,
            'fairway_percentage': None,
            'avg_penalty_strokes': None,
            'birdies': 0,
            'pars': 0,
            'bogeys': 0,
            'double_or_worse': 0
            },

        'par_4': {
            'holes_played': 17,
            'avg_score': 5.5,
            'avg_putts': 2.1,
            'gir_percentage': 0.0,
            'fairway_percentage': 47.1,
            'avg_penalty_strokes': 0.06,
            'birdies': 0,
            'pars': 0,
            'bogeys': 8,
            'double_or_worse': 9
            },

        'par_5': {
            'holes_played': 1,
            'avg_score': 5.0,
            'avg_putts': 2.0,
            'gir_percentage': 100.0,
            'fairway_percentage': 0.0,
            'avg_penalty_strokes': 0.00,
            'birdies': 0,
            'pars': 1,
            'bogeys': 0,
            'double_or_worse': 0
            }
    }


def test_user_stats_by_par_by_season_not_authenticated(no_user_override, stats_rounds):
    response = client.get(f'stats/par_breakdown/2025')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_user_stats_by_par_by_season_season_not_found(stats_user_override, stats_rounds):
    response = client.get(f'stats/par_breakdown/9999')

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Season not found'}


def test_user_trends_gir(stats_user_override, stats_rounds):
    response = client.get('/stats/trends?metric=gir')

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "round_date": "2025-05-01",
            "metric_value": 1.0,
            "round_score_to_par": 8,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2025-06-01",
            "metric_value": 0.0,
            "round_score_to_par": 18,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2026-05-01",
            "metric_value": 4.0,
            "round_score_to_par": 0,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2026-05-01",
            "metric_value": 5.0,
            "round_score_to_par": 0,
            "num_recorded_holes": 9
        }
    ]


def test_user_trends_avg_putts(stats_user_override, stats_rounds):
    response = client.get('/stats/trends?metric=avg_putts')
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "round_date": "2025-05-01",
            "metric_value": 2.0,
            "round_score_to_par": 8,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2025-06-01",
            "metric_value": 2.2,
            "round_score_to_par": 18,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2026-05-01",
            "metric_value": 1.4,
            "round_score_to_par": 0,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2026-05-01",
            "metric_value": 1.6,
            "round_score_to_par": 0,
            "num_recorded_holes": 9
        }
    ]

 
def test_user_trends_fairway_pct(stats_user_override, stats_rounds):
    response = client.get('/stats/trends?metric=fairway_pct')
    
    assert response.status_code == status.HTTP_200_OK
    pprint(response.json())
    assert response.json() == [
        {
            "round_date": "2025-05-01",
            "metric_value": 44.4,
            "round_score_to_par": 8,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2025-06-01",
            "metric_value": 44.4,
            "round_score_to_par": 18,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2026-05-01",
            "metric_value": 100.0,
            "round_score_to_par": 0,
            "num_recorded_holes": 9
        }
    ]


def test_user_trends_normalized_penalty_strokes(stats_user_override, stats_rounds):
    response = client.get('/stats/trends?metric=normalized_penalty_strokes')
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "round_date": "2025-05-01",
            "metric_value": 0.0,
            "round_score_to_par": 8,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2025-06-01",
            "metric_value": 1.0,
            "round_score_to_par": 18,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2026-05-01",
            "metric_value": 0.0,
            "round_score_to_par": 0,
            "num_recorded_holes": 9
        }
    ]


def test_user_trends_birdies(stats_user_override, stats_rounds):
    response = client.get('/stats/trends?metric=birdies')
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "round_date": "2025-05-01",
            "metric_value": 0.0,
            "round_score_to_par": 8,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2025-06-01",
            "metric_value": 0.0,
            "round_score_to_par": 18,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2026-05-01",
            "metric_value": 0.0,
            "round_score_to_par": 0,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2026-05-01",
            "metric_value": 0.0,
            "round_score_to_par": 0,
            "num_recorded_holes": 9
        }
    ]


def test_user_trends_pars(stats_user_override, stats_rounds):
    response = client.get('/stats/trends?metric=pars')
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "round_date": "2025-05-01",
            "metric_value": 1.0,
            "round_score_to_par": 8,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2025-06-01",
            "metric_value": 0.0,
            "round_score_to_par": 18,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2026-05-01",
            "metric_value": 9,
            "round_score_to_par": 0,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2026-05-01",
            "metric_value": 9,
            "round_score_to_par": 0,
            "num_recorded_holes": 9
        }
    ]

def test_user_trends_bogeys(stats_user_override, stats_rounds):
    response = client.get('/stats/trends?metric=bogeys')
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "round_date": "2025-05-01",
            "metric_value": 8.0,
            "round_score_to_par": 8,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2025-06-01",
            "metric_value": 0.0,
            "round_score_to_par": 18,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2026-05-01",
            "metric_value": 0.0,
            "round_score_to_par": 0,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2026-05-01",
            "metric_value": 0.0,
            "round_score_to_par": 0,
            "num_recorded_holes": 9
        }
    ]


def test_user_trends_double_or_worse(stats_user_override, stats_rounds):
    response = client.get('/stats/trends?metric=double_or_worse')
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "round_date": "2025-05-01",
            "metric_value": 0.0,
            "round_score_to_par": 8,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2025-06-01",
            "metric_value": 9.0,
            "round_score_to_par": 18,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2026-05-01",
            "metric_value": 0.0,
            "round_score_to_par": 0,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2026-05-01",
            "metric_value": 0.0,
            "round_score_to_par": 0,
            "num_recorded_holes": 9
        }
    ]


def test_user_trends_season_gir(stats_user_override, stats_rounds):
    response = client.get('/stats/trends?metric=gir&season=2025')
   
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "round_date": "2025-05-01",
            "metric_value": 1.0,
            "round_score_to_par": 8,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2025-06-01",
            "metric_value": 0.0,
            "round_score_to_par": 18,
            "num_recorded_holes": 9
        }
    ]


def test_user_trends_season_avg_putts(stats_user_override, stats_rounds):
    response = client.get('/stats/trends?metric=avg_putts&season=2025')
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "round_date": "2025-05-01",
            "metric_value": 2.0,
            "round_score_to_par": 8,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2025-06-01",
            "metric_value": 2.2,
            "round_score_to_par": 18,
            "num_recorded_holes": 9
        }
    ]

 
def test_user_trends_season_fairway_pct(stats_user_override, stats_rounds):
    response = client.get('/stats/trends?metric=fairway_pct&season=2025')
   
    assert response.status_code == status.HTTP_200_OK
    pprint(response.json())
    assert response.json() == [
        {
            "round_date": "2025-05-01",
            "metric_value": 44.4,
            "round_score_to_par": 8,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2025-06-01",
            "metric_value": 44.4,
            "round_score_to_par": 18,
            "num_recorded_holes": 9
        }
    ]


def test_user_trends_season_normalized_penalty_strokes(stats_user_override, stats_rounds):
    response = client.get('/stats/trends?metric=normalized_penalty_strokes&season=2025')
    
    assert response.status_code == status.HTTP_200_OK

    pprint(response.json())
    assert response.json() == [
        {
            "round_date": "2025-05-01",
            "metric_value": 0.0,
            "round_score_to_par": 8,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2025-06-01",
            "metric_value": 1.0,
            "round_score_to_par": 18,
            "num_recorded_holes": 9
        }
    ]

def test_user_trends_season_birdies(stats_user_override, stats_rounds):
    response = client.get('/stats/trends?metric=birdies&season=2025')
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "round_date": "2025-05-01",
            "metric_value": 0.0,
            "round_score_to_par": 8,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2025-06-01",
            "metric_value": 0.0,
            "round_score_to_par": 18,
            "num_recorded_holes": 9
        }
    ]


def test_user_trends_season_pars(stats_user_override, stats_rounds):
    response = client.get('/stats/trends?metric=pars&season=2025')
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "round_date": "2025-05-01",
            "metric_value": 1.0,
            "round_score_to_par": 8,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2025-06-01",
            "metric_value": 0.0,
            "round_score_to_par": 18,
            "num_recorded_holes": 9
        }
    ]


def test_user_trends_season_bogeys(stats_user_override, stats_rounds):
    response = client.get('/stats/trends?metric=bogeys&season=2025')
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "round_date": "2025-05-01",
            "metric_value": 8.0,
            "round_score_to_par": 8,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2025-06-01",
            "metric_value": 0.0,
            "round_score_to_par": 18,
            "num_recorded_holes": 9
        }
    ]


def test_user_trends_season_double_or_worse(stats_user_override, stats_rounds):
    response = client.get('/stats/trends?metric=double_or_worse&season=2025')
    
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            "round_date": "2025-05-01",
            "metric_value": 0.0,
            "round_score_to_par": 8,
            "num_recorded_holes": 9
        },
        {
            "round_date": "2025-06-01",
            "metric_value": 9.0,
            "round_score_to_par": 18,
            "num_recorded_holes": 9
        }
    ]


def test_user_trends_not_authenticated(no_user_override, stats_rounds):
    response = client.get('/stats/trends?metric=gir')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_user_trends_empty_history(stats_user_override):
    response = client.get('/stats/trends?metric=gir')

    assert response.json() == []
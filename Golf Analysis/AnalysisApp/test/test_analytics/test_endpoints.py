from .conftest import *



def test_linear_score_model_summary_base(db, analytics_rounds, stats_user):
    response = client.get('/analytics/linear_score_model/summary?season=2026&model_type=base')
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["model"] == "base"
    assert data["season"] == 2026
    assert isinstance(data["summary"], str)
    assert isinstance(data["coefficients"], dict)
    assert all(isinstance(value, float) for value in data["coefficients"].values())

    assert "putts" in data["coefficients"]
    assert "gir" in data["coefficients"]

    assert "putt" in data["summary"]
    assert "green in regulation" in data["summary"]


def test_linear_score_model_summary_extended(db, analytics_rounds, stats_user):
    response = client.get('/analytics/linear_score_model/summary?season=2026&model_type=extended')
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["model"] == "extended"
    assert data["season"] == 2026
    assert isinstance(data["summary"], str)
    assert isinstance(data["coefficients"], dict)
    assert all(isinstance(value, float) for value in data["coefficients"].values())

    assert "putts" in data["coefficients"]
    assert "gir" in data["coefficients"]
    assert "fairways" in data["coefficients"]

    assert "putt" in data["summary"]
    assert "green in regulation" in data["summary"]
    assert "fairway hit" in data["summary"]


def test_linear_score_model_summary_full(db, analytics_rounds, stats_user):
    response = client.get('/analytics/linear_score_model/summary?season=2026&model_type=full')
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert data["model"] == "full"
    assert data["season"] == 2026
    assert isinstance(data["summary"], str)
    assert isinstance(data["coefficients"], dict)
    assert all(isinstance(value, float) for value in data["coefficients"].values())

    assert "putts" in data["coefficients"]
    assert "gir" in data["coefficients"]
    assert "fairways" in data["coefficients"]
    assert "penalty_strokes" in data["coefficients"]

    assert "putt" in data["summary"]
    assert "green in regulation" in data["summary"]
    assert "fairway hit" in data["summary"]
    assert "penalty stroke" in data["summary"]


def test_linear_score_model_summary_not_authenticated(db, analytics_rounds, no_user_override):
    response = client.get('/analytics/linear_score_model/summary?season=2026&model_type=base')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_linear_score_model_summary_season_not_found(db, analytics_rounds, stats_user):
    response = client.get('/analytics/linear_score_model/summary?season=9999&model_type=base')
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Season not found'}


def test_linear_score_model_summary_not_enough_fairway_data(db, incomplete_fairway_rounds, stats_user):
    response = client.get('/analytics/linear_score_model/summary?season=2026&model_type=full')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'detail': 'To run the model, you must have at least 20 rounds with applicable data'}


def test_linear_score_model_summary_not_enough_penalty_data(db, incomplete_penalty_rounds, stats_user):
    response = client.get('/analytics/linear_score_model/summary?season=2026&model_type=full')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'detail': 'To run the model, you must have at least 20 rounds with applicable data'}


def test_linear_score_model_diagnostics_base(db, analytics_rounds, stats_user):
    response = client.get('/analytics/linear_score_model/diagnostics?season=2026&model_type=base')
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert isinstance(data['regression_equation'], str)
    assert isinstance(data['intercept'], float)
    assert isinstance(data['coefficients'], dict)

    assert all(isinstance(value, float) for value in data["coefficients"].values())
    assert all(isinstance(score, (int, float)) for score in data['actual_scores'])
    assert all(isinstance(score, (int, float)) for score in data['predicted_scores'])

    assert isinstance(data['mse'], float)
    assert isinstance(data['rmse'], float)
    assert data['mse'] >= 0
    assert data['rmse'] >= 0
    assert data['rmse'] == pytest.approx(data['mse'] ** 0.5, abs=0.01)

    assert data['rounds_used'] == 20
    assert data['rounds_used'] == len(data['actual_scores'])
    assert data['rounds_used'] == len(data['predicted_scores'])

    assert data['regression_equation']
    assert data['regression_equation'].startswith("Score = ")

    assert set(data["coefficients"]) == {"putts", "gir"}



def test_linear_score_model_diagnostics_extended(db, analytics_rounds, stats_user):
    response = client.get('/analytics/linear_score_model/diagnostics?season=2026&model_type=extended')
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    
    assert isinstance(data['regression_equation'], str)
    assert isinstance(data['intercept'], float)
    assert isinstance(data['coefficients'], dict)

    assert all(isinstance(value, float) for value in data["coefficients"].values())
    assert all(isinstance(score, (int, float)) for score in data['actual_scores'])
    assert all(isinstance(score, (int, float)) for score in data['predicted_scores'])

    assert isinstance(data['mse'], float)
    assert isinstance(data['rmse'], float)
    assert data['mse'] >= 0
    assert data['rmse'] >= 0
    assert data['rmse'] == pytest.approx(data['mse'] ** 0.5, abs=0.01)

    assert data['rounds_used'] == 20
    assert data['rounds_used'] == len(data['actual_scores'])
    assert data['rounds_used'] == len(data['predicted_scores'])

    assert data['regression_equation']
    assert data['regression_equation'].startswith("Score = ")

    assert set(data["coefficients"]) == {"putts", "gir", "fairways"}



def test_linear_score_model_diagnostics_full(db, analytics_rounds, stats_user):
    response = client.get('/analytics/linear_score_model/diagnostics?season=2026&model_type=full')
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    
    assert isinstance(data['regression_equation'], str)
    assert isinstance(data['intercept'], float)
    assert isinstance(data['coefficients'], dict)

    assert all(isinstance(value, float) for value in data["coefficients"].values())
    assert all(isinstance(score, (int, float)) for score in data['actual_scores'])
    assert all(isinstance(score, (int, float)) for score in data['predicted_scores'])

    assert isinstance(data['mse'], float)
    assert isinstance(data['rmse'], float)
    assert data['mse'] >= 0
    assert data['rmse'] >= 0
    assert data['rmse'] == pytest.approx(data['mse'] ** 0.5, abs=0.01)

    assert data['rounds_used'] == 20
    assert data['rounds_used'] == len(data['actual_scores'])
    assert data['rounds_used'] == len(data['predicted_scores'])

    assert data['regression_equation']
    assert data['regression_equation'].startswith("Score = ")

    assert set(data["coefficients"]) == {
        "putts",
        "gir",
        "fairways",
        "penalty_strokes"
    }


def test_linear_score_model_diagnostics_not_authenticated(db, analytics_rounds, no_user_override):
    response = client.get('/analytics/linear_score_model/diagnostics?season=2026&model_type=base')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_linear_score_model_diagnostics_season_not_found(db, analytics_rounds, stats_user):
    response = client.get('/analytics/linear_score_model/diagnostics?season=9999&model_type=base')
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Season not found'}


def test_linear_score_model_diagnostics_not_enough_fairway_data(db, incomplete_fairway_rounds, stats_user):
    response = client.get('/analytics/linear_score_model/diagnostics?season=2026&model_type=full')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'detail': 'To run the model, you must have at least 20 rounds with applicable data'}


def test_linear_score_model_diagnostics_not_enough_penalty_data(db, incomplete_penalty_rounds, stats_user):
    response = client.get('/analytics/linear_score_model/diagnostics?season=2026&model_type=full')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'detail': 'To run the model, you must have at least 20 rounds with applicable data'}


def test_pattern_model_summary_base(db, analytics_rounds, stats_user):
    response = client.get('/analytics/pattern_model/summary?season=2026&model_type=base')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'detail': 'Pattern analysis is not supported for the base model'}


def test_pattern_model_summary_extended(db, analytics_rounds, stats_user):
    response = client.get('/analytics/pattern_model/summary?season=2026&model_type=extended')
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert isinstance(data, dict)
    assert len(data) >= 1

    for pattern, summary in data.items():
        assert pattern.startswith("pattern ")
        assert isinstance(summary, str)
        assert summary


def test_pattern_model_summary_full(db, analytics_rounds, stats_user):
    response = client.get('/analytics/pattern_model/summary?season=2026&model_type=full')
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert isinstance(data, dict)
    assert len(data) >= 1

    for pattern, summary in data.items():
        assert pattern.startswith("pattern ")
        assert isinstance(summary, str)
        assert summary


def test_pattern_model_summary_not_authenticated(db, analytics_rounds, no_user_override):
    response = client.get('/analytics/pattern_model/summary?season=2026&model_type=extended')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_pattern_model_summary_season_not_found(db, analytics_rounds, stats_user):
    response = client.get('/analytics/pattern_model/summary?season=9999&model_type=extended')
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Season not found'}


def test_pattern_model_summary_not_enough_fairway_data(db, incomplete_fairway_rounds, stats_user):
    response = client.get('/analytics/pattern_model/summary?season=2026&model_type=full')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'detail': 'To run the model, you must have at least 20 rounds with applicable data'}


def test_pattern_model_summary_not_enough_penalty_data(db, incomplete_penalty_rounds, stats_user):
    response = client.get('/analytics/pattern_model/summary?season=2026&model_type=full')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'detail': 'To run the model, you must have at least 20 rounds with applicable data'}


def test_pattern_model_diagnostics_base(db, analytics_rounds, stats_user):
    response = client.get('/analytics/pattern_model/diagnostics?season=2026&model_type=base')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'detail': 'Pattern analysis is not supported for the base model'}


def test_pattern_model_diagnostics_extended(db, analytics_rounds, stats_user):
    response = client.get('/analytics/pattern_model/diagnostics?season=2026&model_type=extended')
    assert response.status_code == status.HTTP_200_OK

    data = response.json()

    assert isinstance(data, dict)
    assert len(data) >= 1

    for pattern, pattern_data in data.items():
        assert pattern.startswith("pattern_")

        assert isinstance(pattern_data["strength"], float)
        assert isinstance(pattern_data["explained_variance"], float)
        assert isinstance(pattern_data["cumulative_variance"], float)
        assert isinstance(pattern_data["weights"], dict)

        assert pattern_data["strength"] >= 0
        assert 0 <= pattern_data["explained_variance"] <= 1
        assert 0 <= pattern_data["cumulative_variance"] <= 1

        assert set(pattern_data["weights"]) == {
            "putts",
            "gir",
            "fairways"
        }

        assert all(
            isinstance(weight, float)
            for weight in pattern_data["weights"].values()
        )

    explained = [
        pattern_data["explained_variance"]
        for pattern_data in data.values()
    ]

    cumulative = [
        pattern_data["cumulative_variance"]
        for pattern_data in data.values()
    ]

    assert cumulative == sorted(cumulative)
    assert cumulative[-1] <= 1
    assert sum(explained) == pytest.approx(cumulative[-1], abs=0.002)


def test_pattern_model_diagnostics_full(db, analytics_rounds, stats_user):
    response = client.get('/analytics/pattern_model/diagnostics?season=2026&model_type=full')
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    
    assert isinstance(data, dict)
    assert len(data) >= 1

    for pattern, pattern_data in data.items():
        assert pattern.startswith("pattern_")

        assert isinstance(pattern_data["strength"], float)
        assert isinstance(pattern_data["explained_variance"], float)
        assert isinstance(pattern_data["cumulative_variance"], float)
        assert isinstance(pattern_data["weights"], dict)

        assert pattern_data["strength"] >= 0
        assert 0 <= pattern_data["explained_variance"] <= 1
        assert 0 <= pattern_data["cumulative_variance"] <= 1

        assert set(pattern_data["weights"]) == {
            "putts",
            "gir",
            "fairways",
            'penalty_strokes'
        }

        assert all(
            isinstance(weight, float)
            for weight in pattern_data["weights"].values()
        )

    explained = [
        pattern_data["explained_variance"]
        for pattern_data in data.values()
    ]

    cumulative = [
        pattern_data["cumulative_variance"]
        for pattern_data in data.values()
    ]

    assert cumulative == sorted(cumulative)
    assert cumulative[-1] <= 1
    assert sum(explained) == pytest.approx(cumulative[-1], abs=0.002)


def test_pattern_model_diagnostics_not_authenticated(db, analytics_rounds, no_user_override):
    response = client.get('/analytics/pattern_model/diagnostics?season=2026&model_type=extended')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_pattern_model_diagnostics_season_not_found(db, analytics_rounds, stats_user):
    response = client.get('/analytics/pattern_model/diagnostics?season=9999&model_type=extended')
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Season not found'}


def test_pattern_model_diagnostics_not_enough_fairway_data(db, incomplete_fairway_rounds, stats_user):
    response = client.get('/analytics/pattern_model/diagnostics?season=2026&model_type=full')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'detail': 'To run the model, you must have at least 20 rounds with applicable data'}


def test_pattern_model_diagnostics_not_enough_penalty_data(db, incomplete_penalty_rounds, stats_user):
    response = client.get('/analytics/pattern_model/diagnostics?season=2026&model_type=full')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'detail': 'To run the model, you must have at least 20 rounds with applicable data'}


def test_predict_base_irrelevant_fairway_request(db, analytics_rounds, stats_user):
    request_data_1 = {   
        'putts': 20,
        'gir': 3,
        'fairways': 5
        }

    request_data_2 = {
        'putts': 20,
        'gir': 3,
        'fairways': 9
    }
    
    response1 = client.post('/analytics/predict?season=2026&model_type=base', json=request_data_1)
    response2 = client.post('/analytics/predict?season=2026&model_type=base', json=request_data_2)
    assert response1.status_code == status.HTTP_200_OK
    assert response2.status_code == status.HTTP_200_OK

    data = response1.json()

    assert isinstance(data["predicted score"], float)
    assert data["predicted score"] > 0

    # make sure we arent accidentally using an abritrary fairway request field in our calculations
    # our base model should not use fairways at all
    assert response1.json() == response2.json() 


def test_predict_base_different_inputs(db, analytics_rounds, stats_user):
    request_data_1 = {   
        'putts': 20,
        'gir': 3,
        }

    request_data_2 = {
        'putts': 20,
        'gir': 5
    }
    
    response1 = client.post('/analytics/predict?season=2026&model_type=base', json=request_data_1)
    response2 = client.post('/analytics/predict?season=2026&model_type=base', json=request_data_2)
    assert response1.status_code == status.HTTP_200_OK
    assert response2.status_code == status.HTTP_200_OK

    data = response1.json()

    assert isinstance(data["predicted score"], float)
    assert data["predicted score"] > 0

    # make sure we arent accidentally using an abritrary fairway request field in our calculations
    # our base model should not use fairways at all
    assert response1.json() != response2.json() 


def test_predict_extended_irrelevant_penalty_request(db, analytics_rounds, stats_user):
    request_data_1 = {   
        'putts': 20,
        'gir': 3,
        'fairways': 5,
        'penalty_strokes': 2
        }

    request_data_2 = {   
        'putts': 20,
        'gir': 3,
        'fairways': 5,
        'penalty_strokes': 5
        }
    
    response1 = client.post('/analytics/predict?season=2026&model_type=extended', json=request_data_1)
    response2 = client.post('/analytics/predict?season=2026&model_type=extended', json=request_data_2)
    assert response1.status_code == status.HTTP_200_OK
    assert response2.status_code == status.HTTP_200_OK

    data = response1.json()

    assert isinstance(data["predicted score"], float)
    assert data["predicted score"] > 0

    # make sure we arent accidentally using an abritrary penalty request field in our calculations
    # our extended model should not use penalties at all
    assert response1.json() == response2.json() 


def test_predict_extended_different_inputs(db, analytics_rounds, stats_user):
    request_data_1 = {   
        'putts': 20,
        'gir': 3,
        'fairways': 5
        }

    request_data_2 = {   
        'putts': 20,
        'gir': 5,
        'fairways': 7
        }
    
    response1 = client.post('/analytics/predict?season=2026&model_type=extended', json=request_data_1)
    response2 = client.post('/analytics/predict?season=2026&model_type=extended', json=request_data_2)
    assert response1.status_code == status.HTTP_200_OK
    assert response2.status_code == status.HTTP_200_OK

    data = response1.json()

    assert isinstance(data["predicted score"], float)
    assert data["predicted score"] > 0

    # make sure we arent accidentally using an abritrary penalty request field in our calculations
    # our extended model should not use penalties at all
    assert response1.json() != response2.json() 


def test_predict_full(db, analytics_rounds, stats_user):
    request_data_1 = {
        'putts': 20,
        'gir': 3,
        'fairways': 5,
        'penalty_strokes': 2
    }

    request_data_2 = {
        'putts': 20,
        'gir': 3,
        'fairways': 9,
        'penalty_strokes': 5
    }

    response1 = client.post(
        '/analytics/predict?season=2026&model_type=full',
        json=request_data_1
    )
    response2 = client.post(
        '/analytics/predict?season=2026&model_type=full',
        json=request_data_2
    )

    assert response1.status_code == status.HTTP_200_OK
    assert response2.status_code == status.HTTP_200_OK

    data1 = response1.json()
    data2 = response2.json()

    assert isinstance(data1["predicted score"], float)
    assert data1["predicted score"] > 0

    assert isinstance(data2["predicted score"], float)
    assert data2["predicted score"] > 0

    assert data1["predicted score"] != data2["predicted score"]


def test_predict_not_authenticated(db, analytics_rounds, no_user_override):
    request_data = {   
        'putts': 20,
        'gir': 3,
        'fairways': 5,
        'penalty_strokes': 2
        }

    response = client.post('/analytics/predict?season=2026&model_type=base', json=request_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_predict_season_not_found(db, analytics_rounds, stats_user):
    request_data = {   
        'putts': 20,
        'gir': 3,
        'fairways': 5,
        'penalty_strokes': 2
        }

    response = client.post('/analytics/predict?season=9999&model_type=base', json=request_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Season not found'}


def test_predict_bad_extended_request(db, analytics_rounds, stats_user):
    request_data = {   
        'putts': 20,
        'gir': 3
        }

    response = client.post('/analytics/predict?season=2026&model_type=extended', json=request_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'detail': 'Please enter a valid number for fairways'}


def test_predict_bad_full_request(db, analytics_rounds, stats_user):
    request_data = {   
        'putts': 20,
        'gir': 3,
        'fairways': 5
        }

    response = client.post('/analytics/predict?season=2026&model_type=full', json=request_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'detail': 'Please enter a valid number for either fairways or penalty strokes'}


from .conftest import *
from ...routers.analytics import query_model, linear_score_model, pattern_analysis, pattern_summary_generator, ModelType


def test_analytics_rounds_fixture(analytics_rounds, db):
    assert len(analytics_rounds) == 20

    for golf_round in analytics_rounds:
        holes = (
            db.query(Holes)
            .filter(Holes.round_id == golf_round.id)
            .all()
        )

        assert len(holes) == 9


def test_analytics_rounds_have_enough_fairway_data(
    analytics_rounds,
    db
):
    for golf_round in analytics_rounds:

        query = (
            select(func.count(Holes.id))
            .where(
                Holes.round_id == golf_round.id,
                Holes.fairway_hit != None
            )
        )

        fairway_count = db.scalar(query)

        assert fairway_count >= MIN_FAIRWAYS_TRACKED


def test_analytics_rounds_have_enough_penalty_data(
        analytics_rounds,
        db
):
    for golf_round in analytics_rounds:
        query = (
            select(func.count(Holes.id))
            .where(
                Holes.round_id == golf_round.id,
                Holes.penalty_strokes != None
            )
        )

        penalty_count = db.scalar(query)

        assert penalty_count >= MIN_PENALTIES_TRACKED


def test_analytics_rounds_belong_to_test_user(analytics_rounds, stats_user):
    for golf_round in analytics_rounds:
        assert golf_round.user_id == stats_user.id


def test_query_model_base(db, stats_user, analytics_rounds):
    rows, feature_names = query_model(
        db,
        {"id": stats_user.id},
        2026,
        ModelType.base
    )

    assert len(rows) == 20
    assert feature_names == ["putts", "gir"]


def test_query_model_extended(db, stats_user, analytics_rounds):
    rows, feature_names = query_model(
            db,
            {"id": stats_user.id},
            2026,
            ModelType.extended
        )

    assert len(rows) == 20
    assert feature_names == ["putts", "gir", 'fairways']


def test_query_model_full(db, stats_user, analytics_rounds):
    rows, feature_names = query_model(
            db,
            {"id": stats_user.id},
            2026,
            ModelType.full
        )

    assert len(rows) == 20
    assert feature_names == ["putts", "gir", 'fairways', 'penalty_strokes']


def test_linear_score_model_base(db, analytics_rounds, stats_user):
    rows, feature_names = query_model(
        db,
        {"id": stats_user.id},
        2026,
        ModelType.base
    )

    A, coefficients, b, variable_columns = linear_score_model(rows)

    assert A.shape == (20, 3)
    assert coefficients.shape == (3,)
    assert b.shape == (20,)


def test_linear_score_model_extended(db, analytics_rounds, stats_user):
    rows, feature_names = query_model(
        db,
        {"id": stats_user.id},
        2026,
        ModelType.extended
    )

    A, coefficients, b, variable_columns = linear_score_model(rows)

    assert A.shape == (20, 4)
    assert coefficients.shape == (4,)
    assert b.shape == (20,)


def test_linear_score_model_full(db, analytics_rounds, stats_user):
    rows, feature_names = query_model(
        db,
        {"id": stats_user.id},
        2026,
        ModelType.full
    )

    A, coefficients, b, variable_columns = linear_score_model(rows)

    assert A.shape == (20, 5)
    assert coefficients.shape == (5,)
    assert b.shape == (20,)


def test_linear_score_model_predictions_base(
    analytics_rounds,
    db,
    stats_user
):
    rows, _ = query_model(
        db,
        {"id": stats_user.id},
        2026,
        ModelType.base
    )

    A, coefficients, b, variable_columns = linear_score_model(rows)

    predictions = A @ coefficients

    assert predictions.shape == b.shape
    assert np.all(np.isfinite(predictions))


def test_linear_score_model_predictions_extended(
    analytics_rounds,
    db,
    stats_user
):
    rows, _ = query_model(
        db,
        {"id": stats_user.id},
        2026,
        ModelType.extended
    )

    A, coefficients, b, variable_columns = linear_score_model(rows)

    predictions = A @ coefficients

    assert predictions.shape == b.shape
    assert np.all(np.isfinite(predictions))


def test_linear_score_model_predictions_full(
    analytics_rounds,
    db,
    stats_user
):
    rows, _ = query_model(
        db,
        {"id": stats_user.id},
        2026,
        ModelType.full
    )

    A, coefficients, b, variable_columns = linear_score_model(rows)

    predictions = A @ coefficients

    assert predictions.shape == b.shape
    assert np.all(np.isfinite(predictions))


def test_linear_score_model_rejects_singular_data():
    rows = [
        (10, 2, 40),
        (10, 2, 40),
        (10, 2, 40),
        (10, 2, 40),
    ]

    with pytest.raises(HTTPException) as exc_info: #this allows us to to test the exception without calling the endpoint
        linear_score_model(rows)

    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == (
    "Unable to generate model. Your data does not contain enough variation."
)


def test_linear_score_model_removes_singular_column():
    rows = [
        (15, 2, 7, 48),
        (18, 2, 6, 41),
        (17, 2, 2, 46),
        (22, 2, 8, 42),
    ]

    A, coefficients, b, variable_columns = linear_score_model(rows)

    assert A.shape == (4, 3) #ensure we still added the intercept column but removed the column with all 2's
    assert coefficients.shape == (3,)
    assert b.shape == (4,)
    assert np.array_equal(variable_columns, np.array([True, False, True]))


def test_pattern_analysis_extended(analytics_rounds, db, stats_user):
    rows, _ = query_model(
        db,
        {"id": stats_user.id},
        2026,
        ModelType.extended
    )

    eigenvectors, singular_values, explained_variance, cumulative_variance = pattern_analysis(rows)

    assert eigenvectors.shape == (3, 3)
    assert singular_values.shape == (3,)
    assert len(explained_variance) == 3
    assert cumulative_variance.shape == (3,)


def test_pattern_analysis_full(analytics_rounds, db, stats_user):
    rows, _ = query_model(
        db,
        {"id": stats_user.id},
        2026,
        ModelType.full
    )

    eigenvectors, singular_values, explained_variance, cumulative_variance = (
        pattern_analysis(rows)
    )

    assert eigenvectors.shape == (4, 4)
    assert singular_values.shape == (4,)
    assert len(explained_variance) == 4
    assert cumulative_variance.shape == (4,)


def test_pattern_analysis_explained_variance_extended(
    analytics_rounds,
    db,
    stats_user
):
    rows, _ = query_model(
        db,
        {"id": stats_user.id},
        2026,
        ModelType.extended
    )

    _, _, explained_variance, cumulative_variance = pattern_analysis(rows)

    assert np.isclose(np.sum(explained_variance), 1.0)
    assert np.isclose(cumulative_variance[-1], 1.0)


def test_pattern_analysis_explained_variance_full(
    analytics_rounds,
    db,
    stats_user
):
    rows, _ = query_model(
        db,
        {"id": stats_user.id},
        2026,
        ModelType.full
    )

    _, _, explained_variance, cumulative_variance = pattern_analysis(rows)

    assert np.isclose(np.sum(explained_variance), 1.0)
    assert np.isclose(cumulative_variance[-1], 1.0)


def test_pattern_analysis_singular_values_are_descending(
    analytics_rounds,
    db,
    stats_user
):
    rows, _ = query_model(
        db,
        {"id": stats_user.id},
        2026,
        ModelType.extended
    )

    _, singular_values, _, _ = pattern_analysis(rows)

    assert np.all(
        singular_values[:-1] >= singular_values[1:]
    )


def test_pattern_summary_generator_mixed_features():
    pattern_data = {
        "explained_variance": 0.65,
        "features": {
            "positive": {
                "gir": 0.72,
                "fairways": 0.55
            },
            "negative": {
                "putts": -0.68
            }
        }
    }

    summary = pattern_summary_generator("1", pattern_data)

    assert summary == r"Pattern 1 explains 65% of the variation across the selected performance metrics. This pattern represents a relationship where greens in regulation, fairways hit tend to increase while putts tend to decrease, and vice versa. This pattern is primarily driven by greens in regulation"


def test_pattern_summary_generator_positive_features():
    pattern_data = {
        "explained_variance": 0.65,
        "features": {
            "positive": {
                "gir": 0.72,
                "fairways": 0.55
            },
            "negative": {}
        }
    }

    summary = pattern_summary_generator("1", pattern_data)

    assert summary == r"Pattern 1 explains 65% of the variation across the selected performance metrics. This pattern is characterized by greens in regulation, fairways hit tending to increase together. This pattern is primarily driven by greens in regulation"


def test_pattern_summary_generator_negative_features():
    pattern_data = {
        "explained_variance": 0.65,
        "features": {
            "positive": {},
            "negative": {
                "putts": -0.68
            }
        }
    }

    summary = pattern_summary_generator("1", pattern_data)

    assert summary == r"Pattern 1 explains 65% of the variation across the selected performance metrics. This pattern is characterized by putts tending to decrease together. This pattern is primarily driven by putts"


def test_pattern_summary_generator_no_features():
    pattern_data = {
        "explained_variance": 0.65,
        "features": {
            "positive": {},
            "negative": {}
        }
    }

    summary = pattern_summary_generator("1", pattern_data)

    assert summary == r"Pattern 1 explains 65% of the variation across the selected performance metrics, but no major contributing features were identified. "


def test_pattern_summary_generator_strongest_negative_feature():
    pattern_data = {
        "explained_variance": 0.65,
        "features": {
            "positive": {
                "gir": 0.55
            },
            "negative": {
                "putts": -0.80
            }
        }
    }

    summary = pattern_summary_generator("1", pattern_data)

    assert "primarily driven by putts" in summary
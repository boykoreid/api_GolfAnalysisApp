from fastapi import APIRouter, Depends, status, HTTPException, Query
from ..models import Users, Rounds, Holes
from ..database import get_db
from .auth import get_current_user
from typing import Annotated
from sqlalchemy.orm import Session
from sqlalchemy import case, func, select, Result
from pydantic import BaseModel, Field
import datetime
from enum import Enum
import numpy as np

#model types: base, extended, full

router = APIRouter(
    prefix='/analytics',
    tags=['analytics']
)


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


# Used for displaying variables in the linear score model summary
LINEAR_SCORE_MODEL_DISPLAY_NAMES = {
        'putts': 'putt',
        "gir": "green in regulation",
        "fairways": "fairway hit",
        "penalty_strokes": "penalty stroke"
    }

PATTERN_ANALYSIS_DISPLAY_NAMES = {
    'putts': 'putts',
    "gir": "greens in regulation",
    "fairways": "fairways hit",
    "penalty_strokes": "penalty strokes"
}

VARIANCE_THRESHOLD = 0.85 # we keep eigenvectors which contribute to 85% of the variance
MIN_VECTOR_CONTRIBUTION = 0.1 # we keep vector components which shows a meaningful contribution to the pattern 

MIN_FAIRWAYS_TRACKED = 6 # the minimum number of holes required to be recorded for a round to be used as data in a model
MIN_PENALTIES_TRACKED = 8


class ModelType(str, Enum):
    base = 'base'
    extended = 'extended'
    full = 'full'


class PredictionRequest(BaseModel):
    putts: int = Field(
        ge=0, 
        description='The total number of putts in the round you want to predict the score of'
    )
    gir: int = Field(
        ge=0, 
        le=9,
        description='The total number of green in regulations in the round you want to predict the score of'
    )
    fairways: int | None = Field(
        default=None, 
        ge=0, 
        le=9,
        description='The total number of fairways hit in the round you want to predict the score of'
    )
    penalty_strokes: int | None = Field(
        default=None, 
        ge=0,
        description='The total number of penalty strokes in the round you want to predict the score of'
    )


def validate_season(db: db_dependency, user: user_dependency, season: int):
    season_exists = db.scalar(
        select(Rounds.id)
        .where(
            Rounds.user_id == user.get('id'),
            Rounds.season == season
        )
        .limit(1)
    )

    if season_exists is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Season not found"
        )


def query_model(db: db_dependency, user: user_dependency, season: int, model_type: ModelType):
    '''
    Queries the database based the model that is suggested (base, extended, full)
    '''

    if model_type == ModelType.base:
        query = (
            select(           
                func.sum(Holes.putts).label('putts'),
                func.sum(case((Holes.gir == True, 1), else_=0)).label('gir'),
                func.sum(Holes.score).label('score')
            )
            .select_from(Rounds)
            .join(Holes, Holes.round_id == Rounds.id)
            .where(Rounds.user_id == user.get('id'), Rounds.season == season)
            .group_by(Rounds.id)
        )


    elif model_type == ModelType.extended:
        query = (
            select(           
                func.sum(Holes.putts).label('putts'),
                func.sum(case((Holes.gir == True, 1), else_=0)).label('gir'),
                func.sum(case((Holes.fairway_hit == True, 1), else_=0)).label('fairways'),
                func.sum(Holes.score).label('score')
            )
            .select_from(Rounds)
            .join(Holes, Holes.round_id == Rounds.id)
            .where(Rounds.user_id == user.get('id'), Rounds.season == season)
            .group_by(Rounds.id)
            .having(func.count(Holes.fairway_hit) >= MIN_FAIRWAYS_TRACKED)
        )

    elif model_type == ModelType.full:
        query = (
            select(           
                func.sum(Holes.putts).label('putts'),
                func.sum(case((Holes.gir == True, 1), else_=0)).label('gir'),
                func.sum(case((Holes.fairway_hit == True, 1), else_=0)).label('fairways'),
                func.sum(Holes.penalty_strokes).label('penalty_strokes'),
                func.sum(Holes.score).label('score')
            )
            .select_from(Rounds)
            .join(Holes, Holes.round_id == Rounds.id)
            .where(Rounds.user_id == user.get('id'), Rounds.season == season)
            .group_by(Rounds.id)
            .having(func.count(Holes.fairway_hit) >= MIN_FAIRWAYS_TRACKED, func.count(Holes.penalty_strokes) >= MIN_PENALTIES_TRACKED)
        )

    rows = db.execute(query).all()

    if len(rows) < 20:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='To run the model, you must have at least 20 rounds with applicable data')

    #._mapping remembers the labels we assigned to each column. 
    # #taking .keys() returns us ONLY the column names, not the data associated with the columns (which would be row[0])
    feature_names = list(rows[0]._mapping.keys())[:-1] 

    return rows, feature_names


def linear_score_model(rows):
    '''
    Performs a linear regression on the data we queried
    '''

    data = np.array(rows, dtype=float)

    X = data[:, :-1] #means 'grab all rows and columns except for the last one
    scores = data[:, -1] #means 'grab all rows, and the last column'

    # Find features that contain variation
    variable_columns = np.ptp(X, axis=0) != 0

    # Remove features that have no variation
    # This would be most likely with a column like penalty strokes, where a great golfer may only ever have rounds with 0 penalty strokes
    X = X[:, variable_columns]

    # Make sure we still have at least one variable feature
    if X.shape[1] == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to generate model. Your data does not contain enough variation."
        )

    #X.shape gives us the dimensions of the data (ex, (3,3) means 3 rows and 3 columns).
    # We take the X.shape[0] to give us the dimension of only the rows.
    # we give it one column to make it column wise
    intercept = np.ones((X.shape[0], 1)) 


    #The matrix A
    A = np.column_stack((intercept, X))

    #the column vector we are trying to solve the linear regression on
    b = scores

    AT = A.T #A transpose

    ATA = AT @ A
    ATb = AT @ b

    try:
        coefficients = np.linalg.solve(ATA, ATb)
    except np.linalg.LinAlgError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to generate model. Your data does not contain enough variation."
        )

    return A, coefficients, b, variable_columns


def pattern_analysis(rows):
    '''
    Uses SVD to find patterns in a golfer's game
    '''
    data = np.array(rows, dtype=float)

    A = data[:, :-1] #leave out the score column

    means = A.mean(axis=0) #axis=0 means we get one mean per column. It gives us the mean by averaging across each of the rows
    stds = A.std(axis=0)
    stds[stds == 0] = 1 # when we get returned the list of standard deviations for each column, if one of them is 0, make it 1. this prevents a 0 division error

    # this scales our data to the mean of the column so SVD doesnt assume a column with higher values (ex.putts) is more important than others
    A_scaled = (A - means) / stds

    ATA = A_scaled.T @ A_scaled

    # I did not want to compute this manually. 
    # This would involve taking the det(ATA - lambda*I), and then taking the kernel of that matrix to find the eigenvectors
    # Then I would take the eigenvalues and feed them back into ATA - lambda*I to get my eigenvalues
    # I figured this was a needless process to try and show myself, because it would quickly create headaches for large matrices
    # Using this formula, the eigenvectors are already normalized as well (this is v / ||v||, where ||v|| = root(v*v))
    # We intentionally leave out finding matrix U because it has no relevance.
    eigenvalues, eigenvectors = np.linalg.eigh(ATA)
    # We use eigh() because ATA is always symmetric and it guarantees real eigenvalues

    idx = np.argsort(eigenvalues)[::-1]  # Gives us the indices that would sort the array. Then uses slicing to put them in reverse order so we can get a descending order

    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx] #Take every row, but rearrange the columns according to idx.

    eigenvalues[eigenvalues < 0] = 0 #this is just protection against bugs. Sometimes you may get a floating decimal like '-0.000001' which is essentially a 0 eigenvalue. this just protects against that
    singular_values = np.sqrt(eigenvalues)

    sum_sigma = np.sum(singular_values**2)

    explained_variance = []
    for sv in singular_values:
        explained_variance.append(sv**2 / sum_sigma if sum_sigma != 0 else 0)

    # get cumulative variance. 
    # lets say pattern 1 explains 50%, pattern 2 explains 25%, pattern 3 explains 15% and pattern 4 explains 10%. then cumsum returns [0.5, 0.75, 0.9, 1]
    cumulative_variance = np.cumsum(explained_variance) 

    return eigenvectors, singular_values, explained_variance, cumulative_variance


def pattern_summary_generator(pattern_number: str, pattern_data: dict):
    '''
    Takes a filtered dictionary of all relevant pattern information for each pattern a golfer has, and translates it into a paragraph'
    '''
    variance_percent = round(pattern_data['explained_variance'] * 100)

    positive_features = [
        PATTERN_ANALYSIS_DISPLAY_NAMES.get(feature, feature)
        for feature in pattern_data['features']['positive']
    ]

    negative_features = [
        PATTERN_ANALYSIS_DISPLAY_NAMES.get(feature, feature)
        for feature in pattern_data['features']['negative']
    ]

    all_features = {
        **pattern_data['features']['positive'],
        **pattern_data['features']['negative']
    }

    if all_features:
        strongest_feature = max(
            all_features,
            key=lambda feature: abs(all_features[feature])
        )

        strongest_feature = PATTERN_ANALYSIS_DISPLAY_NAMES.get(
            strongest_feature,
            strongest_feature
        )

    if positive_features and negative_features:
        return (
            f"Pattern {pattern_number} explains {variance_percent}% "
            f"of the variation across the selected performance metrics. "
            f"This pattern represents a relationship where "
            f"{', '.join(positive_features)} tend to increase while "
            f"{', '.join(negative_features)} tend to decrease, and vice versa. "
            f"This pattern is primarily driven by {strongest_feature}"
        )

    elif positive_features:
        return (
            f"Pattern {pattern_number} explains {variance_percent}% "
            f"of the variation across the selected performance metrics. "
            f"This pattern is characterized by "
            f"{', '.join(positive_features)} tending to increase together. "
            f"This pattern is primarily driven by {strongest_feature}"
        )

    elif negative_features:
        return (
            f"Pattern {pattern_number} explains {variance_percent}% "
            f"of the variation across the selected performance metrics. "
            f"This pattern is characterized by "
            f"{', '.join(negative_features)} tending to decrease together. "
            f"This pattern is primarily driven by {strongest_feature}"
        )

    else:
        return (
            f"Pattern {pattern_number} explains {variance_percent}% "
            f"of the variation across the selected performance metrics, "
            f"but no major contributing features were identified. " 
        )

    


@router.get('/linear_score_model/summary', status_code=status.HTTP_200_OK)
async def linear_score_model_summary(db: db_dependency, 
                                     user: user_dependency, 
                                     season: int = Query(), 
                                     model_type: ModelType = Query(description='The model type used for predictions')):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    validate_season(db, user, season)
    
    rows, feature_names = query_model(db, user, season, model_type)
    A, coeff, b, variable_columns = linear_score_model(rows)

    #only keep the feature names of the features with variability
    active_feature_names = [
        name
        for name, keep in zip(feature_names, variable_columns)
        if keep
    ]

    weights = {}
    for name, value in zip(active_feature_names, coeff[1:]):
        weights[name] = round(float(value), 2)

    summary = []

    for feature, weight in weights.items():
        label = LINEAR_SCORE_MODEL_DISPLAY_NAMES.get(feature, feature) #if the feature is not in the display names, just return the feature as is. This prevents crashing

        summary.append(f"Each additional {label}")
        if weight > 0:
            summary.append(
                f"is associated with approximately {abs(weight)} additional strokes."
            )

        elif weight < 0:
            summary.append(
                f"is associated with approximately {abs(weight)} fewer strokes."
            )

        else:
            summary.append(
                f"did not have a measurable relationship with score."
            )

    return {
        'summary': " ".join(summary),
        'model': model_type,
        'season': season,
        'coefficients': weights
    }


@router.get('/linear_score_model/diagnostics', status_code=status.HTTP_200_OK)
async def linear_score_model_diagnostics(db: db_dependency, 
                                         user: user_dependency, 
                                         season: int = Query(), 
                                         model_type: ModelType = Query(description='The model type used for predictions')):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    validate_season(db, user, season)
    
    rows, feature_names = query_model(db, user, season, model_type)
    A, coeff, b, variable_columns = linear_score_model(rows)

    #only keep the feature names of the features with variability
    active_feature_names = [
        name
        for name, keep in zip(feature_names, variable_columns)
        if keep
    ]


    predictions = A @ coeff
    residuals = b - predictions

    mse = np.mean(residuals ** 2) #measures how close our model's guesses are to the real b vector

    rmse = np.sqrt(mse) #root mean squared error: tells us how many strokes the model typically misses by

    intercept = round(float(coeff[0]), 2)

    weights = {}
    for name, value in zip(active_feature_names, coeff[1:]):
        weights[name] = round(float(value), 2)

    regression_equation = f"Score = {intercept}"

    for k, v in weights.items():
        if v >= 0:
            regression_equation += f" + {v}({k})"
        else:
            regression_equation += f" - {abs(v)}({k})"

    return {
        'regression_equation': regression_equation,
        'intercept': intercept,
        'coefficients': weights,
        'rounds_used': len(A),
        'mse': round(float(mse), 2),
        'rmse': round(float(rmse), 2),
        'actual_scores': b.tolist(),
        'predicted_scores': np.round(predictions, 2).tolist()
    }


@router.get('/pattern_model/summary', status_code=status.HTTP_200_OK)
async def svd_model_summary(
    db: db_dependency, 
    user: user_dependency, 
    season: int = Query(), 
    model_type: ModelType = Query()):

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    validate_season(db, user, season)

    if model_type == ModelType.base:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Pattern analysis is not supported for the base model')

    rows, feature_names = query_model(db, user, season, model_type)
    eigenvectors, singular_values, explained_variance, cumulative_variance = pattern_analysis(rows)

    num_patterns = np.argmax(cumulative_variance >= VARIANCE_THRESHOLD) + 1 #find the number of patterns that contribute to the minimum variance threshold

    eigenvectors = eigenvectors[:, :num_patterns]
    singular_values = singular_values[:num_patterns]
    explained_variance = explained_variance[:num_patterns]

    # Squared loadings represent how much each feature contributes to a pattern
    contributions = eigenvectors**2 

    # if a vector component is less than 10% of the pattern, discard it bc it has no relevance.
    # This is done by setting it to 0 for later filtering
    filtered_vectors = np.where(contributions >= MIN_VECTOR_CONTRIBUTION, eigenvectors, 0)  

    summary = {}

    for i, vector in enumerate(filtered_vectors.T):

        positive = {}
        negative = {}

        for feature, component in zip(feature_names, vector):
            if component > 0:
                positive[feature] = round(float(component), 3)
            elif component < 0:
                negative[feature] = round(float(component), 3)

        summary[f'pattern {i + 1}'] = {
            'strength': round(float(singular_values[i]), 3),
            'explained_variance': round(float(explained_variance[i]), 3),
            'features': {
                'positive': positive,
                'negative': negative
            }
        }

    pattern_summaries = {}

    for pattern, data in summary.items():
        pattern_number = pattern.split()[-1]

        pattern_summaries[pattern] = pattern_summary_generator(
            pattern_number,
            data
        )

    return pattern_summaries


@router.get('/pattern_model/diagnostics', status_code=status.HTTP_200_OK)
async def svd_model_diagnostics(
    db: db_dependency, 
    user: user_dependency, 
    season: int = Query(), 
    model_type: ModelType = Query()):

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    validate_season(db, user, season)

    if model_type == ModelType.base:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Pattern analysis is not supported for the base model')

    rows, feature_names = query_model(db, user, season, model_type)
    eigenvectors, singular_values, explained_variance, cumulative_variance = pattern_analysis(rows)

    patterns = {}
    
    for i, (sigma, expl_var, cum_var, vector) in enumerate(zip(singular_values, explained_variance, cumulative_variance, eigenvectors.T), start=1):

        weights = {}

        for feature, weight in zip(feature_names, vector):
            weights[feature] = round(float(weight), 3)

        patterns[f"pattern_{i}"] = {
            "strength": round(float(sigma), 3),
            "explained_variance": round(float(expl_var), 3),
            "cumulative_variance": round(float(cum_var), 3),
            "weights": weights
        }

    return patterns


@router.post('/predict', status_code=status.HTTP_200_OK)
async def predict_score(db: db_dependency, 
                        user: user_dependency,
                        request: PredictionRequest, 
                        season: int = Query(), 
                        model_type: ModelType = Query()):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    validate_season(db, user, season)

    if model_type == ModelType.extended and request.fairways is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Please enter a valid number for fairways')

    if model_type == ModelType.full and (request.fairways is None or request.penalty_strokes is None):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Please enter a valid number for either fairways or penalty strokes')
    
    rows, feature_names = query_model(db, user, season, model_type)
    A, coefficients, b, variable_columns = linear_score_model(rows)

    #only keep the feature names of the features with variability
    active_feature_names = [
        name
        for name, keep in zip(feature_names, variable_columns)
        if keep
    ]


    intercept = coefficients[0]
    feature_coefficients = coefficients[1:]

    components = [intercept]

    for coeff, feature in zip(feature_coefficients, active_feature_names):
        component = coeff * getattr(request, feature)
        components.append(component)

    predicted_score = sum(components)

    return {
        'predicted score': round(float(predicted_score), 1)
    }




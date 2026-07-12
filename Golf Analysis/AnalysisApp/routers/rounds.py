from fastapi import APIRouter, Depends, status, HTTPException, Path
from ..models import Users, Rounds, Holes
from ..database import SessionLocal, get_db
from .auth import get_current_user
from typing import Annotated
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import datetime
from typing import Optional

 

router = APIRouter(
    prefix='/rounds',
    tags=['rounds']
)


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


class PostHoleRequest(BaseModel):
    par: int = Field(ge=3, le=5)
    score: int = Field(ge=1)
    putts: int = Field(ge=0)


class PostRoundRequest(BaseModel):
    date: datetime.date
    course_name: str
    is_front_nine: bool
    holes: list[PostHoleRequest] = Field(min_length=9, max_length=9)

    model_config = {
        "json_schema_extra": {
            "example": {
                "date": "2026-06-25",
                "course_name": "Edmonton Country Club",
                "is_front_nine": True,
                "holes": [
                    {"par": 4, "score": 4, "putts": 2},
                    {"par": 4, "score": 4, "putts": 2},
                    {"par": 4, "score": 4, "putts": 2},
                    {"par": 3, "score": 3, "putts": 2},
                    {"par": 4, "score": 4, "putts": 2},
                    {"par": 5, "score": 5, "putts": 2},
                    {"par": 4, "score": 4, "putts": 2},
                    {"par": 4, "score": 4, "putts": 2},
                    {"par": 4, "score": 4, "putts": 2}
                ]
            }
        }
    }


class UpdateHoleRequest(BaseModel):
    par: Optional[int] = Field(default=None, ge=3, le=5)
    score: Optional[int] = Field(default=None,ge=1)
    putts: Optional[int] = Field(default=None, ge=0)


class UpdateRoundInfoRequest(BaseModel):
    date: Optional[datetime.date] = None
    course_name: Optional[str] = None
    is_front_nine: Optional[bool] = None


    


@router.get('/', status_code=status.HTTP_200_OK)
async def get_rounds(db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    return db.query(Rounds).filter(Rounds.user_id == user.get('id')).all()


@router.get('/round_info/{round_id}', status_code=status.HTTP_200_OK)
async def get_info_from_round(db: db_dependency, user: user_dependency, round_id: int):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    user_round = db.query(Rounds).filter(
        Rounds.user_id == user.get('id'),
        Rounds.id == round_id
        ).first()
    
    if user_round is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Round not found')
    
    return user_round


@router.get('/round_stats/{round_id}')
async def get_stats_from_round(db: db_dependency, user: user_dependency, round_id: int):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    user_round = db.query(Rounds).filter(
        Rounds.user_id == user.get('id'),
        Rounds.id == round_id
        ).first()

    if user_round is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Round not found')
    
    return db.query(Holes).filter(Holes.round_id == round_id).all()


@router.post('/create', status_code=status.HTTP_201_CREATED)
async def create_round(db: db_dependency, user: user_dependency, request: PostRoundRequest):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    try:
        round = Rounds(
            user_id=user.get('id'),
            date=request.date,
            course_name=request.course_name,
            is_front_nine=request.is_front_nine
        )

        db.add(round)
        db.flush()


        if request.is_front_nine == True:
            start_hole = 1
        else:
            start_hole = 10

        for hole_num, hole_request in enumerate(request.holes, start=start_hole):

            hole = Holes(
                round_id=round.id,
                hole_number=hole_num,
                par=hole_request.par,
                score=hole_request.score,
                putts=hole_request.putts,
                gir=(hole_request.score - hole_request.putts) <= (hole_request.par - 2)
            )

            db.add(hole)

        
        db.commit()
    
    except:
        db.rollback() #get rid of all the changes we just made to the database
        raise # raise the exception we encountered


@router.patch('/round_info/{round_id}')
async def edit_round_info(
    db: db_dependency, 
    user: user_dependency, 
    request: UpdateRoundInfoRequest, 
    round_id: int):

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    round_model = db.query(Rounds).filter(Rounds.id == round_id, Rounds.user_id == user.get('id')).first()

    if round_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Round not found')
    
    update_data = request.model_dump(exclude_unset=True) #exclude_unset means that our update_data only includes the data our user actually sent

    for key, value in update_data.items():
        setattr(round_model, key, value) #Update the round model to include our new information by seeing which of the keys match
    
    db.commit()
    db.refresh(round_model)
    return round_model #return the updated round model so the person can see if they messed up their update


@router.patch('/round_stats/{round_id}/hole/{hole_number}')
async def edit_hole(
    db: db_dependency, 
    user: user_dependency, 
    request: UpdateHoleRequest,
    round_id: int, 
    hole_number: int = Path(ge=1, le=18)):

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    round_model = db.query(Rounds).filter(Rounds.id == round_id, Rounds.user_id == user.get('id')).first()
    if round_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Round not found')
    
    update_data = request.model_dump(exclude_unset=True)
    hole = db.query(Holes).filter(Holes.round_id == round_id, Holes.hole_number == hole_number).first()
    if hole is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Hole not found')

    for key, value in update_data.items():
        setattr(hole, key, value)

    hole.gir = (hole.score - hole.putts) <= (hole.par - 2)

    db.commit()
    db.refresh(hole)
    return hole



@router.delete('/{round_id}')
async def delete_round(db: db_dependency, user: user_dependency, round_id: int):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    round_model = db.query(Rounds).filter(Rounds.id == round_id, Rounds.user_id == user.get('id')).first()

    if round_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Round not found")
    
    db.query(Holes).filter(Holes.round_id == round_id).delete()
    
    db.delete(round_model)
    db.commit()



    
from fastapi import APIRouter, Depends, status, HTTPException, Path
from ..models import Users, Rounds, Holes
from ..database import SessionLocal, get_db
from .auth import get_current_user
from .rounds import PostHoleRequest, PostRoundRequest, UpdateHoleRequest, UpdateRoundInfoRequest
from typing import Annotated
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import datetime
from typing import Optional
from passlib.context import CryptContext


 

router = APIRouter(
    prefix='/admin',
    tags=['admin']
)


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


def get_admin(user: user_dependency):
    if user is None or user.get('admin') == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authorized')

    return user


admin_dependency = Annotated[dict, Depends(get_admin)]
    

class AdminCreateUserRequest(BaseModel):
    email: str = Field(min_length=7, max_length=30)
    username: str
    first_name: str
    last_name: str
    password: str = Field(min_length=7, max_length=20)
    admin: bool


class AdminChangePasswordRequest(BaseModel):
    new_password: str = Field(min_length=7, max_length=20)
    confirm_password: str = Field(min_length=7, max_length=20)


class UserResponseModel(BaseModel):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    admin: bool


### DASHBOARD
@router.get('/dashboard', status_code=status.HTTP_200_OK)
async def get_dashboard(db: db_dependency, admin: admin_dependency):
    user_count = db.query(Users).count()
    rounds_count = db.query(Rounds).count()
    holes_count = db.query(Holes).count()
    admins_count = db.query(Users).filter(Users.admin == True).count()

    return {
        'users': user_count,
        'rounds': rounds_count,
        'holes': holes_count,
        'admins': admins_count
    }


### ROUND FUNCTIONALITIES
@router.get('/rounds', status_code=status.HTTP_200_OK)
async def get_all_rounds(db: db_dependency, admin: admin_dependency):
    return db.query(Rounds).all()


@router.get('/rounds/round_info/{round_id}', status_code=status.HTTP_200_OK)
async def get_info_from_round(db: db_dependency, admin: admin_dependency, round_id: int):
    user_round = db.query(Rounds).filter(Rounds.id == round_id).first()
    
    if user_round is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Round not found')
    
    return user_round


@router.get('/rounds/round_stats/{round_id}', status_code=status.HTTP_200_OK)
async def get_stats_from_round(db: db_dependency, admin: admin_dependency, round_id: int):
    
    user_round = db.query(Rounds).filter(Rounds.id == round_id).first()

    if user_round is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Round not found')
    
    return db.query(Holes).filter(Holes.round_id == round_id).all()


@router.post('/rounds/create/{user_id}', status_code=status.HTTP_201_CREATED)
async def create_round(db: db_dependency, admin: admin_dependency, request: PostRoundRequest, user_id: int):
    
    try:
        user_model = db.query(Users).filter(Users.id == user_id).first()

        if user_model is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

        round = Rounds(
            user_id=user_id,
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


@router.patch('/rounds/round_info/{round_id}', status_code=status.HTTP_200_OK)
async def edit_round_info(
    db: db_dependency, 
    admin: admin_dependency, 
    request: UpdateRoundInfoRequest, 
    round_id: int):
    
    round_model = db.query(Rounds).filter(Rounds.id == round_id).first()

    if round_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Round not found')
    
    update_data = request.model_dump(exclude_unset=True) #exclude_unset means that our update_data only includes the data our user actually sent

    for key, value in update_data.items():
        setattr(round_model, key, value) #Update the round model to include our new information by seeing which of the keys match
    
    db.commit()
    db.refresh(round_model)
    return round_model #return the updated round model so the person can see if they messed up their update


@router.patch('/rounds/round_stats/{round_id}/hole/{hole_number}', status_code=status.HTTP_200_OK)
async def edit_hole(
    db: db_dependency, 
    admin: admin_dependency, 
    request: UpdateHoleRequest,
    round_id: int, 
    hole_number: int = Path(ge=1, le=18)):
    
    round_model = db.query(Rounds).filter(Rounds.id == round_id).first()
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



@router.delete('/rounds/{round_id}', status_code = status.HTTP_204_NO_CONTENT)
async def delete_round(db: db_dependency, admin: admin_dependency, round_id: int):

    round_model = db.query(Rounds).filter(Rounds.id == round_id).first()

    if round_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Round not found")
    
    db.query(Holes).filter(Holes.round_id == round_id).delete()
    
    db.delete(round_model)
    db.commit()


### USER FUNCTIONALITIES
@router.get('/users', status_code=status.HTTP_200_OK)
async def get_all_users(db: db_dependency, admin: admin_dependency):
    user_response_list = []

    user_model_list = db.query(Users).all()

    for user in user_model_list:
        response = UserResponseModel(
            id = user.id,
            username = user.username,
            email = user.email,
            first_name = user.first_name,
            last_name = user.last_name,
            admin = user.admin,
        )

        user_response_list.append(response)

    return user_response_list
        




@router.get('/users/{user_id}', status_code=status.HTTP_200_OK, response_model=UserResponseModel)
async def get_user(db: db_dependency, admin: admin_dependency, user_id: int):

    user_model = db.query(Users).filter(Users.id == user_id).first()

    if user_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    
    return {
        'id': user_model.id,
        'username': user_model.username,
        'email': user_model.email,
        'first_name': user_model.first_name,
        'last_name': user_model.last_name,
        'admin': user_model.admin
    }

'''
@router.get('users/{user_id}/summary')
async def get_user_summary(db: db_dependency, admin: admin_dependency, user_id: int):
    rounds_count = db.query(Rounds).filter(Rounds.user_id == user_id).count()
    avg_score = db.query()
'''


@router.post('/users/create', status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, admin: admin_dependency, request: AdminCreateUserRequest):
    
    model = Users(
        email=request.email,
        username=request.username,
        first_name=request.first_name,
        last_name=request.last_name,
        hashed_password=bcrypt_context.hash(request.password),
        admin=request.admin
    )

    db.add(model)
    db.commit()


@router.put('/users/{user_id}/password', status_code=status.HTTP_200_OK)
async def change_user_password(
    db: db_dependency, 
    admin: admin_dependency, 
    request: AdminChangePasswordRequest, 
    user_id: int
    ):

    user_model = db.query(Users).filter(Users.id == user_id).first()

    if user_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Passwords do not match')

    user_model.hashed_password = bcrypt_context.hash(request.new_password)

    db.add(user_model)
    db.commit()



@router.patch('/users/{user_id}/add_permissions', status_code=status.HTTP_200_OK, response_model=UserResponseModel)
async def add_admin_permissions(db: db_dependency, admin: admin_dependency, user_id: int):
    user_model = db.query(Users).filter(Users.id == user_id).first()
    if user_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    user_model.admin = True
    db.add(user_model)
    db.commit()
    return user_model


@router.patch('/users/{user_id}/remove_permissions', status_code=status.HTTP_200_OK, response_model=UserResponseModel)
async def remove_admin_permissions(db: db_dependency, admin: admin_dependency, user_id: int):
    user_model = db.query(Users).filter(Users.id == user_id).first()
    if user_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    if user_model.id == admin.get('id'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Don't remove your own permissions, dummy")

    user_model.admin = False
    db.add(user_model)
    db.commit()
    return user_model


@router.delete('/users/delete/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(db: db_dependency, admin: admin_dependency, user_id: int):
    
    user_model = db.query(Users).filter(Users.id == user_id).first()

    if user_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    
    if user_model.id == admin.get('id'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Do not delete yourself, dummy')
    
    if user_model.admin == True:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='You cannot delete another admin')
    
    rounds = db.query(Rounds).filter(Rounds.user_id == user_id).all()

    for round in rounds:
        holes = db.query(Holes).filter(Holes.round_id == round.id).delete()
    
    db.query(Rounds).filter(Rounds.user_id == user_id).delete()

    
    db.delete(user_model)
    db.commit()



    

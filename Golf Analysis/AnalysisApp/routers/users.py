from fastapi import APIRouter, Depends, status, HTTPException
from ..database import SessionLocal, get_db
from ..models import Users
from .auth import get_current_user
from typing import Annotated
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from passlib.context import CryptContext

 

router = APIRouter(
    prefix='/users',
    tags=['users']
)

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[Session, Depends(get_current_user)]


class NewPasswordRequest(BaseModel):
    original_password: str = Field(min_length=7, max_length=20)
    new_password: str = Field(min_length=7, max_length=20)
    confirm_password: str = Field(min_length=7, max_length=20)


@router.get('/', status_code=status.HTTP_200_OK)
async def get_self(db: db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    user_model = db.query(Users).filter(Users.id == user.get('id')).first()

    return {
    'username': user_model.username,
    'email': user_model.email,
    'first_name': user_model.first_name,
    'last_name': user_model.last_name
    }


@router.put('/password', status_code=status.HTTP_204_NO_CONTENT)
async def change_password(db: db_dependency, user: user_dependency, request: NewPasswordRequest):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    user_model = db.query(Users).filter(Users.id == user.get('id')).first()

    if not bcrypt_context.verify(request.original_password, user_model.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Original passwords do not match")

    if request.new_password != request.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='New passwords do not match')


    user_model.hashed_password = bcrypt_context.hash(request.new_password)

    db.add(user_model)
    db.commit()



from fastapi import APIRouter, Depends, status, HTTPException
from ..models import Users
from ..database import SessionLocal, get_db
from typing import Annotated
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
import secrets
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone



router = APIRouter(
    prefix='/auth',
    tags=['auth']
)

SECRET_KEY = 'aisbfaiUsfuiaShfAAOIASOIFHAiofdusdg90ew9rwe90349'
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/login')

db_dependency = Annotated[Session, Depends(get_db)]


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, key=SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        id: int = payload.get('id')
        admin: bool = payload.get('admin')

        if username is None or id is None or admin is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user")


    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user")
    
    return {'username': username, 'id': id, 'admin': admin}
    
    
 

def authenticate_user(db: db_dependency, username: str, password: str):

    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return False
    
    verify = bcrypt_context.verify(password, user.hashed_password)
    if not verify:
        return False
    
    return user


def create_token(id: int, username: str, admin: bool):
    expiry = datetime.now(timezone.utc) + timedelta(minutes=30)

    payload = {
        'sub': username,
        'id': id,
        'admin': admin,
        'exp': expiry
               }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

 
class CreateUserRequest(BaseModel):
    email: str = Field(min_length=7, max_length=30)
    username: str
    first_name: str
    last_name: str
    password: str = Field(min_length=7, max_length=20)


@router.post('/', status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, request: CreateUserRequest):
    model = Users(
        email=request.email,
        username=request.username,
        first_name=request.first_name,
        last_name=request.last_name,
        hashed_password=bcrypt_context.hash(request.password),
        admin=False
    )

    db.add(model)
    db.commit()


@router.post('/login')
async def create_access_token_for_login(db: db_dependency, form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    username = form.username
    password = form.password

    user = authenticate_user(db, username, password)

    if user == False:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')
    
    token = create_token(user.id, user.username, user.admin)

    return {'access_token': token, 'token_type': 'bearer'}












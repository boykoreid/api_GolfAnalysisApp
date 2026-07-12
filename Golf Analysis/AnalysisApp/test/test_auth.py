from .utils import *
from ..routers.auth import authenticate_user, create_token, SECRET_KEY, ALGORITHM
from datetime import timedelta
from jose import jwt
import asyncio
from fastapi import HTTPException

def test_auth_create_user():
    request_data = {
        'email': 'newusertest@email.com',
        'username': 'newusertest',
        'first_name': 'New',
        'last_name': 'User',
        'password': 'testpassword',
    }

    response = client.post('/auth/', json=request_data)
    assert response.status_code == status.HTTP_201_CREATED

    db = TestingSessionLocal()
    user = db.query(Users).filter(Users.email == 'newusertest@email.com').first()

    assert user.email == request_data['email']
    assert user.username == request_data['username']
    assert user.first_name == request_data['first_name']
    assert user.last_name == request_data['last_name']
    assert user.admin == False

    assert bcrypt_context.verify(request_data['password'], user.hashed_password)

    db.delete(user)
    db.commit()
    db.close()




def test_authenticate_user(test_user):
    db = TestingSessionLocal()

    authenticated_user = authenticate_user(db, test_user.username, 'testpassword')
    assert authenticated_user is not None
    assert authenticated_user.username == test_user.username

    non_existent_user = authenticate_user(db, 'wrongusername', 'testpassword')
    assert non_existent_user is False

    wrong_password_user = authenticate_user(db, test_user.username, 'wrongpassword')
    assert wrong_password_user is False


def test_create_access_token():
    username = 'testuser'
    user_id = 1
    admin = True
    expires_delta = timedelta(days=1)

    token = create_token(user_id, username, admin)

    decoded_token = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={'verify_signature': False})

    assert decoded_token['sub'] == username
    assert decoded_token['id'] == user_id
    assert decoded_token['admin'] == admin


@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    encode = {'sub': 'testuser', 'id': 1, 'admin': False}
    token = jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

    user = await get_current_user(token=token)
    assert user == {'username': 'testuser', 'id': 1, 'admin': False}


@pytest.mark.asyncio
async def test_get_current_user_missing_payload():
    encode = {'admin': 'False'}
    token = jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(token=token)
    
    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == 'Could not validate user'


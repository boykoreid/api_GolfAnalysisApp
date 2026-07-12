from .utils import *
from ..routers.auth import bcrypt_context


def test_get_self(test_user):
    response = client.get('/users/')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        'username': test_user.username,
        'email': test_user.email,
        'first_name': test_user.first_name,
        'last_name': test_user.last_name
    }


def test_get_self_not_authenticated(no_user_override):
    response = client.get('/users/')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_change_password(test_user):
    request_data = {
        'original_password': 'testpassword',
        'new_password': 'newtestpassword',
        'confirm_password': 'newtestpassword'
    }

    response = client.put('/users/password', json=request_data)
    assert response.status_code == status.HTTP_204_NO_CONTENT

    db = TestingSessionLocal()
    user = db.query(Users).filter(Users.id == test_user.id).first()
    assert bcrypt_context.verify('newtestpassword', user.hashed_password)


def test_change_password_not_authenticated(no_user_override):
    request_data = {
        'original_password': 'testpassword',
        'new_password': 'newtestpassword',
        'confirm_password': 'newtestpassword'
    }

    response = client.put('/users/password', json=request_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_change_password_failed_password_verifcation(test_user):
    request_data = {
        'original_password': 'WRONG PASSWORD',
        'new_password': 'newtestpassword',
        'confirm_password': 'newtestpassword'
    }

    response = client.put('/users/password', json=request_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {'detail': 'Original passwords do not match'}


def test_change_password_mismatched_new_passwords(test_user):
    request_data = {
        'original_password': 'testpassword',
        'new_password': 'newtestpassword',
        'confirm_password': 'MISMATCH'
    }

    response = client.put('/users/password', json=request_data)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'detail': 'New passwords do not match'}



from .utils import *

def test_admin_authentication(test_non_admin):
    app.dependency_overrides[get_current_user] = lambda: {
        'username': test_non_admin.username,
        'id': test_non_admin.id,
        'admin': False
    }

    response = client.get('/admin/dashboard')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {'detail': 'Not authorized'}

    app.dependency_overrides[get_current_user] = override_get_current_user


def test_admin_dashboard(test_user, test_round, test_hole):
    response = client.get('/admin/dashboard')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'users': 1,'rounds': 1,'holes': 1,'admins': 1}


### ROUND TESTS

def test_admin_get_all_rounds(test_round):
    response = client.get('/admin/rounds')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{'id': 1, 'user_id': 1, 'date': str(datetime.date.today()), 'course_name': 'Edmonton Country Club', 'is_front_nine':True}]


def test_admin_info_from_round(test_round):
    response = client.get('/admin/rounds/round_info/1')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'id': 1, 'user_id': 1, 'date': str(datetime.date.today()), 'course_name': 'Edmonton Country Club', 'is_front_nine':True}


def test_admin_info_from_round_not_found(test_round):
    response = client.get('/admin/rounds/round_info/999')
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Round not found'}


def test_admin_stats_from_round(test_round, test_hole):
    response = client.get('/rounds/round_stats/1')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{'id': 1, 'round_id': 1, 'hole_number': 1, 'par': 4, 'score': 4, 'putts': 2, 'gir': True}]


def test_admin_stats_from_round(test_round, test_hole):
    response = client.get('/rounds/round_stats/999')
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Round not found'}


def test_admin_create_front_nine_round(test_round, test_hole):
    request_data = {
        'date': str(datetime.date.today()), 
        'course_name': 'Edmonton Country Club', 
        'is_front_nine': True,
        'holes':[
            {
                'hole_number': 1,
                'par': 4,
                'score': 4,
                'putts': 2,
            },
            {
                'hole_number': 2,
                'par': 4,
                'score': 4,
                'putts': 2,
            },
            {
                'hole_number': 3,
                'par': 4,
                'score': 4,
                'putts': 2,
            },
            {
                'hole_number': 4,
                'par': 4,
                'score': 4,
                'putts': 2,
            },
            {
                'hole_number': 5,
                'par': 4,
                'score': 5,
                'putts': 2,
            },
            {
                'hole_number': 6,
                'par': 4,
                'score': 4,
                'putts': 2,
            },
            {
                'hole_number': 7,
                'par': 4,
                'score': 4,
                'putts': 2,
            },
            {
                'hole_number': 8,
                'par': 4,
                'score': 4,
                'putts': 2,
            },
            {
                'hole_number': 9,
                'par': 4,
                'score': 4,
                'putts': 2,
            },
        ]
    }

    response = client.post('/admin/rounds/create/1', json=request_data)
    assert response.status_code == status.HTTP_201_CREATED

    db = TestingSessionLocal()

    round_model = db.query(Rounds).filter(Rounds.id == 2).first()
    assert round_model.date == request_data['date']
    assert round_model.course_name == request_data['course_name']
    assert round_model.is_front_nine == request_data['is_front_nine']

    holes_list = db.query(Holes).filter(Holes.round_id == 2).all()
    assert len(holes_list) == len(request_data['holes'])

    holes_list.sort(key=lambda x: x.hole_number)

    for db_hole, request_hole in zip(holes_list, request_data['holes']):
        assert db_hole.hole_number == request_hole['hole_number']
        assert db_hole.par == request_hole['par']
        assert db_hole.score == request_hole['score']
        assert db_hole.putts == request_hole['putts']
        assert db_hole.gir == (request_hole['score'] - request_hole['putts'] <= request_hole['par'] - 2)
    
    for hole in holes_list:
        db.delete(hole)

    db.delete(round_model)

    db.commit()


    



def test_admin_create_back_nine_round(test_round, test_hole):
    request_data = {
        'date': str(datetime.date.today()), 
        'course_name': 'Edmonton Country Club', 
        'is_front_nine': False,
        'holes':[
            {
                'hole_number': 10,
                'par': 4,
                'score': 4,
                'putts': 2,
            },
            {
                'hole_number': 11,
                'par': 4,
                'score': 4,
                'putts': 2,
            },
            {
                'hole_number': 12,
                'par': 4,
                'score': 4,
                'putts': 2,
            },
            {
                'hole_number': 13,
                'par': 4,
                'score': 4,
                'putts': 2,
            },
            {
                'hole_number': 14,
                'par': 4,
                'score': 5,
                'putts': 2,
            },
            {
                'hole_number': 15,
                'par': 4,
                'score': 4,
                'putts': 2,
            },
            {
                'hole_number': 16,
                'par': 4,
                'score': 4,
                'putts': 2,
            },
            {
                'hole_number': 17,
                'par': 4,
                'score': 4,
                'putts': 2,
            },
            {
                'hole_number': 18,
                'par': 4,
                'score': 4,
                'putts': 2,
            },
        ]
    }

    response = client.post('/admin/rounds/create/1', json=request_data)
    assert response.status_code == status.HTTP_201_CREATED

    db = TestingSessionLocal()

    round_model = db.query(Rounds).filter(Rounds.id == 2).first()
    assert round_model.date == request_data['date']
    assert round_model.course_name == request_data['course_name']
    assert round_model.is_front_nine == request_data['is_front_nine']

    holes_list = db.query(Holes).filter(Holes.round_id == 2).all()
    assert len(holes_list) == len(request_data['holes'])

    holes_list.sort(key=lambda x: x.hole_number)

    for db_hole, request_hole in zip(holes_list, request_data['holes']):
        assert db_hole.hole_number == request_hole['hole_number']
        assert db_hole.par == request_hole['par']
        assert db_hole.score == request_hole['score']
        assert db_hole.putts == request_hole['putts']
        assert db_hole.gir == (request_hole['score'] - request_hole['putts'] <= request_hole['par'] - 2)
    
    for hole in holes_list:
        db.delete(hole)

    db.delete(round_model)
    
    db.commit()
    

def test_admin_create_round_user_not_found(test_round, test_hole):
    request_data = {
        'date': str(datetime.date.today()), 
        'course_name': 'Edmonton Country Club', 
        'is_front_nine': False,
        'holes':[
            {
                'hole_number': 10,
                'par': 4,
                'score': 4,
                'putts': 2,
            },
            {
                'hole_number': 11,
                'par': 4,
                'score': 4,
                'putts': 2,
            },
            {
                'hole_number': 12,
                'par': 4,
                'score': 4,
                'putts': 2,
            },
            {
                'hole_number': 13,
                'par': 4,
                'score': 4,
                'putts': 2,
            },
            {
                'hole_number': 14,
                'par': 4,
                'score': 5,
                'putts': 2,
            },
            {
                'hole_number': 15,
                'par': 4,
                'score': 4,
                'putts': 2,
            },
            {
                'hole_number': 16,
                'par': 4,
                'score': 4,
                'putts': 2,
            },
            {
                'hole_number': 17,
                'par': 4,
                'score': 4,
                'putts': 2,
            },
            {
                'hole_number': 18,
                'par': 4,
                'score': 4,
                'putts': 2,
            },
        ]
    }
    response = client.post('/admin/rounds/create/999', json=request_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'User not found'}


def test_admin_edit_round_info(test_round):
    request_data = {
        'date': str(datetime.date.today()),
        'course_name': 'Edmonton Springs'
    }

    response = client.patch('/admin/rounds/round_info/1', json=request_data)
    assert response.status_code == status.HTTP_200_OK

    db = TestingSessionLocal()
    model = db.query(Rounds).filter(Rounds.id == 1).first()
    assert model.date == request_data['date']
    assert model.course_name == request_data['course_name']
    assert model.is_front_nine == True

    assert response.json() == {
        'id': 1,
        'user_id': 1,
        'date': str(datetime.date.today()),
        'course_name': 'Edmonton Springs',
        'is_front_nine': True
    }

def test_admin_edit_round_info_round_not_found(test_round):
    request_data = {
        'date': str(datetime.date.today()),
        'course_name': 'Edmonton Springs'
    }

    response = client.patch('/admin/rounds/round_info/999', json=request_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Round not found'}


def test_admin_edit_hole(test_round, test_hole):
    request_data = {
        'par': 3,
        'score': 4
    }

    response = client.patch('/admin/rounds/round_stats/1/hole/1', json=request_data)
    assert response.status_code == status.HTTP_200_OK

    db = TestingSessionLocal()
    model = db.query(Holes).filter(Holes.round_id == 1, Holes.hole_number == 1).first()
    assert model.id == 1
    assert model.round_id == 1
    assert model.hole_number == 1
    assert model.par == request_data['par']
    assert model.score == request_data['score']
    assert model.putts == 2
    assert model.gir == False 

    assert response.json() == {
        'id': 1,
        'round_id': 1,
        'hole_number': 1,
        'par': 3,
        'score': 4,
        'putts': 2,
        'gir': False
    }


def test_admin_edit_hole_round_not_found(test_round, test_hole):
    request_data = {
        'par': 3,
        'score': 4
    }

    response = client.patch('/admin/rounds/round_stats/999/hole/1', json=request_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Round not found'}


def test_admin_edit_hole_hole_not_found(test_round, test_hole):
    request_data = {
        'par': 3,
        'score': 4
    }

    response = client.patch('/admin/rounds/round_stats/1/hole/18', json=request_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Hole not found'}


def test_admin_delete_round(test_round, test_hole):
    response = client.delete('/admin/rounds/1')

    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    db = TestingSessionLocal()
    round_model = db.query(Rounds).filter(Rounds.id == 1).first()
    assert round_model is None

    holes_list = db.query(Holes).filter(Holes.round_id == 1).all()
    assert holes_list == []


def test_admin_delete_round_round_not_found(test_round, test_hole):
    response = client.delete('/admin/rounds/999')

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Round not found'}


### USER TESTS
def test_admin_get_all_users(test_user):
    response = client.get('/admin/users')

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            'id': 1,
            'username': 'reidboykotest',
            'email': 'reidboykotest@email.com',
            'first_name': 'Reid',
            'last_name': 'Boyko',
            'admin': True
        }
    ]


def test_admin_get_user(test_user):
    response = client.get('/admin/users/1')

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        'id': 1,
        'username': 'reidboykotest',
        'email': 'reidboykotest@email.com',
        'first_name': 'Reid',
        'last_name': 'Boyko',
        'admin': True
    }


def test_admin_get_user_not_found(test_user):
    response = client.get('/admin/users/999')

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'User not found'}


def test_admin_create_user(test_user):
    request_data = {
        'email': 'test@email.com',
        'username': 'testuser',
        'first_name': 'first',
        'last_name': 'last',
        'password': 'testpassword',
        'admin': False,
    }

    response = client.post('/admin/users/create', json=request_data)
    assert response.status_code == status.HTTP_201_CREATED

    db = TestingSessionLocal()
    user = db.query(Users).filter(Users.id == 2).first()
    assert user.id == 2
    assert user.email == request_data['email']
    assert user.username == request_data['username']
    assert user.first_name == request_data['first_name']
    assert user.last_name == request_data['last_name']
    assert user.admin == request_data['admin']
    assert bcrypt_context.verify(request_data['password'], user.hashed_password)

    db.delete(user)
    db.commit()


def test_admin_change_user_password(test_user):
    request_data = {
        'new_password': 'changepasswordtest',
        'confirm_password': 'changepasswordtest'
    }

    response = client.put('/admin/users/1/password', json=request_data)
    assert response.status_code == status.HTTP_200_OK

    db = TestingSessionLocal()
    user = db.query(Users).filter(Users.id == 1).first()
    assert bcrypt_context.verify(request_data['new_password'], user.hashed_password)


def test_admin_change_user_password_user_not_found(test_user):
    request_data = {
        'new_password': 'changepasswordtest',
        'confirm_password': 'changepasswordtest'
    }

    response = client.put('/admin/users/999/password', json=request_data)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'User not found'}


def test_admin_change_user_password_failed_match(test_user):
    request_data = {
        'new_password': 'changepasswordtest',
        'confirm_password': 'somenonsense'
    }

    response = client.put('/admin/users/1/password', json=request_data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'detail': 'Passwords do not match'}


def test_admin_add_user_permissions(test_non_admin):
    
    response = client.patch('/admin/users/1/add_permissions')
    assert response.status_code == status.HTTP_200_OK

    db = TestingSessionLocal()
    user = db.query(Users).filter(Users.id == 1).first()
    assert user.id == 1
    assert user.username == 'otherusertest'
    assert user.email == 'otherusertest@email.com'
    assert user.first_name == 'Reid'
    assert user.last_name == 'Boyko'
    assert user.admin == True

    assert response.json() == {
        'id': 1,
        'username': 'otherusertest',
        'email': 'otherusertest@email.com',
        'first_name': 'Reid',
        'last_name': 'Boyko',
        'admin': True
    }

def test_admin_add_user_permissions_user_not_found(test_non_admin):
    
    response = client.patch('/admin/users/999/add_permissions')
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'User not found'}


def test_admin_remove_user_permissions(test_user):
    dummy_test = Users(
        username= 'newreidboykotest',
        email='newreidboykotest@email.com',
        first_name='Reid',
        last_name='Boyko',
        hashed_password= bcrypt_context.hash('testuserpassword'),
        admin=True
    )

    db = TestingSessionLocal()
    db.add(dummy_test)
    db.commit()

    response = client.patch('/admin/users/2/remove_permissions')
    assert response.status_code == status.HTTP_200_OK

    user = db.query(Users).filter(Users.id == 2).first()
    assert user.id == 2
    assert user.username == 'newreidboykotest'
    assert user.email == 'newreidboykotest@email.com'
    assert user.first_name == 'Reid'
    assert user.last_name == 'Boyko'
    assert user.admin == False

    assert response.json() == {
        'id': 2,
        'username': 'newreidboykotest',
        'email': 'newreidboykotest@email.com',
        'first_name': 'Reid',
        'last_name': 'Boyko',
        'admin': False
    }

    db.delete(dummy_test)
    db.commit()


def test_admin_remove_user_permissions_user_not_found(test_non_admin):

    response = client.patch('/admin/users/999/remove_permissions')
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'User not found'}


def test_admin_remove_own_permissions_error(test_user):
    response = client.patch('/admin/users/1/remove_permissions')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'detail': "Don't remove your own permissions, dummy"}


def test_admin_delete_user(test_user, test_round, test_hole):
    dummy_user = Users(
        username='newreidboykotest',
        email='newreidboykotest@email.com',
        first_name='Reid',
        last_name='Boyko',
        hashed_password= bcrypt_context.hash('testuserpassword'),
        admin=False
    )

    db = TestingSessionLocal()
    db.add(dummy_user)
    db.commit()
    db.refresh(dummy_user)

    dummy_round = Rounds(
        user_id=dummy_user.id,
        date=str(datetime.date.today()),
        course_name= 'Edmonton Country Club',
        is_front_nine= True
    )

    db.add(dummy_round)
    db.commit()
    db.refresh(dummy_round)

    dummy_hole = Holes(
        round_id = dummy_round.id,
        hole_number = 1,
        par = 4,
        score = 4,
        putts = 2,
        gir = True
    )

    db.add(dummy_hole)
    db.commit()
    db.refresh(dummy_hole)

    user_id = dummy_user.id
    round_id = dummy_round.id

    response = client.delete(f'/admin/users/delete/{dummy_user.id}')
    assert response.status_code == status.HTTP_204_NO_CONTENT

    user = db.query(Users).filter(Users.id == user_id).first()
    assert user is None

    rounds = db.query(Rounds).filter(Rounds.user_id == user_id).all()
    assert rounds == []

    holes = db.query(Holes).filter(Holes.round_id == round_id).all()
    assert holes == []


def test_admin_delete_user_not_found(test_user, test_round, test_hole):
    response = client.delete('/admin/users/delete/999')
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'User not found'}


def test_admin_delete_self(test_user, test_round, test_hole):
    response = client.delete('/admin/users/delete/1')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'detail': 'Do not delete yourself, dummy'}


def test_admin_delete_other_admin(test_user, test_round, test_hole):
    dummy_user = Users(
        username='newreidboykotest',
        email='newreidboykotest@email.com',
        first_name='Reid',
        last_name='Boyko',
        hashed_password= bcrypt_context.hash('testuserpassword'),
        admin=True
    )

    db = TestingSessionLocal()
    db.add(dummy_user)
    db.commit()
    db.refresh(dummy_user)

    response = client.delete(f'/admin/users/delete/{dummy_user.id}')
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'detail': 'You cannot delete another admin'}
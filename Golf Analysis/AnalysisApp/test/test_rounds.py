from .utils import *


def test_get_rounds(test_user, test_round):
    response = client.get('/rounds/')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{
        'id': 1,
        'user_id': 1,
        'date': str(datetime.date.today()),
        'course_name': 'Edmonton Country Club',
        'is_front_nine': True
    }]


def test_get_rounds_wrong_user(test_round, non_admin_override):
    response = client.get('/rounds/')
    assert response.json() == []


def test_get_rounds_not_authenticated(test_round, no_user_override):
    response = client.get('/rounds/')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_info_from_round(test_round, test_user):
    response = client.get(f'/rounds/round_info/{test_round.id}')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        'id': test_round.id,
        'user_id': test_user.id,
        'date': str(datetime.date.today()),
        'course_name': 'Edmonton Country Club',
        'is_front_nine': True
    }


def test_get_info_from_round_wrong_user(test_round, non_admin_override):
    response = client.get(f'/rounds/round_info/{test_round.id}')
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Round not found'}


def test_get_info_from_round_not_found(test_round, test_user):
    response = client.get('/rounds/round_info/999')
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Round not found'}


def test_get_info_from_round_not_authenitcated(test_round, no_user_override):
    response = client.get(f'/rounds/round_info/{test_round.id}')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_stats_from_round(test_round, test_hole, test_user):
    response = client.get(f'/rounds/round_stats/{test_round.id}')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        {
            'id': test_hole.id,
            'round_id': test_round.id,
            'hole_number': 1,
            'par': 4,
            'score': 4,
            'putts': 2,
            'gir': True
        }
    ]


def test_get_stats_from_round_wrong_user(test_round, non_admin_override):
    response = client.get(f'/rounds/round_stats/{test_round.id}')
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Round not found'}


def test_get_stats_from_round_not_found(test_round, test_user):
    response = client.get('/rounds/round_stats/999')
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Round not found'}


def test_get_stats_from_round_not_authenitcated(test_round, no_user_override):
    response = client.get(f'/rounds/round_stats/{test_round.id}')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_round(test_round, test_user):
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
        
    response = client.post('/rounds/create', json=request_data)
    assert response.status_code == status.HTTP_201_CREATED


def test_create_round_not_authenitcated(test_round, no_user_override):
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
    

    response = client.post('/rounds/create', json=request_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_edit_round_info(test_round, test_user):
    request_data = {
        'date': str(datetime.date.today()),
        'course_name': 'Edmonton Springs'
    }

    response = client.patch(f'/admin/rounds/round_info/{test_round.id}', json=request_data)
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


def test_edit_round_info_wrong_user(test_round, non_admin_override):
    request_data = {
        'date': str(datetime.date.today()),
        'course_name': 'Edmonton Springs'
    }
    response = client.patch(f'/rounds/round_info/{test_round.id}', json=request_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Round not found'}


def test_edit_round_info_not_found(test_round, test_user):
    request_data = {
        'date': str(datetime.date.today()),
        'course_name': 'Edmonton Springs'
    }
    response = client.patch('/rounds/round_info/999', json=request_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Round not found'}


def test_edit_round_info_not_authenitcated(test_round, no_user_override):
    request_data = {
        'date': str(datetime.date.today()),
        'course_name': 'Edmonton Springs'
    }

    response = client.patch(f'/rounds/round_info/{test_round.id}', json=request_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_edit_hole(test_round, test_hole, test_user):
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


def test_edit_hole_wrong_user(test_round, test_hole, non_admin_override):
    request_data = {
        'date': str(datetime.date.today()),
        'course_name': 'Edmonton Springs'
    }
    response = client.patch(f'/rounds/round_stats/{test_round.id}/hole/{test_hole.id}', json=request_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Round not found'}


def test_edit_hole_round_not_found(test_round, test_hole, test_user):
    request_data = {
        'date': str(datetime.date.today()),
        'course_name': 'Edmonton Springs'
    }
    response = client.patch(f'/rounds/round_stats/999/hole/{test_hole.id}', json=request_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Round not found'}


def test_edit_hole_hole_not_found(test_round, test_hole, test_user):
    request_data = {
        'date': str(datetime.date.today()),
        'course_name': 'Edmonton Springs'
    }
    response = client.patch(f'/rounds/round_stats/{test_round.id}/hole/18', json=request_data)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Hole not found'}


def test_edit_hole_not_authenitcated(test_round, test_hole, no_user_override):
    request_data = {
        'par': 3,
        'score': 4
    }

    response = client.patch(f'/rounds/round_stats/{test_round.id}/hole/{test_hole.id}', json=request_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def delete_round(test_round, test_user):
    response = client.delete(f'/admin/rounds/{test_round.id}')

    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    db = TestingSessionLocal()
    round_model = db.query(Rounds).filter(Rounds.id == 1).first()
    assert round_model is None

    holes_list = db.query(Holes).filter(Holes.round_id == 1).all()
    assert holes_list == []


def delete_round_wrong_user(test_round, non_admin_override):
    response = client.delete(f'/rounds/{test_round.id}')
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Round not found'}


def test_delete_round_not_found(test_round, test_user):
    response = client.delete('/rounds/999')
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'detail': 'Round not found'}


def test_delete_round_not_authenitcated(test_round, no_user_override):
    response = client.delete(f'/rounds/{test_round.id}')
    assert response.status_code == status.HTTP_401_UNAUTHORIZED




import pytest
from app import app  

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_login(client):
    response = client.get('/login')
    assert response.status_code == 200

def test_register(client):
    response = client.get('/register')
    assert response.status_code == 200


def test_create_task(client):
    response = client.get('/submit_estimation')
    assert response.status_code == 302
    

def test_update_task(client):
    response = client.get('/update_estimation_data_collection/664ee923b7e21da818f9e5ef')
    assert response.status_code == 200


def test_delete(client):
    response = client.get('/his_delete_item/664ee923b7e21da818f9e5ef')
    assert response.status_code == 200

def test_logout(client):
    response = client.get('/logout')
    assert response.status_code == 302
    
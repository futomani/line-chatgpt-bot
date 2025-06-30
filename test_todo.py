import pytest
from app import app, tasks

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_get_todo_page(client):
    res = client.get('/todo')
    assert res.status_code == 200
    assert b'Todo List' in res.data


def test_post_empty_task(client):
    res = client.post('/add_todo', data={'task': ''})
    assert res.status_code == 400
    assert b'Task cannot be empty' in res.data


def test_post_valid_task(client):
    tasks.clear()
    res = client.post('/add_todo', data={'task': 'Test Task'})
    assert res.status_code == 302
    assert tasks[-1] == 'Test Task'

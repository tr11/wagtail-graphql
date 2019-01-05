import pytest
from .graphql import assert_query


@pytest.mark.django_db
def test_get_user(client):
    assert_query(client, 'test_user', 'anonymous')


@pytest.mark.django_db
def test_get_user_admin(client):
    client.post('/graphql',
                {"query": 'mutation { login(username: "admin", password: "password") { user { username } } }'}
                )
    assert_query(client, 'test_user', 'admin')
    response = client.post(
        '/graphql',
        {"query": 'mutation { logout { user { username } } }'}
    )
    assert response.json() == {'data': {'logout': {'user': {'username': 'anonymous'}}}}


@pytest.mark.django_db
def test_get_user_admin_fail(client):
    client.post('/graphql',
                {"query": 'mutation { login(username: "admin", password: "fail") { user { username } } }'}
                )
    assert_query(client, 'test_user', 'anonymous')

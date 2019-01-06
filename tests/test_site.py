import pytest
from .graphql import assert_query


@pytest.mark.django_db
def test_site(client):
    client.post('/graphql',
                {"query": 'mutation { login(username: "admin", password: "password") { user { username } } }'}
                )
    assert_query(client, 'site')


@pytest.mark.django_db
def test_site_fail(client):
    response = client.post('/graphql', {"query": 'query {root { id } }'})
    assert response.status_code == 200
    assert {'data': {'root': None}} == response.json()


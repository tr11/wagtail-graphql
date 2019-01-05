import pytest
from .graphql import assert_query


@pytest.mark.django_db
def test_type(client):
    response = client.post('/graphql', {"query": "{__schema { types { name kind } } }"})
    assert response.status_code == 200
    assert {'name': 'Test_app_1HomePage', 'kind': 'OBJECT'} in response.json()['data']['__schema']['types']


@pytest.mark.django_db
def test_get_page(client):
    assert_query(client, 'test_app_1', 'get_home')

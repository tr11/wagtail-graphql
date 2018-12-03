import pytest


@pytest.mark.django_db
def test_type(client):
    response = client.post('/graphql', {"query": "{__schema { types { name kind } } }"})
    assert response.status_code == 200
    assert {'name': 'Test_app_1HomePage', 'kind': 'OBJECT'} in response.json()['data']['__schema']['types']

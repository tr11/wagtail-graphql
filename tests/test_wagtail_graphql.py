import pytest
from wagtail_graphql import __version__

EXPECTED_VERSION = '0.1.3'
EXPECTED_API_VERSION = '0.1.3'


def test_version_import():
    assert __version__ == EXPECTED_VERSION


@pytest.mark.django_db
def test_version_api(client):
    response = client.post('/graphql', {"query": "{ format }"})
    assert response.status_code == 200
    assert response.json() == {'data': {'format': EXPECTED_API_VERSION}}


@pytest.mark.django_db
def test_types(client):
    response = client.post('/graphql', {"query": "{__schema { types { name } } }"})
    assert response.status_code == 200
    assert set(x['name'] for x in response.json()['data']['__schema']['types']) == {
        'Query',
        'PageInterface',
        'Int',
        'String',
        'PageLink',
        'Boolean',
        'User',
        'ID',
        'DateTime',
        'Document',
        'Image',
        'Rect',
        'Site',
        'Test_app_1HomePage',
        'Mutation',
        '__Schema',
        '__Type',
        '__TypeKind',
        '__Field',
        '__InputValue',
        '__EnumValue',
        '__Directive',
        '__DirectiveLocation',
        'Date',
        'Float',
        'Page',
        'LoginMutation',
        'LogoutMutation',
    }

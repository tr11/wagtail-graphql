import pytest
from wagtail_graphql import __version__


def test_version_import():
    assert __version__ == '0.1.0'


@pytest.mark.django_db
def test_version(client):
    response = client.post('/graphql', {"query": "{ format }"})

    assert response.status_code == 200
    assert response.json() == {'data': {'format': __version__}}


@pytest.mark.django_db
def test_types(client):
    response = client.post('/graphql', {"query": "{__schema { types { name } } }"})
    assert response.status_code == 200
    assert response.json() == {'data': {'__schema': {'types': [{'name': 'Query'}, {'name': 'PageInterface'}, {'name': 'Int'}, {'name': 'String'}, {'name': 'PageLink'}, {'name': 'Boolean'}, {'name': 'User'}, {'name': 'ID'}, {'name': 'DateTime'}, {'name': 'Document'}, {'name': 'Image'}, {'name': 'Rect'}, {'name': 'Site'}, {'name': 'Test_app_1HomePage'}, {'name': 'Mutation'}, {'name': '__Schema'}, {'name': '__Type'}, {'name': '__TypeKind'}, {'name': '__Field'}, {'name': '__InputValue'}, {'name': '__EnumValue'}, {'name': '__Directive'}, {'name': '__DirectiveLocation'}, {'name': 'Date'}, {'name': 'Float'}]}}}

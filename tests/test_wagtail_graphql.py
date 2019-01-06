import pytest
from wagtail_graphql import __version__

EXPECTED_VERSION = '0.2.0'
EXPECTED_API_VERSION = '0.2.0'


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
        'Test_app_2PageTypeAAnotherType',
        'Test_app_2PageTypeA',
        'StringBlock',
        'Test_app_2PageTypeAStreamfieldType',
        'IntBlock',
        'Time',
        'GenericScalar',
        'Test_app_2PageTypeAThirdType',
        'DateBlock',
        'GenericScalarBlock',
        'BooleanBlock',
        'UUID',
        'FloatBlock',
        'DateTimeBlock',
        'TimeBlock',
        'Snippet',
        'Test_app_2Advert',
        'MainMenuMaxLevels',
        'FlatMenuMaxLevels',
        'SecondaryMenuItem',
        'MenuItem',
        'Menu',
        'SecondaryMenu',
        'Test_app_2PageTypeAAnotherCustomType',
        'Test_app_2PageTypeACustomType',
        'PageBlock',
        'Test_app_2CustomBlockInner',
        'Test_app_2PageTypeALinksType',
        'Test_app_2CustomBlock1',
        'Test_app_2CustomBlock2',
        'Test_app_2App2Snippet',
        'Test_app_2App2SnippetBlock',
        'ImageBlock',
        'DateTimeListBlock',
        'Test_app_2App2SnippetListBlock',
        'Test_app_2PageTypeALinksListType',
        'Test_app_2PageTypeAListsType',
        'Test_app_2CustomBlock2ListBlock',
        'Test_app_2CustomBlock1ListBlock',
        'FloatListBlock',
        'TimeListBlock',
        'DateListBlock',
        'PageInterfaceListBlock',
        'ImageListBlock',
        'Test_app_2PageTypeACustomListsType',
        'IntListBlock',
        'StringListBlock',
        'DateTimeListBlock',
        'Test_app_2App2SnippetListBlock',

    }

import pytest
from .graphql import assert_query, assert_query_fail
from django.conf import settings
IS_RELAY = settings.GRAPHQL_API.get('RELAY', False)


@pytest.mark.django_db
def test_type(client):
    response = client.post('/graphql', {"query": "{__schema { types { name kind } } }"})
    assert response.status_code == 200
    assert {'name': 'Test_app_1HomePage', 'kind': 'OBJECT'} in response.json()['data']['__schema']['types']


@pytest.mark.skipif(IS_RELAY, reason="requires the relay setting")
@pytest.mark.django_db
def test_get_page(client):
    assert_query(client, 'test_app_1', 'get_home')


@pytest.mark.skipif(not IS_RELAY, reason="requires the relay setting to be off")
@pytest.mark.django_db
def test_get_page_relay(client):
    assert_query(client, 'test_app_1', 'get_home', 'relay')


@pytest.mark.skipif(IS_RELAY, reason="requires the relay setting")
@pytest.mark.django_db
def test_get_page_latest(client):
    assert_query(client, 'test_app_1', 'get_home', 'latest')


@pytest.mark.skipif(not IS_RELAY, reason="requires the relay setting to be off")
@pytest.mark.django_db
def test_get_page_latest_relay(client):
    assert_query(client, 'test_app_1', 'get_home', 'latest', 'relay')


@pytest.mark.skipif(IS_RELAY, reason="requires the relay setting")
@pytest.mark.django_db
def test_get_page_revision(client):
    assert_query(client, 'test_app_1', 'get_home', 'revision')


@pytest.mark.skipif(not IS_RELAY, reason="requires the relay setting to be off")
@pytest.mark.django_db
def test_get_page_revision_relay(client):
    assert_query(client, 'test_app_1', 'get_home', 'revision', 'relay')


@pytest.mark.django_db
def test_get_page_doesnt_exist(client):
    assert_query(client, 'test_app_1', 'get_home', 'none')


@pytest.mark.django_db
def test_get_page_revision_doesnt_exist(client):
    assert_query_fail(client, 'test_app_1', 'get_home', 'revision', 'fail')


@pytest.mark.skipif(IS_RELAY, reason="requires the relay setting")
@pytest.mark.django_db
def test_get_pages(client):
    assert_query(client, 'test_app_1', 'get', 'pages')


@pytest.mark.skipif(not IS_RELAY, reason="requires the relay setting to be off")
@pytest.mark.django_db
def test_get_pages_relay(client):
    assert_query(client, 'test_app_1', 'get', 'pages', 'relay')


@pytest.mark.skipif(IS_RELAY, reason="requires the relay setting")
@pytest.mark.django_db
def test_get_pages_parent(client):
    assert_query(client, 'test_app_1', 'get', 'pages', 'parent')


@pytest.mark.skipif(IS_RELAY, reason="requires the relay setting")
@pytest.mark.django_db
def test_get_pages_parent_fail(client):
    assert_query_fail(client, 'test_app_1', 'get', 'pages', 'parent', 'fail')


@pytest.mark.skipif(IS_RELAY, reason="requires the relay setting")
@pytest.mark.django_db
def test_get_children(client):
    assert_query(client, 'children')


@pytest.mark.skipif(IS_RELAY, reason="requires the relay setting")
@pytest.mark.django_db
def test_show_in_menus(client):
    assert_query(client, 'showmenus')


@pytest.mark.skipif(IS_RELAY, reason="requires the relay setting")
@pytest.mark.django_db
def test_prefetch(client):
    assert_query(client, 'prefetch')

import pytest
from .graphql import assert_query, assert_query_fail
from django.conf import settings
IS_RELAY = settings.GRAPHQL_API.get('RELAY', False)


@pytest.mark.skipif(IS_RELAY, reason="requires the relay setting")
@pytest.mark.django_db
def test_settings(client):
    assert_query(client, 'settings')


@pytest.mark.skipif(not IS_RELAY, reason="requires the relay setting to be off")
@pytest.mark.django_db
def test_settings_relay(client):
    assert_query(client, 'settings', 'relay')


@pytest.mark.skipif(IS_RELAY, reason="requires the relay setting")
@pytest.mark.django_db
def test_settings_fail(client):
    assert_query_fail(client, 'settings', 'fail')

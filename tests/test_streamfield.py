import pytest
from .graphql import assert_query
from django.conf import settings
IS_RELAY = settings.GRAPHQL_API.get('RELAY', False)


@pytest.mark.skipif(IS_RELAY, reason="requires the relay setting")
@pytest.mark.django_db
def test_streamfield_scalar_blocks(client):
    assert_query(client, 'test_app_2', 'streamfield')


@pytest.mark.skipif(not IS_RELAY, reason="requires the relay setting to be off")
@pytest.mark.django_db
def test_streamfield_scalar_blocks_relay(client):
    assert_query(client, 'test_app_2', 'streamfield', 'relay')

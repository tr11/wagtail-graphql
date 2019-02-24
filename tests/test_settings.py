import pytest
from .graphql import assert_query, assert_query_fail


@pytest.mark.django_db
def test_settings(client):
    assert_query(client, 'settings')


@pytest.mark.django_db
def test_settings_fail(client):
    assert_query_fail(client, 'settings', 'fail')

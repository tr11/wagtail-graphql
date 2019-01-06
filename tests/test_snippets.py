import pytest
from .graphql import assert_query


@pytest.mark.django_db
def test_snippets(client):
    assert_query(client, 'snippets', '1')

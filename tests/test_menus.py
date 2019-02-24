import pytest
from .graphql import assert_query


@pytest.mark.django_db
def test_documents(client):
    assert_query(client, 'menus', 'all')

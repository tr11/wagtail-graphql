import pytest
from .graphql import assert_query


@pytest.mark.django_db
def test_streamfield_scalar_blocks(client):
    assert_query(client, 'test_app_2', 'streamfield')


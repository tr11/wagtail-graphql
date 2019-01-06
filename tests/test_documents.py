import pytest
from .graphql import assert_query


@pytest.mark.django_db
def test_documents(client):
    assert_query(client, 'documents', 'all')


@pytest.mark.django_db
def test_document_1(client):
    assert_query(client, 'document', '1')

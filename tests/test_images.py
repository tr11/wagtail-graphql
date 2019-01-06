import pytest
from .graphql import assert_query


@pytest.mark.django_db
def test_image(client):
    assert_query(client, 'image', '1')


@pytest.mark.django_db
def test_image_with_focal_point(client):
    assert_query(client, 'image', '2')


@pytest.mark.django_db
def test_image_with_rendition(client):
    assert_query(client, 'image', '1', 'rendition')


@pytest.mark.django_db
def test_images_list(client):
    assert_query(client, 'images', 'all')

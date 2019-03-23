import pytest


@pytest.mark.django_db
def test_reverse_models(client):
    from wagtail_graphql.registry import registry

    # force loading the api
    client.post('/graphql', {"query": "{ format }"})

    models = registry.models
    assert {v: k for k, v in models.items()} == registry.rmodels


@pytest.mark.django_db
def test_reverse_snippets(client):
    from wagtail_graphql.registry import registry

    # force loading the api
    client.post('/graphql', {"query": "{ format }"})

    snippets = registry.snippets
    assert {v: k for k, v in snippets.items()} == registry.rsnippets

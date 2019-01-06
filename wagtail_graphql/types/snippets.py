# django
from django.db import models
# graphql
from graphql.execution.base import ResolveInfo
# graphene
import graphene
# app
from ..registry import registry


def SnippetsQueryMixin():
    class Mixin:
        if registry.snippets:
            class Snippet(graphene.types.union.Union):
                class Meta:
                    types = registry.snippets.types

            snippets = graphene.List(Snippet,
                                     typename=graphene.String(required=True))

            def resolve_snippets(self, _info: ResolveInfo, typename: str) -> models.Model:
                node = registry.snippets_by_name[typename]
                cls = node._meta.model
                return cls.objects.all()
        else:  # pragma: no cover
            pass
    return Mixin

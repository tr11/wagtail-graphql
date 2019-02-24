# graphql
from graphql.execution.base import ResolveInfo
# graphene
import graphene
# graphene_django
from graphene_django.converter import String
# app
from ..registry import registry
from ..settings import settings_registry


class Settings(graphene.Interface):
    __typename = graphene.Field(String)


def SettingsQueryMixin():
    class Mixin:
        if settings_registry:
            settings = graphene.Field(Settings,
                                      name=graphene.String(required=True))

            def resolve_settings(self, _info: ResolveInfo, name):
                try:
                    result = registry.settings[name][1].objects.first()
                except KeyError:
                    raise ValueError(f"Settings '{name}' not found.")
                return result
        else:  # pragma: no cover
            pass
    return Mixin

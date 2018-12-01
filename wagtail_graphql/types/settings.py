# graphql
from graphql.execution.base import ResolveInfo
# graphene
import graphene
# graphene_django
from graphene_django.converter import String
# wagtail settings
try:
    from wagtail.contrib.settings.registry import registry as settings_registry
except ImportError:
    settings_registry = None
# app
from ..registry import registry


class Settings(graphene.Interface):
    __typename = graphene.Field(String)


class SettingsQueryMixin:
    if settings_registry:
        settings = graphene.Field(Settings,
                                  name=graphene.String(required=True))

        def resolve_settings(self, _info: ResolveInfo, name):
            try:
                result = registry.settings[name].objects.first()
            except KeyError:
                raise ValueError(f"Settings '{name}' not found.")
            return result
    else:
        pass

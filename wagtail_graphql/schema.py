# django
from django.utils.text import camel_case_to_spaces
# graphql
from graphql import ResolveInfo
# graphene
import graphene
# graphene_django
from graphene_django.converter import String
# app
from .registry import registry
from .actions import add_apps
# mixins
from .types import (
    DocumentQueryMixin,
    ImageQueryMixin,
    InfoQueryMixin,
    MenusQueryMixin,
    PagesQueryMixin,
    SettingsQueryMixin,
    SnippetsQueryMixin,
)

# api version
GRAPHQL_API_FORMAT = (0, 1, 3)

# add all the apps from the settings
add_apps()


class Query(graphene.ObjectType,
            DocumentQueryMixin,
            ImageQueryMixin,
            InfoQueryMixin,
            MenusQueryMixin,
            PagesQueryMixin,
            SettingsQueryMixin,
            SnippetsQueryMixin,
            ):
    # API Version
    format = graphene.Field(String)

    def resolve_format(self, _info: ResolveInfo):
        return '%d.%d.%d' % GRAPHQL_API_FORMAT


def mutation_parameters() -> dict:
    dict_params = {"format": graphene.Field(String)}
    dict_params.update((camel_case_to_spaces(n).replace(' ', '_'), mut.Field())
                       for n, mut in registry.forms.items())
    return dict_params


Mutations = type("Mutation",
                 (graphene.ObjectType,),
                 mutation_parameters()
                 )

schema = graphene.Schema(
    query=Query,
    mutation=Mutations,
    types=list(registry.models.values())
)

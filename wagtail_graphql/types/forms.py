# graphene
import graphene
# graphene_django
from graphene_django.converter import String


class FormField(graphene.ObjectType):
    name = graphene.Field(String)
    field_type = graphene.Field(String)


class FormError(graphene.ObjectType):
    name = graphene.Field(String)
    errors = graphene.List(String)

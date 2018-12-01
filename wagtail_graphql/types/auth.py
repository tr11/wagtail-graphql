# django
from django.contrib.auth.models import User as wagtailUser, AnonymousUser
# graphene
import graphene
from graphql.execution.base import ResolveInfo
# app types
from .core import User


class AuthQueryMixin:
    # User information
    user = graphene.Field(User)

    def resolve_user(self, info: ResolveInfo):
        user = info.context.user
        if isinstance(user, AnonymousUser):
            return wagtailUser(id='-1', username='anonymous')
        return user

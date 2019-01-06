# django
from django.contrib.auth.models import User as wagtailUser, AnonymousUser
# graphene
import graphene
from graphql.execution.base import ResolveInfo
# app types
from .core import User


def AuthQueryMixin():
    class Mixin:
        # User information
        user = graphene.Field(User)

        def resolve_user(self, info: ResolveInfo):
            user = info.context.user
            if isinstance(user, AnonymousUser):
                return wagtailUser(id='-1', username='anonymous')
            return user
    return Mixin


class LoginMutation(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    user = graphene.Field(User)

    def mutate(self, info, username, password):
        from django.contrib.auth import authenticate, login
        user = authenticate(info.context, username=username, password=password)
        if user is not None:
            login(info.context, user)
        else:
            user = wagtailUser(id='-1', username='anonymous')
        return LoginMutation(user=user)


class LogoutMutation(graphene.Mutation):
    user = graphene.Field(User)

    def mutate(self, info):
        from django.contrib.auth import logout
        logout(info.context)
        return LogoutMutation(wagtailUser(id='-1', username='anonymous'))

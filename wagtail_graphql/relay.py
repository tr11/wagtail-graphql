# graphene
import graphene
# app
from .settings import RELAY


if RELAY:
    class RelayMixin:
        node = graphene.relay.Node.Field()
else:
    class RelayMixin:   # type: ignore
        pass

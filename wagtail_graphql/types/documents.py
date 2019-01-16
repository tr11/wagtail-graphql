# graphql
from graphql.execution.base import ResolveInfo
# graphene
import graphene
# graphene_django
from graphene_django import DjangoObjectType
# graphene_django_optimizer
import graphene_django_optimizer as gql_optimizer
# wagtail documents
from wagtail.documents.models import Document as wagtailDocument
# app
from ..permissions import with_collection_permissions


class Document(DjangoObjectType):
    class Meta:
        model = wagtailDocument

    url = graphene.String()
    filename = graphene.String()
    file_extension = graphene.String()

    def resolve_tags(self: wagtailDocument, _info: ResolveInfo):
        return self.tags.all()


def DocumentQueryMixin():
    class Mixin:
        documents = graphene.List(Document)
        document = graphene.Field(Document,
                                  id=graphene.Int(required=True))

        def resolve_documents(self, info: ResolveInfo):
            return with_collection_permissions(
                info.context,
                gql_optimizer.query(
                    wagtailDocument.objects.all(),
                    info
                )
            )

        def resolve_document(self, info: ResolveInfo, id: int):
            doc = with_collection_permissions(
                info.context,
                gql_optimizer.query(
                    wagtailDocument.objects.filter(id=id),
                    info
                )
            ).first()
            return doc
    return Mixin

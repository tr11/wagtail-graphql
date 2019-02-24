# graphql
from graphql.execution.base import ResolveInfo
# django
from django.urls import reverse
# graphene
import graphene
# graphene_django
from graphene_django import DjangoObjectType
from graphene_django.converter import convert_django_field
# graphene_django_optimizer
import graphene_django_optimizer as gql_optimizer
# wagtail images
from wagtail.images.models import Image as wagtailImage
from wagtail.images.views.serve import generate_signature
# app
from ..permissions import with_collection_permissions


@convert_django_field.register(wagtailImage)
def convert_image(field, _registry=None):
    return Image(description=field.help_text, required=not field.null)      # pragma: no cover


class Rect(graphene.ObjectType):
    left = graphene.Int()
    top = graphene.Int()
    right = graphene.Int()
    bottom = graphene.Int()

    x = graphene.Int()
    y = graphene.Int()
    height = graphene.Int()
    width = graphene.Int()


class Image(DjangoObjectType):
    class Meta:
        model = wagtailImage
        exclude_fields = [
            'focal_point_x',
            'focal_point_y',
            'focal_point_width',
            'focal_point_height',
        ]

    has_focal_point = graphene.Boolean()
    focal_point = graphene.Field(Rect)

    url = graphene.String(rendition=graphene.String())
    url_link = graphene.String(rendition=graphene.String())

    def resolve_has_focal_point(self: wagtailImage, _info: ResolveInfo):
        return self.has_focal_point()

    def resolve_focal_point(self: wagtailImage, _info: ResolveInfo):
        return self.get_focal_point()

    def resolve_tags(self: wagtailImage, _info: ResolveInfo):
        return self.tags.all()

    def resolve_url(self: wagtailImage, _info: ResolveInfo, rendition: str = None):
        if not rendition:
            if not self.has_focal_point():
                rendition = "original"
            else:
                fp = self.get_focal_point()
                rendition = 'fill-%dx%d-c100' % (fp.width, fp.height)

        return generate_image_url(self, rendition)

    def resolve_url_link(self: wagtailImage, _info: ResolveInfo, rendition: str = None):
        if not rendition:
            if not self.has_focal_point():
                rendition = "original"
            else:
                fp = self.get_focal_point()
                rendition = 'fill-%dx%d-c100' % (fp.width, fp.height)
        return self.get_rendition(rendition).url


def generate_image_url(image: wagtailImage, filter_spec: str) -> str:
    signature = generate_signature(image.pk, filter_spec)
    url = reverse('wagtailimages_serve', args=(signature, image.pk, filter_spec))
    return url


def ImageQueryMixin():
    class Mixin:
        images = graphene.List(Image)
        image = graphene.Field(Image,
                               id=graphene.Int(required=True))

        def resolve_images(self, info: ResolveInfo):
            return with_collection_permissions(
                info.context,
                gql_optimizer.query(
                    wagtailImage.objects.all(),
                    info
                )
            )

        def resolve_image(self, info: ResolveInfo, id: int):
            image = with_collection_permissions(
                info.context,
                gql_optimizer.query(
                    wagtailImage.objects.filter(id=id),
                    info
                )
            ).first()
            return image
    return Mixin

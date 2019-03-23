# typings
from typing import cast
# django
from django.contrib.auth.models import User as wagtailUser
from django.contrib.contenttypes.models import ContentType
# graphql
from graphql.execution.base import ResolveInfo
from graphql.language.ast import InlineFragment
# graphene
import graphene
# graphene_django
from graphene_django import DjangoObjectType
from graphene_django.converter import convert_django_field, String, List
# wagtail
from wagtail.core.models import Page as wagtailPage, Site as wagtailSite
from taggit.managers import TaggableManager
from wagtail.core.utils import camelcase_to_underscore
# app
from ..settings import url_prefix_for_site, RELAY
from ..registry import registry
from ..permissions import with_page_permissions


class User(DjangoObjectType):
    class Meta:
        model = wagtailUser
        exclude_fields = ['password']


class Site(DjangoObjectType):
    class Meta:
        model = wagtailSite


interface_cls: graphene.Interface = graphene.relay.Node if RELAY else graphene.Interface


class Page(interface_cls):
    if not RELAY:   # use opaque ids in Relay
        id = graphene.Int(required=True)
    title = graphene.String(required=True)
    url_path = graphene.String()
    content_type = graphene.String()
    slug = graphene.String(required=True)
    path = graphene.String()
    depth = graphene.Int()
    seoTitle = graphene.String()
    numchild = graphene.Int()
    revision = graphene.Int()
    first_published_at = graphene.DateTime()
    last_published_at = graphene.DateTime()
    latest_revision_created_at = graphene.DateTime()
    live = graphene.Boolean()
    go_live_at = graphene.DateTime()
    expire_at = graphene.DateTime()
    expired = graphene.Boolean()
    locked = graphene.Boolean()
    draft_title = graphene.String()
    has_unpublished_changes = graphene.Boolean()

    def resolve_content_type(self, _info: ResolveInfo):
        self.content_type = ContentType.objects.get_for_model(self)
        return self.content_type.app_label + '.' + self.content_type.model_class().__name__

    @classmethod
    def resolve_type(cls, instance, info: ResolveInfo) -> 'Page':
        mdl = ContentType.objects.get_for_model(instance).model_class()
        try:
            model = registry.pages[mdl]
        except KeyError:  # pragma: no cover
            raise ValueError("Model %s is not a registered GraphQL type" % mdl)
        return model

    def resolve_url_path(self, info: ResolveInfo) -> str:
        self.url_path = cast(str, self.url_path)
        url_prefix = url_prefix_for_site(info)
        url = self.url_path if not self.url_path.startswith(url_prefix) else self.url_path[len(url_prefix):]
        return url.rstrip('/')

    if RELAY:
        children = graphene.ConnectionField(lambda *x: PageConnection)
    else:
        children = graphene.List(lambda *x: Page)

    def resolve_children(self, info: ResolveInfo, **_kwargs):
        query = wagtailPage.objects.child_of(self)
        return with_page_permissions(
            info.context,
            query.specific()
        ).live().order_by('path').all()


@convert_django_field.register(TaggableManager)
def convert_field_to_string(field, _registry=None):
    return List(String, description=field.help_text, required=not field.null)


def _resolve_preview(request, view):  # pragma: no cover
    from django.http import QueryDict
    page = view.get_page()
    post_data, timestamp = request.session.get(view.session_key, (None, None))
    if not isinstance(post_data, str):
        post_data = ''
    form = view.get_form(page, QueryDict(post_data))
    if not form.is_valid():
        raise ValueError("Invalid preview data")
    form.save(commit=False)
    return page


if RELAY:
    class PageConnection(graphene.relay.Connection):
        class Meta:
            node = Page

        class Edge:
            pass


def PagesQueryMixin():  # noqa: C901
    class Mixin:
        if RELAY:
            pages = graphene.ConnectionField(PageConnection)
        else:
            pages = graphene.List(Page, parent=graphene.Int())

        page = graphene.Field(Page,
                              id=graphene.Int(),
                              url=graphene.String(),
                              revision=graphene.Int(),
                              )
        preview = graphene.Field(Page,
                                 id=graphene.Int(required=True),
                                 )

        preview_add = graphene.Field(Page,
                                     app_name=graphene.String(),
                                     model_name=graphene.String(),
                                     parent=graphene.Int(required=True),
                                     )

        def resolve_pages(self, info: ResolveInfo, parent: int = None, **_kwargs):
            query = wagtailPage.objects

            # prefetch specific type pages
            selections = set(camelcase_to_underscore(f.name.value)
                             for f in info.field_asts[0].selection_set.selections
                             if not isinstance(f, InlineFragment))
            for pf in registry.page_prefetch_fields.intersection(selections):
                query = query.select_related(pf)

            if parent is not None:
                parent_page = wagtailPage.objects.filter(id=parent).first()
                if parent_page is None:
                    raise ValueError(f'Page id={parent} not found.')
                query = query.child_of(parent_page)

            return with_page_permissions(
                info.context,
                query.specific()
            ).live().order_by('path').all()

        def resolve_page(self, info: ResolveInfo, id: int = None, url: str = None, revision: int = None):
            query = wagtailPage.objects
            if id is not None:
                query = query.filter(id=id)
            elif url is not None:
                url_prefix = url_prefix_for_site(info)
                query = query.filter(url_path=url_prefix + url.rstrip('/') + '/')
            else:   # pragma: no cover
                raise ValueError("One of 'id' or 'url' must be specified")
            page = with_page_permissions(
                info.context,
                query.specific()
            ).live().first()

            if page is None:
                return None

            if revision is not None:
                if revision == -1:
                    rev = page.get_latest_revision()
                else:
                    rev = page.revisions.filter(id=revision).first()
                if not rev:
                    raise ValueError("Revision %d doesn't exist" % revision)

                page = rev.as_page_object()
                page.revision = rev.id
                return page

            return page

        def resolve_preview(self, info: ResolveInfo, id: int):   # pragma: no cover
            from wagtail.admin.views.pages import PreviewOnEdit
            request = info.context
            view = PreviewOnEdit(args=('%d' % id, ), request=request)
            return _resolve_preview(request, view)

        def resolve_preview_add(self, info: ResolveInfo, app_name: str = 'wagtailcore',
                                model_name: str = 'page', parent: int = None):  # pragma: no cover
            from wagtail.admin.views.pages import PreviewOnCreate
            request = info.context
            view = PreviewOnCreate(args=(app_name, model_name, str(parent)), request=request)
            page = _resolve_preview(request, view)
            page.id = 0  # force an id, since our schema assumes page.id is an Int!
            return page

        # Show in Menu
        show_in_menus = graphene.List(Page)

        def resolve_show_in_menus(self, info: ResolveInfo):
            return with_page_permissions(
                info.context,
                wagtailPage.objects.filter(show_in_menus=True)
            ).live().order_by('path')
    return Mixin


def InfoQueryMixin():
    class Mixin:
        # Root
        root = graphene.Field(Site)

        def resolve_root(self, info: ResolveInfo):
            user = info.context.user
            if user.is_superuser:
                return info.context.site
            else:
                return None
    return Mixin

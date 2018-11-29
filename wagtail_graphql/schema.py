# python
import string
# django
from django.conf import settings
from django.utils.text import capfirst, camel_case_to_spaces
from django.contrib.auth.models import User as wagtailUser, AnonymousUser
from django.urls import reverse
# graphene
import graphene
from graphene.types.generic import GenericScalar
from graphene.types import Scalar
# graphene_django
from graphene_django import DjangoObjectType
from graphene_django.converter import convert_django_field, String, List
# graphene_django_optimizer
import graphene_django_optimizer as gql_optimizer
# graphql
from graphql.language.ast import InlineFragment
from graphql.execution.base import ResolveInfo
# wagtail
from wagtail.core.blocks import PageChooserBlock, ListBlock, StructBlock
from wagtail.core.fields import StreamField
from wagtail.core.models import Page as wagtailPage, Site as wagtailSite
from wagtail.core.utils import camelcase_to_underscore
from taggit.managers import TaggableManager
# wagtail documents
from wagtail.documents.models import Document as wagtailDocument
# wagtail snippets
from wagtail.snippets.blocks import SnippetChooserBlock
# wagtail images
from wagtail.images.models import Image as wagtailImage
from wagtail.images.blocks import ImageChooserBlock
from wagtail.images.views.serve import generate_signature
# wagtail forms
from wagtail.contrib.forms.models import AbstractForm
# wagtail settings
from wagtail.contrib.settings.models import BaseSetting
from wagtail.contrib.settings.registry import registry as settings_registry
# wagtailmenus
try:
    from wagtailmenus.models import FlatMenu, FlatMenuItem, MainMenu, MainMenuItem
    HAS_WAGTAILMENUS = True
except ImportError:
    HAS_WAGTAILMENUS = False
# app
from .permissions import with_collection_permissions, with_page_permissions


# api version
GRAPHQL_API_FORMAT = (0, 1, 0)


def generate_image_url(image, filter_spec):
    signature = generate_signature(image.id, filter_spec)
    url = reverse('wagtailimages_serve', args=(signature, image.id, filter_spec))
    return url


@convert_django_field.register(TaggableManager)
def convert_field_to_string(field, registry=None):
    return List(String, description=field.help_text, required=not field.null)


@convert_django_field.register(StreamField)
def convert_stream_field(field, registry=None):
    return Scalar(description=field.help_text, required=not field.null)


@convert_django_field.register(wagtailImage)
def convert_image(field, registry=None):
    return Image(description=field.help_text, required=not field.null)


def _create_stream_field_type(stream_field_name, field_name, block_type_handlers):
    class Meta:
        types = tuple(set(block_type_handlers.values()))

    stream_field_type = type(
        stream_field_name + "Type",
        (graphene.Union, ),
        {'Meta': Meta}
    )

    def convert_block(block):
        block_type = block.get('type')
        value = block.get('value')
        if block_type in block_type_handlers:
            handler = block_type_handlers.get(block_type)
            if isinstance(value, dict):
                return handler(**value)
            else:
                raise NotImplementedError()
        else:
            raise NotImplementedError()

    def resolve_field(self, info):
        field = getattr(self, field_name)
        return [convert_block(block) for block in field.stream_data]

    return graphene.List(stream_field_type), resolve_field


def _is_compound_block(block):
    return isinstance(block, StructBlock)


def _is_list_block(block):
    return isinstance(block, ListBlock)


def _add_handler_resolves(dict_params, block):
    to_add = {}
    for k, v in dict_params.items():
        if isinstance(v, tuple):
            if isinstance(v[0], (List, graphene.Field)):
                val = v[0]
            else:
                val = v[0](block)
            to_add['resolve_' + k] = v[1]
        elif v != GenericScalar:
            val = v
            to_add['resolve_' + k] = _resolve
        else:
            val = v
        dict_params[k] = graphene.Field(val)
    dict_params.update(to_add)


def _class_full_name(cls):
    return cls.__module__ + "." + cls.__qualname__


def _handler(block, app, prefix=''):
    cls = block.__class__
    clsname = _class_full_name(cls)

    handler = BLOCK_HANDLERS.get(clsname)
    if handler is None:
        if _is_compound_block(block):
            node = prefix + cls.__name__
            dict_params = dict(
                (n, _handler(block_type, app, prefix))
                for n, block_type in block.child_blocks.items()
            )
            _add_handler_resolves(dict_params, block)
            tp = type(node, (graphene.ObjectType,), dict_params)
            handler = tp
            BLOCK_HANDLERS[clsname] = handler
        elif _is_list_block(block):
            child_clsname = _class_full_name(block.child_block.__class__)
            this_handler = BLOCK_HANDLERS.get(child_clsname)
            if this_handler is None:
                this_handler = _handler(block.child_block, app, prefix)
            if isinstance(this_handler, tuple):
                this_handler = this_handler[0](block.child_block)
                handler = List(this_handler), _resolve_list
            else:
                handler = List(this_handler), _resolve_simple_list
        else:
            handler = GenericScalar

    return handler


def add_apps_with_settings(settings):
    if settings_registry:
        add_app('wagtail.contrib.settings')

    for app in settings['APPS']:
        prefixes = settings.get('PREFIX', {})
        if isinstance(prefixes, str):
            prefix = prefixes
        else:
            prefix = prefixes.get(app, '{app}')
        add_app(app, prefix)


def add_app(app, prefix='{app}', exclude_models=tuple()):
    from django.contrib.contenttypes.models import ContentType
    from wagtail.snippets.models import get_snippet_models
    models = ContentType.objects.filter(app_label=app).all()
    snippets = get_snippet_models()

    for cls in snippets:
        prefix = prefix.format(app=string.capwords(app),
                               cls=cls.__name__)
        node = prefix + cls.__name__

        class Meta:
            model = cls
        dict_params = {'Meta': Meta}
        tp = type(node, (DjangoObjectType,), dict_params)
        SNIPPET_MODELS[cls] = tp
        SNIPPET_MODELS_NAME[node] = tp

    for mdl in models:
        cls = mdl.model_class()
        if cls is None or cls in exclude_models:
            continue

        prefix = prefix.format(app=string.capwords(app),
                               cls=cls.__name__)
        node = prefix + cls.__name__

        class Meta:
            model = cls
        dict_params = {'Meta': Meta}

        # check for StreamFields
        for field in cls._meta.fields:
            if isinstance(field, StreamField):
                field_name = field.name
                stream_field_name = f"{node}{string.capwords(field_name, sep='_').replace('_', '')}"
                blocks = field.stream_block.child_blocks

                handlers = dict(
                    (name,_handler(block, app, prefix))
                    for name, block in blocks.items()
                )

                f, resolve = _create_stream_field_type(
                    stream_field_name,
                    field_name,
                    handlers
                )

                dict_params.update({
                    field.name: f,
                    "resolve_" + field.name: resolve
                })

        if issubclass(cls, AbstractForm):
            # AbstractForm Page
            PAGE_PREFETCH_FIELDS.add(cls.__name__.lower())
            dict_params['Meta'].interfaces = (PageInterface, )
            dict_params['form_fields'] = graphene.List(FormField)

            def form_fields(self, info):
                return list(FormField(name=f.clean_name, field_type=f.field_type) for f in self.form_fields.all())

            dict_params['resolve_form_fields'] = form_fields
            tp = type(node, (DjangoObjectType, ), dict_params)
            PAGE_MODELS[cls] = tp

            args = type("Arguments", (), {'values': GenericScalar(),
                                          "url": graphene.String(required=True)})
            _class = cls
            _node = node

            def mutate(self, info, url, values):
                query = wagtailPage.objects.filter(url_path=URL_PREFIX + url.rstrip('/') + '/')
                instance = with_page_permissions(
                    info.context,
                    query.specific()
                ).live().first()
                user = info.context.user
                form = instance.get_form(values, None, page=instance, user=user)
                if form.is_valid():
                    # form_submission
                    instance.process_form_submission(form)
                    return FORM_MODELS[_node](result="OK")
                else:
                    return FORM_MODELS[_node](result="FAIL", errors=[FormError(*err) for err in form.errors.items()])

            dict_params = {
                "Arguments": args,
                "mutate": mutate,
                "result": graphene.String(),
                "errors": graphene.List(FormError),
            }
            tp = type(node + "Mutation", (graphene.Mutation,), dict_params)
            FORM_MODELS[node] = tp

        elif issubclass(cls, wagtailPage):
            # Page
            PAGE_PREFETCH_FIELDS.add(cls.__name__.lower())
            dict_params['Meta'].interfaces = (PageInterface, )
            tp = type(node, (DjangoObjectType, ), dict_params)
            PAGE_MODELS[cls] = tp
        elif cls in snippets:
            if cls not in SNIPPET_MODELS:
                raise ValueError("Snippet should already be registered")
        elif issubclass(cls, BaseSetting):
            dict_params['Meta'].interfaces = (Settings, )
            type(node, (DjangoObjectType, ), dict_params)
            SETTINGS_MODELS[capfirst(cls._meta.verbose_name)] = cls
        else:
            # Django Model
            tp = type(node, (DjangoObjectType, ), dict_params)
            DJANGO_MODELS[node] = tp


PAGE_PREFETCH_FIELDS = {
    'content_type', 'owner', 'live_revision', 'page_ptr'
}
PAGE_MODELS = {}
FORM_MODELS = {}
SNIPPET_MODELS = {}
SNIPPET_MODELS_NAME = {}
TYPES = []
DJANGO_MODELS = {}
SETTINGS_MODELS = {}


class User(DjangoObjectType):
    class Meta:
        model = wagtailUser
        exclude_fields = ['password']


class Site(DjangoObjectType):
    class Meta:
        model = wagtailSite


class PageInterface(graphene.Interface):
    id = graphene.Int(required=True)
    title = graphene.String(required=True)
    url_path = graphene.String()
    content_type = graphene.String()
    slug = graphene.String(required=True)
    path = graphene.String()
    depth = graphene.Int()
    seoTitle = graphene.String()
    numchild = graphene.Int()

    @graphene.resolve_only_args
    def resolve_content_type(self):
        return self.content_type.app_label + '.' + self.content_type.model_class().__name__

    @classmethod
    def resolve_type(cls, instance, info: ResolveInfo):
        if isinstance(instance, int):
            return PAGE_MODELS[type(wagtailPage.objects.filter(id=instance).specific().first())]

        model = PAGE_MODELS[instance.content_type.model_class()]
        return model

    @graphene.resolve_only_args
    def resolve_url_path(self):
        url = self.url_path if not self.url_path.startswith(URL_PREFIX) else self.url_path[len(URL_PREFIX):]
        return url.rstrip('/')


class PageLink(DjangoObjectType):
    class Meta:
        model = wagtailPage
        interfaces = (PageInterface, )

    @graphene.resolve_only_args
    def resolve_url_path(self):
        url = self.url_path if not self.url_path.startswith(URL_PREFIX) else self.url_path[len(URL_PREFIX):]
        return url.rstrip('/')


class Document(DjangoObjectType):
    class Meta:
        model = wagtailDocument

    url = graphene.String()
    filename = graphene.String()
    file_extension = graphene.String()

    def resolve_tags(self, info):
        return self.tags.all()


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

    @graphene.resolve_only_args
    def resolve_has_focal_point(self: wagtailImage):
        return self.has_focal_point()

    @graphene.resolve_only_args
    def resolve_focal_point(self: wagtailImage):
        return self.get_focal_point()

    @graphene.resolve_only_args
    def resolve_tags(self: wagtailImage):
        return self.tags.all()

    @graphene.resolve_only_args
    def resolve_url(self: wagtailImage, rendition: str = None):
        if not rendition:
            if not self.has_focal_point():
                rendition = "original"
            else:
                fp = self.get_focal_point()
                rendition = 'fill-%dx%d-c100' % (fp.width, fp.height)
        # return self.get_rendition(rendition).url

        return generate_image_url(self, rendition)

    @graphene.resolve_only_args
    def resolve_url_link(self: wagtailImage, rendition: str = None):
        if not rendition:
            if not self.has_focal_point():
                rendition = "original"
            else:
                fp = self.get_focal_point()
                rendition = 'fill-%dx%d-c100' % (fp.width, fp.height)
        return self.get_rendition(rendition).url


def _snippet_handler(block):
    tp = SNIPPET_MODELS[block.target_model]
    return tp


def _resolve_snippet(self, info: ResolveInfo):
    if self is None:
        return None
    id_ = getattr(self, info.field_name)
    cls = info.return_type.graphene_type._meta.model
    obj = cls.objects.filter(id=id_).first()
    return obj


def _resolve_image(self, info: ResolveInfo):
    if self is None:
        return None
    id_ = getattr(self, info.field_name)
    return wagtailImage.objects.filter(id=id_).first()


def _resolve_page(self, info: ResolveInfo):
    if self is None:
        return None
    id_ = self if isinstance(self, int) else getattr(self, info.field_name)
    return wagtailPage.objects.filter(id=id_).specific().first()


def _resolve(self, info: ResolveInfo):
    data = getattr(self, info.field_name)
    cls = info.return_type
    return cls.graphene_type(**data)


def _resolve_simple_list(self, info: ResolveInfo):
    if self is None:
        return None
    data = getattr(self, info.field_name)
    cls = info.return_type.of_type.graphene_type
    if cls == GenericScalar:
        return list(d for d in data)
    return list(cls(**d) for d in data)


def _resolve_list(self, info: ResolveInfo):
    if self is None:
        return None
    ids = getattr(self, info.field_name)
    cls = info.return_type.of_type.graphene_type._meta.model
    objs = dict((x.id, x) for x in cls.objects.filter(id__in=ids).all())
    return list(objs.get(i) for i in ids)


class Settings(graphene.Interface):
    __typename = graphene.Field(String)


class FormField(graphene.ObjectType):
    name = graphene.Field(String)
    field_type = graphene.Field(String)


class FormError(graphene.ObjectType):
    name = graphene.Field(String)
    errors = graphene.List(String)


if HAS_WAGTAILMENUS:
    class MenuItem(DjangoObjectType):
        class Meta:
            model = MainMenuItem

    class Menu(DjangoObjectType):
        class Meta:
            model = MainMenu
            only_fields = ['max_levels', 'menu_items']

    class SecondaryMenuItem(DjangoObjectType):
        class Meta:
            model = FlatMenuItem

    class SecondaryMenu(DjangoObjectType):
        class Meta:
            model = FlatMenu
            only_fields = ['title', 'handle', 'heading', 'max_levels', 'menu_items']


BLOCK_HANDLERS = {
    # # classes
    # ImageChooserBlock: (lambda x: Image, _resolve_image),
    # PageChooserBlock: (lambda x: PageInterface, _resolve_page),
    # SnippetChooserBlock: (_snippet_handler, _resolve_snippet),
    # names
    "wagtail.images.blocks.ImageChooserBlock": (lambda x: Image, _resolve_image),
    "wagtail.core.blocks.field_block.PageChooserBlock": (lambda x: PageInterface, _resolve_page),
    "wagtail.snippets.blocks.SnippetChooserBlock": (_snippet_handler, _resolve_snippet),
}
SETTINGS = settings.GRAPHQL_API
URL_PREFIX = SETTINGS.get('URL_PREFIX', '')

add_apps_with_settings(SETTINGS)

SNIPPET_MODELS_REVERSE = dict((v, k) for k, v in SNIPPET_MODELS.items())

MODELS = {}
MODELS.update(PAGE_MODELS)
MODELS.update(SNIPPET_MODELS)
MODELS.update(FORM_MODELS)
MODELS.update(DJANGO_MODELS)
MODELS.update(SETTINGS_MODELS)
MODELS.update((k, v) for k, v in BLOCK_HANDLERS.items() if not isinstance(v, tuple))
MODELS_REVERSE = dict((v, k) for k, v in MODELS.items())


class Query(graphene.ObjectType):
    if PAGE_MODELS:
        class Page(graphene.types.union.Union):
            class Meta:
                types = tuple(PAGE_MODELS.values())
    else:
        Page = PageInterface

    if SNIPPET_MODELS:
        class Snippet(graphene.types.union.Union):
            class Meta:
                types = tuple(SNIPPET_MODELS.values())
    else:
        Snippet = PageInterface

    # User information
    user = graphene.Field(User)

    # Show in Menu
    show_in_menus = graphene.List(PageLink)

    # Pages
    pages = graphene.List(PageInterface,
                          parent=graphene.Int())
    page = graphene.Field(PageInterface,
                          id=graphene.Int(),
                          url=graphene.String()
                          )

    # Documents
    documents = graphene.List(Document)
    document = graphene.Field(Document,
                              id=graphene.Int(required=True))

    # Images
    images = graphene.List(Image)
    image = graphene.Field(Image,
                           id=graphene.Int(required=True))

    # Snippets
    if SNIPPET_MODELS:
        snippets = graphene.List(Snippet,
                                 typename=graphene.String(required=True))

    # Root
    root = graphene.Field(Site)

    # Version
    format = graphene.Field(String)

    @graphene.resolve_only_args
    def resolve_format(self):
        return '%d.%d.%d' % GRAPHQL_API_FORMAT

    def resolve_user(self, info: ResolveInfo):
        user = info.context.user
        if isinstance(user, AnonymousUser):
            return wagtailUser(id='-1', username='anonymous')
        return user

    def resolve_root(self, info: ResolveInfo):
        user = info.context.user
        if user.is_superuser:
            return info.context.site
        else:
            return None

    def resolve_show_in_menus(self, info: ResolveInfo):
        return with_page_permissions(
            info.context,
            wagtailPage.objects.filter(show_in_menus=True)
        ).live().order_by('path')

    def resolve_menus(self):
        return []

    def resolve_pages(self, info: ResolveInfo, parent: int = None):
        query = wagtailPage.objects

        # prefetch specific type pages
        selections = set(camelcase_to_underscore(f.name.value)
                         for f in info.field_asts[0].selection_set.selections
                         if not isinstance(f, InlineFragment))
        for pf in PAGE_PREFETCH_FIELDS.intersection(selections):
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

    def resolve_page(self, info: ResolveInfo, id: int = None, url: str = None):
        if id is None and url is None:
            raise ValueError("One of 'id' or 'url' must be specified")
        query = wagtailPage.objects
        if id is not None:
            query = query.filter(id=id)
        else:
            query = query.filter(url_path=URL_PREFIX + url.rstrip('/') + '/')
        page = with_page_permissions(
            info.context,
            query.select_related('content_type').specific()
        ).live().first()
        if page is None:
            return None
        return page

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

    def resolve_snippets(self, info: ResolveInfo, typename: str):
        node = SNIPPET_MODELS_NAME[typename]
        cls = node._meta.model
        return cls.objects.all()

    if settings_registry:
        settings = graphene.Field(Settings,
                                  name=graphene.String(required=True))

        def resolve_settings(self, info: ResolveInfo, name):
            try:
                result = SETTINGS_MODELS[name].objects.first()
            except KeyError:
                raise ValueError(f"Settings '{name}' not found.")
            return result

    if HAS_WAGTAILMENUS:
        main_menu = graphene.List(Menu)
        secondary_menu = graphene.Field(SecondaryMenu,
                                        handle=graphene.String(required=True))
        secondary_menus = graphene.List(SecondaryMenu)

        def resolve_main_menu(self, info: ResolveInfo):
            return MainMenu.objects.all()

        def resolve_secondary_menus(self, info: ResolveInfo):
            return FlatMenu.objects.all()

        def resolve_secondary_menu(self, info: ResolveInfo, handle):
            return FlatMenu.objects.filter(handle=handle).first()


def mutation_parameters() -> dict:
    dict_params = {"format": graphene.Field(String)}
    dict_params.update((camel_case_to_spaces(n).replace(' ', '_'), mut.Field()) for n, mut in FORM_MODELS.items())
    return dict_params


Mutations = type("Mutation",
                 (graphene.ObjectType,),
                 mutation_parameters()
                 )

schema = graphene.Schema(
    query=Query,
    mutation=Mutations,
    types=list(MODELS.values())
)

# python
import string
from typing import Type, Set
# django
from django.utils.text import camel_case_to_spaces
# graphene
import graphene
from graphene.types.generic import GenericScalar
# graphene_django
from graphene_django import DjangoObjectType
# wagtail
from wagtail.core.fields import StreamField
from wagtail.core.models import Page as wagtailPage
# wagtail forms
from wagtail.contrib.forms.models import AbstractForm
# wagtail settings
from wagtail.contrib.settings.models import BaseSetting
# app
from .registry import registry
from .permissions import with_page_permissions
from .settings import url_prefix_for_site, RELAY
# app types
from .types import (
    Page,
    Settings,
    FormError,
    FormField,
)


def _add_form(cls: Type[AbstractForm], node: str, dict_params: dict) -> Type[graphene.Mutation]:
    if node in registry.forms:  # pragma: no cover
        return registry.forms[node]

    registry.page_prefetch_fields.add(cls.__name__.lower())
    dict_params['Meta'].interfaces += (Page,)
    dict_params['form_fields'] = graphene.List(FormField)

    def form_fields(self, _info):
        return list(FormField(name=field_.clean_name, field_type=field_.field_type,
                              label=field_.label, required=field_.required,
                              help_text=field_.help_text, choices=field_.choices,
                              default_value=field_.default_value)
                    for field_ in self.form_fields.all())

    dict_params['resolve_form_fields'] = form_fields
    registry.pages[cls] = type(node, (DjangoObjectType,), dict_params)

    args = type("Arguments", (), {'values': GenericScalar(),
                                  "url": graphene.String(required=True)})
    _node = node

    def mutate(_self, info, url, values):
        url_prefix = url_prefix_for_site(info)
        query = wagtailPage.objects.filter(url_path=url_prefix + url.rstrip('/') + '/')
        instance = with_page_permissions(
            info.context,
            query.specific()
        ).live().first()
        user = info.context.user
        # convert camelcase to dashes
        values = {camel_case_to_spaces(k).replace(' ', '-'): v for k, v in values.items()}
        form = instance.get_form(values, None, page=instance, user=user)
        if form.is_valid():
            # form_submission
            instance.process_form_submission(form)
            return registry.forms[_node](result="OK")
        else:
            return registry.forms[_node](result="FAIL", errors=[FormError(*err) for err in form.errors.items()])

    dict_params = {
        "Arguments": args,
        "mutate": mutate,
        "result": graphene.String(),
        "errors": graphene.List(FormError),
    }
    tp = type(node + "Mutation", (graphene.Mutation,), dict_params)  # type: Type[graphene.Mutation]
    registry.forms[node] = tp
    return tp


def _add_page(cls: Type[wagtailPage], node: str, dict_params: dict) -> Type[DjangoObjectType]:
    if cls in registry.pages:   # pragma: no cover
        return registry.pages[cls]
    registry.page_prefetch_fields.add(cls.__name__.lower())
    dict_params['Meta'].interfaces += (Page,)
    tp = type(node, (DjangoObjectType,), dict_params)  # type: Type[DjangoObjectType]
    registry.pages[cls] = tp
    return tp


def _add_setting(cls: Type[BaseSetting], node: str, dict_params: dict) -> Type[DjangoObjectType]:
    if not hasattr(cls, 'name'):    # we always need a name field
        cls.name = cls.__name__
    dict_params['Meta'].interfaces += (Settings,)
    tp = type(node, (DjangoObjectType,), dict_params)  # type: Type[DjangoObjectType]
    registry.settings[node] = (tp, cls)
    return tp


def _add_snippet(cls: type, node: str, dict_params: dict) -> Type[DjangoObjectType]:
    if cls in registry.snippets:   # pragma: no cover
        return registry.snippets[cls]
    tp = type(node, (DjangoObjectType,), dict_params)  # type: Type[DjangoObjectType]
    registry.snippets[cls] = tp
    registry.snippets_by_name[node] = tp
    return tp


def _add_django_model(_cls: type, node: str, dict_params: dict) -> Type[DjangoObjectType]:
    if node in registry.django:   # pragma: no cover
        return registry.django[node]
    tp = type(node, (DjangoObjectType,), dict_params)  # type: Type[DjangoObjectType]
    registry.django[node] = tp
    return tp


def _add_streamfields(cls: wagtailPage, node: str, dict_params: dict, app: str, prefix: str) -> None:
    from .types.streamfield import (
        block_handler,
        stream_field_handler,
    )

    for field in cls._meta.fields:
        if isinstance(field, StreamField):
            field_name = field.name
            stream_field_name = f"{node}{string.capwords(field_name, sep='_').replace('_', '')}"
            blocks = field.stream_block.child_blocks

            handlers = dict(
                (name, block_handler(block, app, prefix))
                for name, block in blocks.items()
            )

            f, resolve = stream_field_handler(
                stream_field_name,
                field_name,
                handlers
            )

            dict_params.update({
                field.name: f,
                "resolve_" + field.name: resolve
            })


def _register_model(registered: Set[type], cls: type, snippet: bool,
                    app: str, prefix: str, override_name=None) -> None:
    if cls in registered:
        return

    prefix = prefix.format(app=string.capwords(app),
                           cls=cls.__name__)
    node = override_name or prefix + cls.__name__

    # dict parameters to create GraphQL type
    class Meta:
        model = cls
        interfaces = (graphene.relay.Node, ) if RELAY else tuple()

    dict_params = {'Meta': Meta}

    # add streamfield handlers
    _add_streamfields(cls, node, dict_params, app, prefix)

    if snippet:
        _add_snippet(cls, node, dict_params)
    elif issubclass(cls, AbstractForm):
        _add_form(cls, node, dict_params)
    elif issubclass(cls, wagtailPage):
        _add_page(cls, node, dict_params)
    elif issubclass(cls, BaseSetting):
        _add_setting(cls, node, dict_params)
    else:  # Django Model
        _add_django_model(cls, node, dict_params)

    registered.add(cls)


def add_app(app: str, prefix: str = '{app}') -> None:
    from django.contrib.contenttypes.models import ContentType
    from wagtail.snippets.models import get_snippet_models
    snippets = get_snippet_models()
    models = [mdl.model_class()
              for mdl in ContentType.objects.filter(app_label=app).all()]
    snippets = [s for s in snippets if s in models]
    to_register = [x for x in snippets + models if x is not None]
    registered: Set = set()

    # prefetch content_types
    ContentType.objects.get_for_models(*to_register)

    for cls in to_register:
        _register_model(registered, cls, cls in snippets, app, prefix)


def add_apps_with_settings(settings: dict) -> None:
    apps = settings.get('APPS', [])

    for app in apps:
        prefixes = settings.get('PREFIX', {})
        if isinstance(prefixes, str):
            prefix = prefixes   # pragma: no cover
        else:
            prefix = prefixes.get(app, '{app}')
        add_app(app, prefix=prefix)
    if not apps:   # pragma: no cover
        import logging
        logging.warning("No APPS specified for wagtail_graphql")


def add_apps() -> None:
    from .settings import SETTINGS
    add_apps_with_settings(SETTINGS)


# standard page
_register_model(set(), wagtailPage, False, 'wagtailcore', '', override_name='BasePage')

# python
from typing import Tuple, Callable
# graphql
from graphql.execution.base import ResolveInfo
# graphene
import graphene
from graphene.types.generic import GenericScalar
from graphene.types import Scalar
# graphene_django
from graphene_django.converter import convert_django_field, List
# wagtail
import wagtail.core.blocks
import wagtail.images.blocks
import wagtail.snippets.blocks
from wagtail.core.blocks import Block, ListBlock, StructBlock
from wagtail.core.fields import StreamField
# app
from ..registry import registry
# app types
from .core import PageInterface, wagtailPage
from .images import Image, wagtailImage

# types
StreamFieldHandlerType = Tuple[graphene.List, Callable[[StreamField, ResolveInfo], list]]


@convert_django_field.register(StreamField)
def convert_stream_field(field, _registry=None):
    return Scalar(description=field.help_text, required=not field.null)


def _scalar_block(graphene_type):
    tp = registry.scalar_blocks.get(graphene_type)
    if not tp:
        node = '%sBlock' % graphene_type
        tp = type(node, (graphene.ObjectType,), {
            'value': graphene.Field(graphene_type),
            'field': graphene.Field(graphene.String),
        })
        registry.scalar_blocks[graphene_type] = tp
    return tp, lambda x: tp


def _resolve_scalar(key, type_):
    def resolve(self, _info: ResolveInfo):
        return type_(value=self, field=key)
    return resolve


def stream_field_handler(stream_field_name: str, field_name: str, block_type_handlers: dict) -> StreamFieldHandlerType:
    for k, t in block_type_handlers.items():
        # Unions must reference NamedTypes, so for scalar types we need to create a new type to encapsulate the scalar
        if not isinstance(t, tuple) and issubclass(t, Scalar):
            typ, typ_fn = _scalar_block(t)
            block_type_handlers[k] = typ_fn, _resolve_scalar(k, typ)

    types_ = list(block_type_handlers.values())

    for i, t in enumerate(types_):
        if isinstance(t, tuple):
            types_[i] = t[0](None)

    class Meta:
        types = tuple(set(types_))

    def resolve_type(self, _info: ResolveInfo):
        return self.__class__

    stream_field_type = type(
        stream_field_name + "Type",
        (graphene.Union, ),
        {
            'Meta': Meta,
            'resolve_type': resolve_type
        }
    )

    def convert_block(block, info: ResolveInfo, is_lazy=True):
        if is_lazy:
            block_type = block.get('type')
            value = block.get('value')
        else:
            block_type, value = block[:2]
        if block_type in block_type_handlers:
            handler = block_type_handlers.get(block_type)
            if isinstance(handler, tuple):
                tp, resolver = handler
                return resolver(value, info)
            else:
                if isinstance(value, dict):
                    return handler(**value)
                else:
                    raise NotImplementedError()
        else:
            raise NotImplementedError()

    def resolve_field(self, info: ResolveInfo):
        field = getattr(self, field_name)
        return [convert_block(block, info, field.is_lazy) for block in field.stream_data]

    return graphene.List(stream_field_type), resolve_field


def _is_compound_block(block):
    return isinstance(block, StructBlock)


def _is_list_block(block):
    return isinstance(block, ListBlock)


def _is_custom_type(block):
    return hasattr(block, "__graphql_type__")


def _add_handler_resolves(dict_params, block):
    to_add = {}
    for k, v in dict_params.items():
        if isinstance(v, tuple):
            if isinstance(v[0], (List, graphene.Field)):
                val = v[0]
            else:
                val = v[0](block)
            to_add['resolve_' + k] = v[1]
        elif not issubclass(v, Scalar):
            val = v
            to_add['resolve_' + k] = _resolve
        else:
            val = v
        dict_params[k] = graphene.Field(val)
    dict_params.update(to_add)


def _class_full_name(cls):
    return cls.__module__ + "." + cls.__qualname__


def block_handler(block: Block, app, prefix=''):
    cls = block.__class__
    handler = registry.blocks.get(cls)

    if handler is None:
        if _is_custom_type(block):
            target_block_type = block.__graphql_type__()
            this_handler = block_handler(target_block_type, app, prefix)
            if isinstance(this_handler, tuple):
                raise NotImplementedError()
            if hasattr(block, '__graphql_resolve__'):
                resolver = _resolve_custom(block, this_handler)
            elif issubclass(target_block_type, Scalar):
                resolver = _resolve_generic_scalar
            else:
                raise TypeError("Non Scalar custom types need an explicit __graphql_resolve__ method.")
            handler = (lambda x: this_handler, resolver)
        elif _is_compound_block(block):
            node = prefix + cls.__name__
            dict_params = dict(
                (n, block_handler(block_type, app, prefix))
                for n, block_type in block.child_blocks.items()
            )
            _add_handler_resolves(dict_params, block)
            tp = type(node, (graphene.ObjectType,), dict_params)
            handler = tp
            registry.blocks[cls] = handler
        elif _is_list_block(block):
            this_handler = registry.blocks.get(block.child_block.__class__)
            if this_handler is None:
                this_handler = block_handler(block.child_block, app, prefix)
            if isinstance(this_handler, tuple):
                this_handler = this_handler[0](block.child_block)
                handler = List(this_handler), _resolve_list
            else:
                handler = List(this_handler), _resolve_simple_list
        else:
            handler = GenericScalar

    return handler


def _snippet_handler(block):
    tp = registry.snippets[block.target_model]
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


def _resolve_custom(block, hdl):
    def _inner(self, info: ResolveInfo):
        cls = info.return_type
        if isinstance(self, dict):
            data = self
        else:
            data = getattr(self, info.field_name)
        value = block.__graphql_resolve__(data, info)

        if hasattr(cls, "serialize"):
            return cls.serialize(value)
        return hdl(**value)
    return _inner


def _resolve_generic_scalar(self, info: ResolveInfo):
    data = getattr(self, info.field_name)
    cls = info.return_type
    return cls.serialize(data)


def _resolve_simple_list(self, info: ResolveInfo):
    if self is None:
        return None
    data = getattr(self, info.field_name)
    cls = info.return_type.of_type.graphene_type
    if issubclass(cls, Scalar):
        return list(d for d in data)
    return list(cls(**d) for d in data)


def _resolve_list(self, info: ResolveInfo):
    if self is None:
        return None
    ids = getattr(self, info.field_name)
    cls = info.return_type.of_type.graphene_type._meta.model
    objs = dict((x.id, x) for x in cls.objects.filter(id__in=ids).all())
    return list(objs.get(i) for i in ids)


registry.blocks.update({
    # choosers
    wagtail.images.blocks.ImageChooserBlock: (lambda x: Image, _resolve_image),
    wagtail.core.blocks.PageChooserBlock: (lambda x: PageInterface, _resolve_page),
    wagtail.snippets.blocks.SnippetChooserBlock: (_snippet_handler, _resolve_snippet),
    # standard fields
    wagtail.core.blocks.CharBlock: graphene.types.String,
    wagtail.core.blocks.URLBlock: graphene.types.String,
    wagtail.core.blocks.DateBlock: graphene.types.Date,
    wagtail.core.blocks.DateTimeBlock: graphene.types.DateTime,
    wagtail.core.blocks.BooleanBlock: graphene.types.Boolean,
    wagtail.core.blocks.IntegerBlock: graphene.types.Int,
    wagtail.core.blocks.FloatBlock: graphene.types.Float,
    wagtail.core.blocks.DecimalBlock: graphene.types.String,
    wagtail.core.blocks.TextBlock: graphene.types.String,
})

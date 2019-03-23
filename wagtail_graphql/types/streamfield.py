# python
from typing import Tuple, Callable
import datetime
# graphql
from graphql import GraphQLScalarType
from graphql.execution.base import ResolveInfo
# graphene
import graphene
from graphene.utils.str_converters import to_snake_case
from graphene.types.generic import GenericScalar
from graphene.types import Scalar
# graphene_django
from graphene_django.converter import convert_django_field, List
# dateutil
from dateutil.parser import parse as dtparse
# wagtail
import wagtail.core.blocks
import wagtail.images.blocks
import wagtail.snippets.blocks
from wagtail.core.blocks import Block, ListBlock, StructBlock
from wagtail.core.fields import StreamField
# app
from ..registry import registry
from .. import settings
# app types
from .core import Page, wagtailPage
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
    return tp


def _resolve_scalar(key, type_):
    type_str = str(type_)
    if type_str == 'DateBlock':
        def resolve(self, _info: ResolveInfo):
            return type_(value=dtparse(self), field=key)
    elif type_str == 'DateTimeBlock':
        def resolve(self, _info: ResolveInfo):
            return type_(value=dtparse(self), field=key)
    elif type_str == 'TimeBlock':
        def resolve(self, _info: ResolveInfo):
            return type_(value=datetime.time.fromisoformat(self), field=key)
    else:
        def resolve(self, _info: ResolveInfo):
            return type_(value=self, field=key)
    return resolve


def _page_block():
    tp = registry.scalar_blocks.get(Page)
    if not tp:
        node = 'PageBlock'
        tp = type(node, (graphene.ObjectType,), {
            'value': graphene.Field(Page),
            'field': graphene.Field(graphene.String),
        })
        registry.scalar_blocks[Page] = tp
    return tp


def _resolve_page_block(key, type_):
    def resolve(self, info: ResolveInfo):
        return type_(value=_resolve_page(self, info), field=key)
    return resolve


def _image_block():
    tp = registry.scalar_blocks.get(Image)
    if not tp:
        node = 'ImageBlock'
        tp = type(node, (graphene.ObjectType,), {
            'value': graphene.Field(Image),
            'field': graphene.Field(graphene.String),
        })
        registry.scalar_blocks[Image] = tp
    return tp


def _resolve_image_block(key, type_):
    def resolve(self, info: ResolveInfo):
        return type_(value=_resolve_image(self, info), field=key)
    return resolve


def _snippet_block(typ):
    tp = registry.scalar_blocks.get(typ)
    if not tp:
        node = '%sBlock' % typ
        tp = type(node, (graphene.ObjectType,), {
            'value': graphene.Field(typ),
            'field': graphene.Field(graphene.String),
        })
        registry.scalar_blocks[typ] = tp
    return tp


def _resolve_snippet_block(key, type_, snippet_type):
    def resolve(self, info: ResolveInfo):
        info.return_type = snippet_type
        return type_(value=_resolve_snippet(self, info), field=key)
    return resolve


def _list_block(typ):
    tp = registry.scalar_blocks.get((List, typ))
    if not tp:
        node = '%sListBlock' % typ
        tp = type(node, (graphene.ObjectType,), {
            'value': graphene.List(typ),
            'field': graphene.Field(graphene.String),
        })
        registry.scalar_blocks[(List, typ)] = tp
    return tp


def _resolve_list_block_scalar(key, type_, of_type):
    type_str = str(of_type)
    if type_str == 'Date' or type_str == 'DateTime':
        def resolve(self, _info: ResolveInfo):
            return type_(value=list(dtparse(s) for s in self), field=key)
    elif type_str == 'Time':
        def resolve(self, _info: ResolveInfo):
            return type_(value=list(datetime.time.fromisoformat(s) for s in self), field=key)
    else:
        def resolve(self, _info: ResolveInfo):
            return type_(value=list(s for s in self), field=key)
    return resolve


def _resolve_list_block(key, type_, of_type):
    if issubclass(of_type, Scalar):
        resolve = _resolve_list_block_scalar(key, type_, of_type)
    elif of_type == Image:
        def resolve(self, info: ResolveInfo):
            return type_(value=list(_resolve_image(s, info) for s in self), field=key)
    elif of_type == Page:
        def resolve(self, info: ResolveInfo):
            return type_(value=list(_resolve_page(s, info) for s in self), field=key)
    elif of_type in registry.snippets.values():
        def resolve(self, info: ResolveInfo):
            info.return_type = of_type
            return type_(value=list(_resolve_snippet(s, info) for s in self), field=key)
    else:
        def resolve(self, info: ResolveInfo):
            info.return_type = of_type
            return type_(value=list(of_type(**s) for s in self), field=key)
    return resolve


def _create_root_blocks(block_type_handlers: dict):
    for k, t in block_type_handlers.items():
        if not isinstance(t, tuple) and issubclass(t, Scalar):
            typ = _scalar_block(t)
            block_type_handlers[k] = typ, _resolve_scalar(k, typ)
        elif isinstance(t, tuple) and isinstance(t[0], List):
            typ = _list_block(t[0].of_type)
            block_type_handlers[k] = typ, _resolve_list_block(k, typ, t[0].of_type)
        elif isinstance(t, tuple) and issubclass(t[0], Page):
            typ = _page_block()
            block_type_handlers[k] = typ, _resolve_page_block(k, typ)
        elif isinstance(t, tuple) and issubclass(t[0], Image):
            typ = _image_block()
            block_type_handlers[k] = typ, _resolve_image_block(k, typ)
        elif isinstance(t, tuple) and t[0] in registry.snippets.values():
            typ = _snippet_block(t[0])
            block_type_handlers[k] = typ, _resolve_snippet_block(k, typ, t[0])


def convert_block(block, block_type_handlers: dict, info: ResolveInfo, is_lazy=True):
    if is_lazy:
        block_type = block.get('type')
        value = block.get('value')
    else:
        block_type, value = block[:2]
    if block_type in block_type_handlers:
        handler = block_type_handlers[block_type]
        if isinstance(handler, tuple):
            tp, resolver = handler
            return resolver(value, info)
        else:
            if isinstance(value, dict):
                return handler(**value)
            else:
                raise NotImplementedError()  # pragma: no cover
    else:
        raise NotImplementedError()  # pragma: no cover


def _resolve_type(self, _info: ResolveInfo):
    return self.__class__


def stream_field_handler(stream_field_name: str, field_name: str, block_type_handlers: dict) -> StreamFieldHandlerType:
    # add Generic Scalars (default)
    if settings.LOAD_GENERIC_SCALARS:
        _scalar_block(GenericScalar)

    # Unions must reference NamedTypes, so for scalar types we need to create a new type to
    # encapsulate scalars, page links, images, snippets
    _create_root_blocks(block_type_handlers)

    types_ = list(block_type_handlers.values())
    for i, t in enumerate(types_):
        if isinstance(t, tuple):
            types_[i] = t[0]

    class Meta:
        types = tuple(set(types_))

    stream_field_type = type(
        stream_field_name + "Type",
        (graphene.Union, ),
        {
            'Meta': Meta,
            'resolve_type': _resolve_type
        }
    )

    def resolve_field(self, info: ResolveInfo):
        field = getattr(self, field_name)
        return [convert_block(block, block_type_handlers, info, field.is_lazy) for block in field.stream_data]

    return graphene.List(stream_field_type), resolve_field


def _is_compound_block(block):
    return isinstance(block, StructBlock)


def _is_list_block(block):
    return isinstance(block, ListBlock)


def _is_custom_type(block):
    return hasattr(block, "__graphql_type__")


def _add_handler_resolves(dict_params):
    to_add = {}
    for k, v in dict_params.items():
        if k == 'field':    # pragma: no cover
            raise ValueError("StructBlocks cannot have fields named 'field'")
        if isinstance(v, tuple):
            val = v[0]
            to_add['resolve_' + k] = v[1]
        elif issubclass(v, (graphene.types.DateTime, graphene.types.Date)):
            val = v
            to_add['resolve_' + k] = _resolve_datetime
        elif issubclass(v, graphene.types.Time):
            val = v
            to_add['resolve_' + k] = _resolve_time
        elif not issubclass(v, Scalar):
            val = v
            to_add['resolve_' + k] = _resolve
        else:
            val = v
        dict_params[k] = graphene.Field(val)
    dict_params.update(to_add)


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
            _add_handler_resolves(dict_params)
            dict_params.update({  # add the field name
                'field': graphene.Field(graphene.String),
                'resolve_field': lambda *x: block.name,
            })
            tp = type(node, (graphene.ObjectType,), dict_params)
            handler = tp
            registry.blocks[cls] = handler
        elif _is_list_block(block):
            this_handler = block_handler(block.child_block, app, prefix)
            if isinstance(this_handler, tuple):
                handler = List(this_handler[0]), _resolve_list(*this_handler)
            else:
                handler = List(this_handler), _resolve_simple_list
        else:
            handler = GenericScalar

    if cls == wagtail.snippets.blocks.SnippetChooserBlock:
        handler = (handler[0](block), handler[1])   # type: ignore

    return handler


def _snippet_handler(block):
    tp = registry.snippets[block.target_model]
    return tp


def _resolve_snippet(self, info: ResolveInfo):
    if self is None:    # pragma: no cover
        return None
    field = to_snake_case(info.field_name)
    id_ = self if isinstance(self, int) else getattr(self, field)
    if hasattr(info.return_type, 'graphene_type'):
        cls = info.return_type.graphene_type._meta.model
    else:
        cls = info.return_type._meta.model
    obj = cls.objects.filter(id=id_).first()
    return obj


def _resolve_image(self, info: ResolveInfo):
    if self is None:    # pragma: no cover
        return None
    field = to_snake_case(info.field_name)
    id_ = self if isinstance(self, int) else getattr(self, field)
    return wagtailImage.objects.filter(id=id_).first()


def _resolve_page(self, info: ResolveInfo):
    if self is None:    # pragma: no cover
        return None
    field = to_snake_case(info.field_name)
    id_ = self if isinstance(self, int) else getattr(self, field)
    return wagtailPage.objects.filter(id=id_).specific().first()


def _resolve(self, info: ResolveInfo):
    if self is None:    # pragma: no cover
        return None
    field = to_snake_case(info.field_name)
    data = getattr(self, field)
    cls = info.return_type
    return cls.graphene_type(**data)


def _resolve_datetime(self, info: ResolveInfo):
    if self is None:    # pragma: no cover
        return None
    field = to_snake_case(info.field_name)
    data = getattr(self, field)
    return dtparse(data) if data else None


def _resolve_time(self, info: ResolveInfo):
    if self is None:    # pragma: no cover
        return None
    field = to_snake_case(info.field_name)
    data = getattr(self, field)
    return datetime.time.fromisoformat(data) if data else None


def _resolve_custom(block, hdl):
    def _inner(self, info: ResolveInfo):
        if self is None:    # pragma: no cover
            return None
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
    if self is None:    # pragma: no cover
        return None
    data = getattr(self, info.field_name)
    cls = info.return_type
    return cls.serialize(data)


def _resolve_simple_list(self, info: ResolveInfo):
    if self is None:    # pragma: no cover
        return None
    field = to_snake_case(info.field_name)
    data = getattr(self, field)
    cls = info.return_type.of_type
    if isinstance(cls, (Scalar, GraphQLScalarType)):
        return list(d for d in data)
    return list(cls(**d) for d in data)


def _resolve_list(tp, inner_resolver):
    def resolve(self, info: ResolveInfo):
        if self is None:    # pragma: no cover
            return None
        field = to_snake_case(info.field_name)
        ids = getattr(self, field)
        info.return_type = tp
        return list(inner_resolver(i, info) for i in ids)
    return resolve


registry.blocks.update({
    # choosers
    wagtail.images.blocks.ImageChooserBlock: (Image, _resolve_image),
    wagtail.core.blocks.PageChooserBlock: (Page, _resolve_page),
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
    wagtail.core.blocks.TimeBlock: graphene.types.Time,
    wagtail.core.blocks.RichTextBlock: graphene.types.String,
    wagtail.core.blocks.RawHTMLBlock: graphene.types.String,
    wagtail.core.blocks.BlockQuoteBlock: graphene.types.String,
    wagtail.core.blocks.ChoiceBlock: graphene.types.String,
    wagtail.core.blocks.RegexBlock: graphene.types.String,
    wagtail.core.blocks.EmailBlock: graphene.types.String,
    wagtail.core.blocks.StaticBlock: graphene.types.String,
})

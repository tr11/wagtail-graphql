from .core import (
    PageInterface,
    PageLink,
    Site,
    User,
    # mixins
    InfoQueryMixin,
    PagesQueryMixin,
)
from .documents import (
    Document,
    # mixins
    DocumentQueryMixin,
)
from .forms import FormField, FormError
from .images import (
    Image,
    # mixins
    ImageQueryMixin,
)
from .settings import Settings, SettingsQueryMixin
from .snippets import SnippetsQueryMixin

__all__ = [
    # core
    'PageInterface',
    'PageLink',
    'Settings',
    'Site',
    'User',
    # documents
    'Document',
    # forms
    'FormError',
    'FormField',
    # images
    'Image',
    # mixins
    'DocumentQueryMixin',
    'ImageQueryMixin',
    'InfoQueryMixin',
    'MenusQueryMixin',
    'PagesQueryMixin',
    'SettingsQueryMixin',
    'SnippetsQueryMixin',
]

# menus

try:
    from django.conf import settings
    if 'wagtailmenus' not in settings.INSTALLED_APPS:
        raise ImportError()

    from .menus import MenusQueryMixin, Menu, MenuItem, SecondaryMenu, SecondaryMenuItem  # noqa: F401

    __all__.extend([
        # menus
        'Menu',
        'MenuItem',
        'SecondaryMenu',
        'SecondaryMenuItem',
    ])

    HAS_WAGTAILMENUS = True
except ImportError:
    # type: ignore
    class _MenusQueryMixin:
        pass
    MenusQueryMixin = _MenusQueryMixin
    HAS_WAGTAILMENUS = False

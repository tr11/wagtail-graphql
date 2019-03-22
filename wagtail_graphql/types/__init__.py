from .core import (
    Page,
    Site,
    User,
    # mixins
    InfoQueryMixin,
    PagesQueryMixin,
)
from .auth import (
    LoginMutation,
    LogoutMutation,
    # mixins
    AuthQueryMixin,
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
# noinspection PyUnresolvedReferences
from . import converters    # noqa: F401

__all__ = [
    # core
    'Page',
    'Settings',
    'Site',
    'User',
    # auth
    'AuthQueryMixin',
    'LoginMutation',
    'LogoutMutation',
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
        raise ImportError()  # pragma: no cover

    from .menus import MenusQueryMixin, Menu, MenuItem, SecondaryMenu, SecondaryMenuItem  # noqa: F401

    __all__.extend([
        # menus
        'Menu',
        'MenuItem',
        'SecondaryMenu',
        'SecondaryMenuItem',
    ])

    HAS_WAGTAILMENUS = True
except ImportError:  # pragma: no cover
    def MenusQueryMixin():
        # type: ignore
        class _MenusQueryMixin:
            pass
        return _MenusQueryMixin
    HAS_WAGTAILMENUS = False

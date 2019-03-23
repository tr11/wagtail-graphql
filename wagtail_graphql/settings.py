# django
from django.conf import settings
# graphql
from graphql import ResolveInfo

# settings
if hasattr(settings, 'GRAPHQL_API'):
    SETTINGS = settings.GRAPHQL_API
else:   # pragma: no cover
    SETTINGS = {}
URL_PREFIX = SETTINGS.get('URL_PREFIX', {})
LOAD_GENERIC_SCALARS = SETTINGS.get('GENERIC_SCALARS', True)
RELAY = SETTINGS.get('RELAY', False)

# wagtail settings
try:
    from wagtail.contrib.settings.registry import registry as settings_registry
except ImportError:  # pragma: no cover
    settings_registry = None


def url_prefix_for_site(info: ResolveInfo):
    hostname = info.context.site.hostname
    return URL_PREFIX.get(
        hostname,
        info.context.site.root_page.url_path.rstrip('/')
    )

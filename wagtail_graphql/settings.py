# django
from django.conf import settings
# graphql
from graphql import ResolveInfo

if hasattr(settings, 'GRAPHQL_API'):
    SETTINGS = settings.GRAPHQL_API
else:
    SETTINGS = {}
URL_PREFIX = SETTINGS.get('URL_PREFIX', {})


def url_prefix_for_site(info: ResolveInfo):
    hostname = info.context.site.hostname
    return URL_PREFIX.get(
        hostname,
        info.context.site.root_page.url_path.rstrip('/')
    )

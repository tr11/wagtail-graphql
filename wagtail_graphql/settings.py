# django
from django.conf import settings
# graphql
from graphql import ResolveInfo


SETTINGS = settings.GRAPHQL_API
URL_PREFIX = SETTINGS.get('URL_PREFIX', {})


def url_prefix_for_site(info: ResolveInfo):
    hostname = info.context.site.hostname
    return URL_PREFIX.get(
        hostname,
        info.context.site.root_page.url_path.rstrip('/')
    )

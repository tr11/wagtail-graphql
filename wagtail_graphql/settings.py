# django
from django.conf import settings


SETTINGS = settings.GRAPHQL_API
URL_PREFIX = SETTINGS.get('URL_PREFIX', '')

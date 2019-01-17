from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
CORS_ORIGIN_ALLOW_ALL = DEBUG

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'l_0ybxo5&rg-b&5-ya$a5v-kks7&znfl)b52@n9@5qt@to$b%j'

# SECURITY WARNING: define the correct hosts in production!
ALLOWED_HOSTS = ['*'] 

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


try:
    from .local import *
except ImportError:
    pass

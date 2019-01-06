# django
from django.db import models
# graphene_django
from graphene import String
from graphene_django.converter import convert_django_field


@convert_django_field.register(models.DecimalField)
@convert_django_field.register(models.DurationField)
def convert_force_string(field, _registry=None):
    return String(description=field.help_text, required=not field.null)

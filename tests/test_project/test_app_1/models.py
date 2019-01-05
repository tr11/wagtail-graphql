from django.db import models
from wagtail.admin.edit_handlers import FieldPanel

from wagtail.core.models import Page


class HomePage(Page):
    field_char = models.CharField(max_length=10, null=True)
    field_int = models.IntegerField(null=True)
    field_bool = models.BooleanField(default=False)
    field_date = models.DateField(null=True)
    field_datetime = models.DateTimeField(null=True)

    content_panels = Page.content_panels + [
        FieldPanel('field_char'),
        FieldPanel('field_int'),
        FieldPanel('field_bool'),
        FieldPanel('field_date'),
        FieldPanel('field_datetime'),
    ]

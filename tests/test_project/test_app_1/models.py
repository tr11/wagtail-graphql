from django.db import models
from wagtail.admin.edit_handlers import FieldPanel

from wagtail.core.models import Page
from wagtail.snippets.models import register_snippet


class HomePage(Page):
    field_char = models.CharField(max_length=10, null=True)
    field_int = models.IntegerField(null=True)
    field_bool = models.BooleanField(default=False)
    field_date = models.DateField(null=True)
    field_datetime = models.DateTimeField(null=True)
    field_url = models.URLField(null=True)
    field_decimal = models.DecimalField(null=True, decimal_places=2, max_digits=5)
    field_email = models.EmailField(null=True)
    field_float = models.FloatField(null=True)
    field_duration = models.DurationField(null=True)
    field_intp = models.PositiveIntegerField(null=True)
    field_smallintp = models.PositiveSmallIntegerField(null=True)
    field_smallint = models.SmallIntegerField(null=True)
    field_text = models.TextField(null=True)
    field_time = models.TimeField(null=True)
    field_ip = models.GenericIPAddressField(null=True)
    field_uuid = models.UUIDField(null=True)

    content_panels = Page.content_panels + [
        FieldPanel('field_char'),
        FieldPanel('field_int'),
        FieldPanel('field_bool'),
        FieldPanel('field_date'),
        FieldPanel('field_datetime'),
        FieldPanel('field_url'),
        FieldPanel('field_decimal'),
        FieldPanel('field_email'),
        FieldPanel('field_float'),
        FieldPanel('field_duration'),
        FieldPanel('field_intp'),
        FieldPanel('field_smallintp'),
        FieldPanel('field_smallint'),
        FieldPanel('field_text'),
        FieldPanel('field_time'),
        FieldPanel('field_ip'),
        FieldPanel('field_uuid'),
    ]


@register_snippet
class Advert(models.Model):
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)

    panels = [
        FieldPanel('url'),
        FieldPanel('text'),
    ]

    def __str__(self):
        return self.text

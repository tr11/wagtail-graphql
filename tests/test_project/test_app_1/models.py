from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel
from wagtail.contrib.forms.models import AbstractForm, AbstractFormField

from wagtail.core.models import Page
from wagtail.snippets.models import register_snippet


class HomePage(Page):
    field_char = models.CharField(max_length=10, null=True, blank=True)
    field_int = models.IntegerField(null=True, blank=True)
    field_bool = models.BooleanField(default=False)
    field_date = models.DateField(null=True, blank=True)
    field_datetime = models.DateTimeField(null=True, blank=True)
    field_url = models.URLField(null=True, blank=True)
    field_decimal = models.DecimalField(null=True, decimal_places=2, max_digits=5, blank=True)
    field_email = models.EmailField(null=True, blank=True)
    field_float = models.FloatField(null=True, blank=True)
    field_duration = models.DurationField(null=True, blank=True)
    field_intp = models.PositiveIntegerField(null=True, blank=True)
    field_smallintp = models.PositiveSmallIntegerField(null=True, blank=True)
    field_smallint = models.SmallIntegerField(null=True, blank=True)
    field_text = models.TextField(null=True, blank=True)
    field_time = models.TimeField(null=True, blank=True)
    field_ip = models.GenericIPAddressField(null=True, blank=True)
    field_uuid = models.UUIDField(null=True, blank=True)

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


class FormField(AbstractFormField):
    page = ParentalKey('FormPage', on_delete=models.CASCADE, related_name='form_fields')


class FormPage(AbstractForm):
    body = models.TextField()
    thank_you_text = models.TextField(blank=True)

    content_panels = AbstractForm.content_panels + [
        FieldPanel('body'),
        FieldPanel('thank_you_text', classname="full"),
        InlinePanel('form_fields', label="Form fields"),
    ]

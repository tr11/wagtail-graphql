from django.db import models
from wagtail.core.fields import StreamField
from wagtail.core.models import Page
from wagtail.core import blocks
from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.images.blocks import ImageChooserBlock
from wagtail.core.blocks import PageChooserBlock
from wagtail.snippets.blocks import SnippetChooserBlock
from wagtail.snippets.models import register_snippet
from wagtail.contrib.settings.models import BaseSetting, register_setting


@register_setting
class SiteBranding(BaseSetting):
    site_setting1 = models.TextField()
    site_setting2 = models.TextField()

    panels = [
        FieldPanel('site_setting1'),
        FieldPanel('site_setting2'),
    ]


@register_snippet
class App2Snippet(models.Model):
    text = models.CharField(max_length=255)

    panels = [
        FieldPanel('text'),
    ]

    def __str__(self):
        return self.text


class CustomBlockInner(blocks.StructBlock):
    field_text = blocks.TextBlock(required=False)


class CustomBlock1(blocks.StructBlock):
    field_char = blocks.CharBlock(required=False)
    field_text = blocks.TextBlock(required=False)
    field_email = blocks.EmailBlock(required=False)
    field_int = blocks.IntegerBlock(required=False)
    field_float = blocks.FloatBlock(required=False)
    field_decimal = blocks.DecimalBlock(required=False)
    field_regex = blocks.RegexBlock(regex=r'^[0-9]{3}$', required=False)
    field_url = blocks.URLBlock(required=False)
    field_bool = blocks.BooleanBlock(required=False)
    field_date = blocks.DateBlock(required=False)
    field_time = blocks.TimeBlock(required=False)
    field_datetime = blocks.DateTimeBlock(required=False)
    field_rich = blocks.RichTextBlock(required=False)
    field_raw = blocks.RawHTMLBlock(required=False)
    field_quote = blocks.BlockQuoteBlock(required=False)
    field_choice = blocks.ChoiceBlock(choices=[('tea', 'Tea'), ('coffee', 'Coffee')], icon='cup', required=False)
    field_static = blocks.StaticBlock(required=False)
    field_list = blocks.ListBlock(blocks.CharBlock, required=False)
    field_list_2 = blocks.ListBlock(CustomBlockInner, required=False)


class CustomBlock2(blocks.StructBlock):
    field_link = PageChooserBlock(required=False)
    field_link_list = blocks.ListBlock(PageChooserBlock(), required=False)
    field_image = ImageChooserBlock(required=False)
    field_image_list = blocks.ListBlock(ImageChooserBlock(), required=False)
    field_snippet = SnippetChooserBlock(target_model=App2Snippet, required=False)
    field_snippet_list = blocks.ListBlock(SnippetChooserBlock(target_model=App2Snippet), required=False)


class PageTypeA(Page):
    streamfield = StreamField([
        ('h1', blocks.CharBlock(icon="title", classname="title")),
        ('h2', blocks.CharBlock(icon="subtitle", classname="subtitle")),
        ('n1', blocks.IntegerBlock(icon="subtitle", classname="subtitle")),
    ], null=True, blank=True)

    another = StreamField([
        ('h3', blocks.CharBlock(icon="title", classname="title")),
        ('h4', blocks.CharBlock(icon="subtitle", classname="subtitle")),
        ('n2', blocks.IntegerBlock(icon="subtitle", classname="subtitle")),
    ], null=True, blank=True)

    third = StreamField([
        ('char', blocks.CharBlock()),
        ('text', blocks.TextBlock()),
        ('email', blocks.EmailBlock()),
        ('int', blocks.IntegerBlock()),
        ('float', blocks.FloatBlock()),
        ('decimal', blocks.DecimalBlock()),
        ('regex', blocks.RegexBlock(regex=r'^[0-9]{3}$')),
        ('url', blocks.URLBlock()),
        ('bool', blocks.BooleanBlock()),
        ('date', blocks.DateBlock()),
        ('time', blocks.TimeBlock()),
        ('datetime', blocks.DateTimeBlock()),
        ('rich', blocks.RichTextBlock()),
        ('raw', blocks.RawHTMLBlock()),
        ('quote', blocks.BlockQuoteBlock()),
        ('choice', blocks.ChoiceBlock(choices=[('tea', 'Tea'), ('coffee', 'Coffee')], icon='cup')),
        ('static', blocks.StaticBlock()),
    ], null=True)

    links = StreamField([
        ('image', ImageChooserBlock()),
        ('page', PageChooserBlock()),
        ('snippet', SnippetChooserBlock(target_model=App2Snippet)),
    ], null=True)

    lists = StreamField([
        ('char', blocks.ListBlock(blocks.CharBlock())),
        ('text', blocks.ListBlock(blocks.TextBlock())),
        ('int', blocks.ListBlock(blocks.IntegerBlock())),
        ('float', blocks.ListBlock(blocks.FloatBlock())),
        ('decimal', blocks.ListBlock(blocks.DecimalBlock())),
        ('date', blocks.ListBlock(blocks.DateBlock())),
        ('time', blocks.ListBlock(blocks.TimeBlock())),
        ('datetime', blocks.ListBlock(blocks.DateTimeBlock())),
    ], null=True)

    links_list = StreamField([
        ('image', blocks.ListBlock(ImageChooserBlock())),
        ('page', blocks.ListBlock(PageChooserBlock())),
        ('snippet', blocks.ListBlock(SnippetChooserBlock(target_model=App2Snippet))),
    ], null=True)

    custom = StreamField([
        ('custom1', CustomBlock1()),
        ('custom2', CustomBlock2()),
    ], null=True)

    another_custom = StreamField([
        ('custom1', CustomBlock1()),
        ('custom2', CustomBlock2()),
    ], null=True)

    custom_lists = StreamField([
        ('custom1', blocks.ListBlock(CustomBlock1())),
        ('custom2', blocks.ListBlock(CustomBlock2())),
    ], null=True)

    content_panels = [
        FieldPanel('title', classname="full title"),
        StreamFieldPanel('streamfield'),
        StreamFieldPanel('another'),
        StreamFieldPanel('third'),
        StreamFieldPanel('links'),
        StreamFieldPanel('custom'),
        StreamFieldPanel('another_custom'),
        StreamFieldPanel('lists'),
        StreamFieldPanel('links_list'),
        StreamFieldPanel('custom_lists'),
    ]



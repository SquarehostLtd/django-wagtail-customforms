from __future__ import absolute_import, unicode_literals

from django.db import models

from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.core.blocks import StreamBlock
from wagtail.core.fields import RichTextField, StreamField
from wagtail.core.models import Page
from modelcluster.fields import ParentalKey

from customforms.models import FormPageMixin
from customforms.blocks import FormChooserBlock


"""
Create a StreamBlock containing a FormChooserBlock.
"""
class DemoStreamBlock(StreamBlock):
    form = FormChooserBlock()


"""
Add the StreamBlock to the page as a StreamField.
Include StreamFieldPanel in content panels.
"""
class HomePage(Page):
    body = StreamField(DemoStreamBlock)

    content_panels = Page.content_panels + [
        StreamFieldPanel('body', classname="full"),
    ]


"""
Inherit from FormPageMixin and add foreignkey to Form model
Then include the form in the template see example template.
"""
class HomeFormPage(FormPageMixin, Page):
    body = RichTextField(blank=True)

    form = ParentalKey(
        'customforms.Form',
        related_name='pages',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    content_panels = Page.content_panels + [
        FieldPanel('body', classname="full"),
        FieldPanel('form', classname="full"),
    ]

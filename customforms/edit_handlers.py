from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from wagtail.admin.edit_handlers import BaseChooserPanel

from .models import Form
from .widgets import AdminFormChooser


class FormChooserPanel(BaseChooserPanel):
    object_type_name = 'form'

    def widget_overrides(self):
        return {self.field_name: AdminFormChooser}

import json

from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from wagtail.admin.widgets import AdminChooser
from .models import Form


class AdminFormChooser(AdminChooser):
    choose_one_text = _('Choose a form')
    choose_another_text = _('Choose another form')
    link_to_chosen_text = _('Edit this form')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.form_model = Form

    def render_html(self, name, value, attrs):
        instance, value = self.get_instance_and_id(self.form_model, value)
        original_field_html = super().render_html(name, value, attrs)

        return render_to_string("customforms/forms/widgets/form_chooser.html", {
            'widget': self,
            'original_field_html': original_field_html,
            'attrs': attrs,
            'value': value,
            'form': instance,
        })

    def render_js_init(self, id_, name, value):
        return "createFormChooser({0});".format(json.dumps(id_))

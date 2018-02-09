from django.conf.urls import include, url
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from django.utils.translation import ugettext_lazy as _

from wagtail.contrib.modeladmin.options import (
    ModelAdmin, ModelAdminGroup, modeladmin_register)
from wagtail.admin.edit_handlers import (
    FieldPanel, FieldRowPanel,
    InlinePanel, MultiFieldPanel
)
from wagtail.admin.menu import MenuItem
from wagtail.core import hooks
from . import admin_urls

from .models import Form, FormSubmission


class FormAdmin(ModelAdmin):
    model = Form
    menu_label = 'Forms'
    menu_icon = 'form'
    panels = [
        InlinePanel('form_fields', label="Form fields"),
    ]

class FormSubmissionAdmin(ModelAdmin):
    model = FormSubmission
    menu_label = 'Form Submissions'
    menu_icon = 'form'

class MyModelAdminGroup(ModelAdminGroup):
    menu_label = 'Custom forms'
    menu_icon = 'form'
    menu_order = 200
    items = (FormAdmin,)
modeladmin_register(MyModelAdminGroup)


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^forms/', include(admin_urls, namespace='customforms')),
    ]


class FormsMenuItem(MenuItem):
    def is_shown(self, request):
        return True


@hooks.register('register_admin_menu_item')
def register_forms_menu_item():
    return FormsMenuItem(
        _('Form Submissions'), reverse('customforms:index'),
        name='forms', classnames='icon icon-form', order=700
    )


@hooks.register('insert_editor_js')
def editor_js():
    js_files = [
        static('customforms/js/form-chooser.js'),
    ]
    js_includes = format_html_join(
        '\n', '<script src="{0}"></script>',
        ((filename, ) for filename in js_files)
    )
    return js_includes + format_html(
        """
        <script>
            window.chooserUrls.formChooser = '{0}';
        </script>
        """,
        reverse('customforms:chooser')
    )

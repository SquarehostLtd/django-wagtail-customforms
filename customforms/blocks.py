from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string

from wagtail.core.blocks import ChooserBlock

from .models import Form
from .widgets import AdminFormChooser


# class FormBlock(StructBlock):
#     form =


class FormChooserBlock(ChooserBlock):
    @cached_property
    def target_model(self):
        return Form

    @cached_property
    def widget(self):
        return AdminFormChooser

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        request = context.get('request')
        if request and request.method == 'POST':
            form = value.get_form(request.POST, request.FILES, page=value, user=request.user)
            if form.is_valid():
                value.process_form_submission(form)
                messages.add_message(request, messages.SUCCESS, 'Thank you for submitting the form.')
                context['redirect'] = request.path_info
                form = value.get_form(page=value, user=request.user)
            else:
                messages.add_message(request, messages.ERROR, 'There was an error on the form, please correct it.')
        else:
            form = value.get_form(page=value, user=request.user)

        context['form'] = form
        if value.display_title:
            context['form_title'] = value.title
        if value.button_alignment:
            context['button_alignment'] = value.button_alignment
        return context

    def render(self, value, context=None):
        """
        Return a text rendering of 'value', suitable for display on templates. By default, this will
        use a template (with the passed context, supplemented by the result of get_context) if a
        'template' property is specified on the block, and fall back on render_basic otherwise.
        """
        template = self.get_template(context=context, value=value)
        if not template:
            return self.render_basic(value, context=context)

        if context is None:
            new_context = self.get_context(value)
        else:
            new_context = self.get_context(value, parent_context=dict(context))

        return mark_safe(render_to_string(template, new_context))

    def get_template(self, context=None, value=None):
        if not value.form_template or value.form_template == 'standard':
            return getattr(self.meta, 'template', None)
        return value.form_template

    class Meta:
        icon = "form"
        template = 'customforms/blocks/form.html'

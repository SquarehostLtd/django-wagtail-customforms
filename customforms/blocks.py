from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.functional import cached_property
from django.utils.html import format_html

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
        return context

    class Meta:
        icon = "form"
        template = 'customforms/blocks/form.html'

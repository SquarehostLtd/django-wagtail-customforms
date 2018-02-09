from __future__ import absolute_import, unicode_literals

from django.conf import settings
from django.contrib import messages
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.forms import Widget, CharField
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _

from wagtail.admin.edit_handlers import (
    FieldPanel, FieldRowPanel,
    InlinePanel, MultiFieldPanel
)
from wagtail.core.fields import RichTextField
from wagtail.core.models import Page, CollectionMember
from wagtail.contrib.forms.forms import FormBuilder, BaseForm, WagtailAdminFormPageForm
from wagtail.contrib.forms.models import FORM_FIELD_CHOICES, AbstractEmailForm, AbstractFormField, AbstractFormSubmission
from wagtail.search import index
from wagtail.search.queryset import SearchableQuerySetMixin
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel

import os, json


NEW_FORM_FIELD_CHOICES = FORM_FIELD_CHOICES + (('blocktext', _('Block of text')),)


class CustomInput(Widget):
    template_name = 'customform/forms/widgets/blocktext.html'


class CustomBlockTextField(CharField):
    widget = CustomInput

    def __init__(self, *args, **kwargs):
        super(CustomBlockTextField, self).__init__(*args, **kwargs)
        self.label = ''


class CustomFormBuilder(FormBuilder):
    def create_blocktext_field(self, field, options):
        if field.content:
            options['required'] = False
            options['initial'] = field.content
        return CustomBlockTextField(**options)

    FIELD_TYPES = {
        'singleline': FormBuilder.create_singleline_field,
        'multiline': FormBuilder.create_multiline_field,
        'date': FormBuilder.create_date_field,
        'datetime': FormBuilder.create_datetime_field,
        'email': FormBuilder.create_email_field,
        'url': FormBuilder.create_url_field,
        'number': FormBuilder.create_number_field,
        'dropdown': FormBuilder.create_dropdown_field,
        'multiselect': FormBuilder.create_multiselect_field,
        'radio': FormBuilder.create_radio_field,
        'checkboxes': FormBuilder.create_checkboxes_field,
        'checkbox': FormBuilder.create_checkbox_field,
        'blocktext': create_blocktext_field,
    }


class CustomWagtailAdminFormPageForm(WagtailAdminFormPageForm):
    class Media:
        js = ('customforms/js/custom-form-fields.js',)


class FormField(AbstractFormField):
    field_type = models.CharField(
        verbose_name=_('field type'),
        max_length=16,
        choices=NEW_FORM_FIELD_CHOICES
    )

    default_value = models.TextField(
        verbose_name=_('default value'),
        blank=True,
        help_text=_('Default value. Comma separated values supported for checkboxes.')
    )

    content = RichTextField(
        verbose_name=_('content'),
        blank=True,
        help_text=_('This is used for Blocks of text.')
    )

    panels = [
        FieldPanel('label', classname="formbuilder-label"),
        FieldPanel('help_text', classname="formbuilder-help"),
        FieldPanel('required', classname="formbuilder-required"),
        FieldPanel('field_type', classname="formbuilder-type"),
        FieldPanel('choices', classname="formbuilder-choices"),
        FieldPanel('default_value', classname="formbuilder-default"),
        FieldPanel('content', classname="formbuilder-content"),
    ]

    form = ParentalKey(
        'Form',
        related_name='form_fields',
        on_delete=models.CASCADE,
        null=True
    )


class FormSubmission(AbstractFormSubmission):
    class Meta:
        verbose_name = _('form submission')
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name='form_sub',
        null=True
    )

    form = models.ForeignKey(
        'customforms.Form',
        on_delete=models.CASCADE
    )


class FormQuerySet(SearchableQuerySetMixin, models.QuerySet):
    pass


class Form(CollectionMember, index.Indexed, ClusterableModel):
    form_builder = CustomFormBuilder
    base_form_class = CustomWagtailAdminFormPageForm
    template = 'customform/customform.html'


    title = models.CharField(
        max_length=255
    )

    to_address = models.CharField(
        verbose_name=_('to address'), max_length=255, blank=True,
        help_text=_("Optional - form submissions will be emailed to these addresses. Separate multiple addresses by comma.")
    )
    from_address = models.CharField(verbose_name=_('from address'), max_length=255, blank=True)
    subject = models.CharField(verbose_name=_('subject'), max_length=255, blank=True)

    uploaded_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_('uploaded by user'),
        null=True,
        blank=True,
        editable=False,
        on_delete=models.SET_NULL
    )

    created_at = models.DateTimeField(verbose_name=_('created at'), auto_now_add=True)

    panels = [
        FieldPanel('title', classname="full"),
        MultiFieldPanel([
            FieldRowPanel([
                FieldPanel('from_address', classname="col6"),
                FieldPanel('to_address', classname="col6"),
            ]),
            FieldPanel('subject'),
        ], "Email"),
        InlinePanel('form_fields', label="Form fields"),
    ]

    search_fields = CollectionMember.search_fields + [
        index.SearchField('title', partial_match=True, boost=10),
        index.FilterField('title'),
        index.FilterField('to_address', partial_match=True),
        index.FilterField('from_address', partial_match=True),
        index.FilterField('subject', partial_match=True),
    ]

    admin_form_fields = (
        'title',
        'to_address',
        'from_address',
        'subject',
        'collection',
        # 'form_fields'
    )

    objects = FormQuerySet.as_manager()

    def __str__(self):
        return self.title

    def __init__(self, *args, **kwargs):
        super(Form, self).__init__(*args, **kwargs)
        if not hasattr(self, 'landing_page_template'):
            name, ext = os.path.splitext(self.template)
            self.landing_page_template = name + '_landing' + ext

    def process_form_submission(self, form):
        submission = self.get_submission_class().objects.create(
            form_data=json.dumps(form.cleaned_data, cls=DjangoJSONEncoder),
            form=self,
        )
        if self.to_address:
            self.send_mail(form)
        return submission

    def send_mail(self, form):
        addresses = [x.strip() for x in self.to_address.split(',')]
        content = []
        for field in form:
            value = field.value()
            if isinstance(value, list):
                value = ', '.join(value)
            content.append('{}: {}'.format(field.label, value))
        content = '\n'.join(content)
        send_mail(self.subject, content, addresses, self.from_address,)

    def get_form_fields(self):
        """
        Form page expects `form_fields` to be declared.
        If you want to change backwards relation name,
        you need to override this method.
        """

        return self.form_fields.all()

    def get_data_fields(self):
        """
        Returns a list of tuples with (field_name, field_label).
        """

        data_fields = [
            ('submit_time', _('Submission date')),
        ]
        data_fields += [
            (field.clean_name, field.label)
            for field in self.get_form_fields()
        ]

        return data_fields

    def get_form_class(self):
        fb = self.form_builder(self.get_form_fields())
        return fb.get_form_class()

    def get_form_parameters(self):
        return {}

    def get_form(self, *args, **kwargs):
        form_class = self.get_form_class()
        form_params = self.get_form_parameters()
        form_params.update(kwargs)

        return form_class(*args, **form_params)

    def get_submission_class(self):
        return FormSubmission


"""
Mixin for adding a single form to a wagtail Page model.
Allows form submission on the page.
"""
class FormPageMixin(models.Model):
    class Meta:
        abstract = True

    form = models.ForeignKey(
        'customforms.Form',
        related_name='pages',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def get_context(self, request, *args, **kwargs):
        context = super(FormPageMixin, self).get_context(request, *args, **kwargs)
        if not 'form' in context:
            context['form'] = self.handle_form(request)
        return context

    def handle_form(self, request):
        if request.method == 'POST':
            form = self.form.get_form(request.POST, request.FILES, page=self.form, user=request.user)
            if form.is_valid():
                self.form.process_form_submission(form)
                messages.add_message(request, messages.SUCCESS, 'Thank you for submitting the form.')
                return HttpResponseRedirect(request.path_info)
            else:
                messages.add_message(request, messages.ERROR, 'There was an error on the form, please correct it.')
        else:
            form = self.form.get_form(page=self.form, user=request.user)
        return form

    def serve(self, request, *args, **kwargs):
        resp = self.handle_form(request)
        if isinstance(resp, HttpResponseRedirect):
            return resp
        return super(FormPageMixin, self).serve(request, *args, **kwargs)

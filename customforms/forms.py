from django.forms.models import modelform_factory
from wagtail.admin.forms import BaseCollectionMemberForm

from .permissions import permission_policy as forms_permission_policy

class BaseFormForm(BaseCollectionMemberForm):
    permission_policy = forms_permission_policy


def get_form_form(model):
    fields = model.admin_form_fields
    if 'collection' not in fields:
        # force addition of the 'collection' field, because leaving it out can
        # cause dubious results when multiple collections exist (e.g adding the
        # document to the root collection where the user may not have permission) -
        # and when only one collection exists, it will get hidden anyway.
        fields = list(fields) + ['collection']

    return modelform_factory(
        model,
        form=BaseFormForm,
        fields=fields,
        #widgets={
        #    'tags': widgets.AdminTagWidget,
        #    'file': forms.FileInput()
        #}
    )

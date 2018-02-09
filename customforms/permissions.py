from wagtail.core.permission_policies.collections import CollectionOwnershipPermissionPolicy
from .models import Form

permission_policy = CollectionOwnershipPermissionPolicy(
    Form,
    auth_model=Form,
    owner_field_name='uploaded_by_user'
)

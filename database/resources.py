from import_export import resources
from .models import registrationcode , users
from django.core.exceptions import ValidationError


class RegistrationCodeResource(resources.ModelResource):
    class Meta:
        model = registrationcode
        fields = ('codes', 'user', 'is_used', 'used_time')
        import_id_fields = ['codes']
        skip_unchanged = True


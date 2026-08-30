from django.db import models
from .utils import get_current_tenant

class TenantAwareManager(models.Manager):
    """Manager that automatically filters querysets by the current tenant."""

    def get_queryset(self):
        qs = super().get_queryset()
        tenant = get_current_tenant()
        if tenant:
            return qs.filter(tenant=tenant)
        return qs

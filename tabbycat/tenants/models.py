from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .validators import validate_tenant_slug


class Tenant(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, max_length=63,
        validators=[validate_tenant_slug])
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    logo = models.ImageField(upload_to='tenant_logos/', blank=True, null=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    custom_domain = models.CharField(max_length=255, blank=True, null=True, unique=True,
        help_text="Optional custom domain (e.g. debate.dhaka.edu)")

    # Resource limits — set by platform admin, defaults from Plan
    max_tournaments = models.PositiveIntegerField(default=1)
    max_teams_per_tournament = models.PositiveIntegerField(default=50)
    max_adjudicators_per_tournament = models.PositiveIntegerField(default=30)
    max_users = models.PositiveIntegerField(default=5)
    max_storage_mb = models.PositiveIntegerField(default=100)

    def __str__(self):
        return self.name


class TenantMembership(models.Model):
    class Role(models.TextChoices):
        OWNER = 'owner', _('Owner')
        ADMIN = 'admin', _('Admin')
        MEMBER = 'member', _('Member')

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='tenant_memberships')
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['tenant', 'user']

from django.db import models
from django.conf import settings
from django.utils import timezone

class Plan(models.Model):
    """Fully admin-managed pricing plans. No hardcoded defaults."""
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price_bdt = models.DecimalField(max_digits=10, decimal_places=2)
    billing_period = models.CharField(max_length=10, choices=[
        ('monthly', 'Monthly'), ('yearly', 'Yearly'), ('lifetime', 'Lifetime'),
    ])
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)

    # Limits
    max_tournaments = models.PositiveIntegerField(default=1)
    max_teams_per_tournament = models.PositiveIntegerField(default=50)
    max_adjudicators_per_tournament = models.PositiveIntegerField(default=30)
    max_users = models.PositiveIntegerField(default=5)
    max_storage_mb = models.PositiveIntegerField(default=100)

    # Feature flags
    custom_domain_allowed = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    api_access = models.BooleanField(default=False)

    class Meta:
        ordering = ['display_order', 'price_bdt']

    def __str__(self):
        return f"{self.name} (৳{self.price_bdt}/{self.billing_period})"


class Subscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        PENDING = 'pending', 'Pending Payment'
        EXPIRED = 'expired', 'Expired'
        CANCELLED = 'cancelled', 'Cancelled'
        TRIAL = 'trial', 'Trial'
        SUSPENDED = 'suspended', 'Suspended'

    tenant = models.OneToOneField('tenants.Tenant', on_delete=models.CASCADE,
        related_name='subscription')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    started_at = models.DateTimeField(auto_now_add=True)
    current_period_start = models.DateTimeField(default=timezone.now)
    current_period_end = models.DateTimeField(default=timezone.now)
    trial_ends_at = models.DateTimeField(blank=True, null=True)
    auto_renew = models.BooleanField(default=False)

    def is_valid(self):
        if self.status in (self.Status.ACTIVE, self.Status.TRIAL):
            return timezone.now() <= self.current_period_end
        return False

    def __str__(self):
        return f"{self.tenant.name} - {self.plan.name} ({self.get_status_display()})"


class Payment(models.Model):
    class Method(models.TextChoices):
        BKASH_MANUAL = 'bkash_manual', 'bKash (Manual)'
        NAGAD_MANUAL = 'nagad_manual', 'Nagad (Manual)'
        ROCKET_MANUAL = 'rocket_manual', 'Rocket (Manual)'
        BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'
        SSLCOMMERZ = 'sslcommerz', 'SSLCommerz (Online)'
        FREE = 'free', 'Free Plan'

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Verification'
        VERIFIED = 'verified', 'Verified'
        REJECTED = 'rejected', 'Rejected'
        REFUNDED = 'refunded', 'Refunded'

    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE,
        related_name='payments')
    amount_bdt = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=Method.choices)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)

    # Manual payment fields (bKash/Nagad/Rocket)
    sender_phone = models.CharField(max_length=20, blank=True)
    transaction_id = models.CharField(max_length=50, blank=True)
    payment_screenshot = models.ImageField(upload_to='payment_proofs/', blank=True, null=True)

    # Online gateway fields
    gateway_transaction_id = models.CharField(max_length=100, blank=True)
    gateway_response = models.JSONField(blank=True, null=True)

    # Admin verification
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='verified_payments')
    verified_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"৳{self.amount_bdt} for {self.subscription.tenant.name} ({self.get_status_display()})"

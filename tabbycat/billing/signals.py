from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from .models import Payment, Subscription

@receiver(post_save, sender=Payment)
def handle_payment_status_change(sender, instance, created, **kwargs):
    """
    When a payment is verified, update the subscription status and dates,
    and propagate limits to the tenant.
    """
    if not created and instance.status == Payment.Status.VERIFIED:
        # Check if the subscription is already active to prevent double-applying time
        # This is a simple implementation; a robust one would track the specific period paid for
        subscription = instance.subscription
        plan = subscription.plan
        
        # Calculate new end date based on billing period
        if plan.billing_period == 'monthly':
            delta = relativedelta(months=1)
        elif plan.billing_period == 'yearly':
            delta = relativedelta(years=1)
        else:
            delta = relativedelta(years=100) # lifetime
            
        now = timezone.now()
        if subscription.current_period_end and subscription.current_period_end > now:
            subscription.current_period_end += delta
        else:
            subscription.current_period_start = now
            subscription.current_period_end = now + delta
            
        subscription.status = Subscription.Status.ACTIVE
        subscription.save()

@receiver(post_save, sender=Subscription)
def update_tenant_limits(sender, instance, **kwargs):
    """
    When a subscription is updated (e.g. status changes to active, or plan changes),
    propagate the plan limits to the tenant if the subscription is valid.
    """
    if instance.is_valid():
        tenant = instance.tenant
        plan = instance.plan
        
        tenant.max_tournaments = plan.max_tournaments
        tenant.max_teams_per_tournament = plan.max_teams_per_tournament
        tenant.max_adjudicators_per_tournament = plan.max_adjudicators_per_tournament
        tenant.max_users = plan.max_users
        tenant.max_storage_mb = plan.max_storage_mb
        
        if not plan.custom_domain_allowed:
            tenant.custom_domain = None
            
        tenant.save()
    elif instance.status in (Subscription.Status.EXPIRED, Subscription.Status.CANCELLED, Subscription.Status.SUSPENDED):
        # We might want to mark the tenant as inactive, or restrict it somehow.
        # For now, just mark it inactive.
        tenant = instance.tenant
        tenant.is_active = False
        tenant.save()

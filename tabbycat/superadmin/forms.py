from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from tenants.models import Tenant, TenantMembership
from billing.models import Plan, Subscription, Payment

User = get_user_model()


class TenantForm(forms.ModelForm):
    class Meta:
        model = Tenant
        fields = [
            'name', 'slug', 'owner', 'custom_domain', 'is_active',
            'contact_email', 'contact_phone',
            'max_tournaments', 'max_teams_per_tournament',
            'max_adjudicators_per_tournament', 'max_users', 'max_storage_mb'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Dhaka University Debating Club'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. dudc'}),
            'owner': forms.Select(attrs={'class': 'form-control custom-select'}),
            'custom_domain': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. debate.dhaka.edu (optional)'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'custom-control-input'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'contact@club.org'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+8801700000000'}),
            'max_tournaments': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_teams_per_tournament': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_adjudicators_per_tournament': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_users': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_storage_mb': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = [
            'name', 'slug', 'description', 'price_bdt', 'billing_period',
            'is_active', 'is_featured', 'display_order',
            'max_tournaments', 'max_teams_per_tournament',
            'max_adjudicators_per_tournament', 'max_users', 'max_storage_mb',
            'custom_domain_allowed', 'priority_support', 'api_access'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Premium Tournament'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. premium'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Short summary of the plan...'}),
            'price_bdt': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'billing_period': forms.Select(attrs={'class': 'form-control custom-select'}),
            'display_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'custom-control-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'custom-control-input'}),
            'max_tournaments': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_teams_per_tournament': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_adjudicators_per_tournament': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_users': forms.NumberInput(attrs={'class': 'form-control'}),
            'max_storage_mb': forms.NumberInput(attrs={'class': 'form-control'}),
            'custom_domain_allowed': forms.CheckboxInput(attrs={'class': 'custom-control-input'}),
            'priority_support': forms.CheckboxInput(attrs={'class': 'custom-control-input'}),
            'api_access': forms.CheckboxInput(attrs={'class': 'custom-control-input'}),
        }


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['plan', 'status', 'current_period_start', 'current_period_end', 'trial_ends_at', 'auto_renew']
        widgets = {
            'plan': forms.Select(attrs={'class': 'form-control custom-select'}),
            'status': forms.Select(attrs={'class': 'form-control custom-select'}),
            'current_period_start': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'current_period_end': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'trial_ends_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'auto_renew': forms.CheckboxInput(attrs={'class': 'custom-control-input'}),
        }


class PaymentVerifyForm(forms.Form):
    admin_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional verification notes...'})
    )


class PaymentRejectForm(forms.Form):
    rejection_reason = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Reason for rejection (e.g. Invalid Transaction ID)...'})
    )
    admin_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional internal admin notes...'})
    )

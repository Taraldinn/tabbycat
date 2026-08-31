from django import forms
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from tenants.models import Tenant
from tenants.validators import validate_tenant_slug
from billing.models import Plan
from .models import UserProfile

User = get_user_model()


COMMON_TIMEZONES = [
    ('Asia/Dhaka', 'Asia/Dhaka (GMT+6:00)'),
    ('Asia/Kolkata', 'Asia/Kolkata (GMT+5:30)'),
    ('Asia/Bangkok', 'Asia/Bangkok (GMT+7:00)'),
    ('Asia/Singapore', 'Asia/Singapore (GMT+8:00)'),
    ('Asia/Kuala_Lumpur', 'Asia/Kuala Lumpur (GMT+8:00)'),
    ('Asia/Hong_Kong', 'Asia/Hong Kong (GMT+8:00)'),
    ('Asia/Tokyo', 'Asia/Tokyo (GMT+9:00)'),
    ('Asia/Seoul', 'Asia/Seoul (GMT+9:00)'),
    ('Asia/Dubai', 'Asia/Dubai (GMT+4:00)'),
    ('Europe/London', 'Europe/London (GMT+0 / GMT+1)'),
    ('Europe/Paris', 'Europe/Paris (GMT+1 / GMT+2)'),
    ('Europe/Berlin', 'Europe/Berlin (GMT+1 / GMT+2)'),
    ('America/New_York', 'America/New York (Eastern Time)'),
    ('America/Chicago', 'America/Chicago (Central Time)'),
    ('America/Denver', 'America/Denver (Mountain Time)'),
    ('America/Los_Angeles', 'America/Los Angeles (Pacific Time)'),
    ('Australia/Sydney', 'Australia/Sydney (AEST)'),
    ('Australia/Melbourne', 'Australia/Melbourne (AEST)'),
    ('Australia/Perth', 'Australia/Perth (AWST)'),
    ('Pacific/Auckland', 'Pacific/Auckland (NZST)'),
    ('UTC', 'UTC (Coordinated Universal Time)'),
]


class UserRegistrationWithTenantForm(forms.Form):
    # Account details
    first_name = forms.CharField(
        label=_("First Name"),
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Abrar'})
    )
    last_name = forms.CharField(
        label=_("Last Name"),
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Hasan'})
    )
    username = forms.CharField(
        label=_("Username"),
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. abrar_hasan'})
    )
    email = forms.EmailField(
        label=_("Email Address"),
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'abrar@example.com'})
    )
    phone = forms.CharField(
        label=_("Phone Number"),
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '01XXXXXXXXX'})
    )
    password = forms.CharField(
        label=_("Password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'At least 8 characters'}),
        min_length=8
    )
    confirm_password = forms.CharField(
        label=_("Confirm Password"),
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Re-enter your password'})
    )

    # Tenant details
    organization_name = forms.CharField(
        label=_("Club / Organization Name"),
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. North South Debating Club'})
    )
    subdomain_slug = forms.SlugField(
        label=_("Desired Subdomain"),
        max_length=63,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g. nsdc',
            'id': 'id_subdomain_slug',
            'pattern': '^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$',
            'title': 'Lowercase letters, numbers, and hyphens only'
        })
    )

    # Selected plan
    plan = forms.ModelChoiceField(
        queryset=Plan.objects.filter(is_active=True).order_by('display_order', 'price_bdt'),
        required=True,
        empty_label=None,
        widget=forms.RadioSelect(attrs={'class': 'custom-control-input'})
    )

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError(_("This username is already taken. Please choose another."))
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(_("An account with this email address already exists. Please log in."))
        return email

    def clean_subdomain_slug(self):
        slug = self.cleaned_data.get('subdomain_slug', '').strip().lower()
        validate_tenant_slug(slug)
        if Tenant.objects.filter(slug__iexact=slug).exists():
            raise ValidationError(_("Subdomain '%(slug)s' is already taken. Please choose a different one.") % {'slug': slug})
        return slug

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            self.add_error('confirm_password', _("Passwords do not match."))

        return cleaned_data


class UserProfileUpdateForm(forms.Form):
    first_name = forms.CharField(
        label=_("First Name"),
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'tc-search-input', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        label=_("Last Name"),
        max_length=30,
        required=False,
        widget=forms.TextInput(attrs={'class': 'tc-search-input', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        label=_("Email Address"),
        required=True,
        widget=forms.EmailInput(attrs={'class': 'tc-search-input', 'placeholder': 'Email Address'})
    )
    phone = forms.CharField(
        label=_("Phone Number"),
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'tc-search-input', 'placeholder': '01XXXXXXXXX'})
    )
    timezone = forms.ChoiceField(
        label=_("Preferred Timezone"),
        choices=COMMON_TIMEZONES,
        required=True,
        widget=forms.Select(attrs={'class': 'form-select custom-select tc-search-input'})
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        profile, created = UserProfile.objects.get_or_create(user=user)
        self.fields['first_name'].initial = user.first_name
        self.fields['last_name'].initial = user.last_name
        self.fields['email'].initial = user.email
        self.fields['phone'].initial = profile.phone
        self.fields['timezone'].initial = profile.timezone or 'Asia/Dhaka'

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise ValidationError(_("This email is already in use by another user."))
        return email

    def save(self):
        data = self.cleaned_data
        self.user.first_name = data.get('first_name', '')
        self.user.last_name = data.get('last_name', '')
        self.user.email = data.get('email', '')
        self.user.save()

        profile, created = UserProfile.objects.get_or_create(user=self.user)
        profile.phone = data.get('phone', '')
        profile.timezone = data.get('timezone', 'Asia/Dhaka')
        profile.save()
        return self.user

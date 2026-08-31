from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, FormView, TemplateView

from billing.models import Plan, Subscription
from tenants.models import Tenant, TenantMembership
from .forms import UserRegistrationWithTenantForm
from .models import UserProfile

User = get_user_model()


class RegisterTenantView(FormView):
    template_name = 'accounts/register.html'
    form_class = UserRegistrationWithTenantForm
    success_url = reverse_lazy('accounts:onboarding-success')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['plans'] = Plan.objects.filter(is_active=True).order_by('display_order', 'price_bdt')
        context['base_domain'] = getattr(settings, 'TABBYCAT_BASE_DOMAIN', 'tabbycatbd.com')
        # Preselect plan if query param provided
        plan_slug = self.request.GET.get('plan')
        if plan_slug:
            plan = Plan.objects.filter(slug=plan_slug, is_active=True).first()
            if plan:
                context['preselected_plan_id'] = plan.id
        return context

    def form_valid(self, form):
        data = form.cleaned_data
        selected_plan = data['plan']

        try:
            with transaction.atomic():
                # 1. Create User
                user = User.objects.create_user(
                    username=data['username'],
                    email=data['email'],
                    password=data['password'],
                    first_name=data['first_name'],
                    last_name=data['last_name']
                )

                # 2. Update Profile with phone
                profile, created = UserProfile.objects.get_or_create(user=user)
                profile.phone = data['phone']
                profile.save()

                # 3. Create Tenant
                is_free_plan = (selected_plan.price_bdt == 0)
                tenant = Tenant.objects.create(
                    name=data['organization_name'],
                    slug=data['subdomain_slug'],
                    owner=user,
                    contact_email=data['email'],
                    contact_phone=data['phone'],
                    is_active=is_free_plan,  # Activated immediately if free
                    max_tournaments=selected_plan.max_tournaments,
                    max_teams_per_tournament=selected_plan.max_teams_per_tournament,
                    max_adjudicators_per_tournament=selected_plan.max_adjudicators_per_tournament,
                    max_users=selected_plan.max_users,
                    max_storage_mb=selected_plan.max_storage_mb,
                )

                # 4. Create Owner Membership
                TenantMembership.objects.create(
                    tenant=tenant,
                    user=user,
                    role=TenantMembership.Role.OWNER
                )

                # 5. Create Subscription
                now = timezone.now()
                if is_free_plan:
                    sub = Subscription.objects.create(
                        tenant=tenant,
                        plan=selected_plan,
                        status=Subscription.Status.ACTIVE,
                        started_at=now,
                        current_period_start=now,
                        current_period_end=now + timedelta(days=36500) # lifetime free
                    )
                else:
                    sub = Subscription.objects.create(
                        tenant=tenant,
                        plan=selected_plan,
                        status=Subscription.Status.PENDING,
                        started_at=now,
                        current_period_start=now,
                        current_period_end=now
                    )

            # Auto-login newly registered user
            login(self.request, user)
            self.request.session['onboarding_tenant_id'] = tenant.id

            if is_free_plan:
                messages.success(self.request, _("Congratulations! Your portal '%s' is ready.") % tenant.name)
                return redirect('accounts:onboarding-success')
            else:
                messages.info(self.request, _("Please complete the payment to activate your '%s' plan.") % selected_plan.name)
                return redirect('billing:checkout', subscription_id=sub.id)

        except Exception as e:
            form.add_error(None, _("An unexpected error occurred during account creation: %s") % str(e))
            return self.form_invalid(form)


class TenantOnboardingSuccessView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/onboarding_success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant_id = self.request.session.get('onboarding_tenant_id')
        tenant = None
        if tenant_id:
            tenant = Tenant.objects.filter(id=tenant_id, owner=self.request.user).first()
        if not tenant:
            tenant = Tenant.objects.filter(owner=self.request.user).order_by('-created_at').first()

        context['tenant'] = tenant
        context['base_domain'] = getattr(settings, 'TABBYCAT_BASE_DOMAIN', 'tabbycatbd.com')
        return context


class ClientDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/client_dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Fetch active tenant
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            tenant = Tenant.objects.filter(owner=user).first()
        if not tenant:
            membership = TenantMembership.objects.filter(user=user).select_related('tenant').first()
            if membership:
                tenant = membership.tenant

        context['tenant'] = tenant
        context['base_domain'] = getattr(settings, 'TABBYCAT_BASE_DOMAIN', 'tabbycatbd.com')

        if tenant:
            tournaments = tenant.tournament_set.all().order_by('-id')
            subscription = getattr(tenant, 'subscription', None)
            plan = subscription.plan if subscription else None

            context['tournaments'] = tournaments
            context['tournaments_count'] = tournaments.count()
            context['active_tournaments_count'] = tournaments.filter(active=True).count()
            context['subscription'] = subscription
            context['plan'] = plan
            context['max_tournaments'] = tenant.max_tournaments
            context['max_teams'] = tenant.max_teams_per_tournament
            context['max_adjudicators'] = tenant.max_adjudicators_per_tournament
            context['max_users'] = tenant.max_users
            context['max_storage_mb'] = tenant.max_storage_mb
        else:
            context['tournaments'] = []
            context['tournaments_count'] = 0
            context['active_tournaments_count'] = 0

        return context


class UserProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        profile, _ = UserProfile.objects.get_or_create(user=user)
        memberships = TenantMembership.objects.filter(user=user).select_related('tenant')

        context['user_profile'] = profile
        context['memberships'] = memberships
        return context


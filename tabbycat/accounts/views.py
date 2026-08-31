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
from django.views import View
from django.views.generic import DetailView, FormView, TemplateView

from billing.models import Payment, Plan, Subscription
from tenants.models import Tenant, TenantMembership
from .forms import TenantDomainForm, TenantManagerAddForm, UserProfileUpdateForm, UserRegistrationWithTenantForm
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

    def get_active_tenant(self):
        user = self.request.user
        tenant = getattr(self.request, 'tenant', None)
        if not tenant:
            tenant = Tenant.objects.filter(owner=user).first()
        if not tenant:
            membership = TenantMembership.objects.filter(user=user).select_related('tenant').first()
            if membership:
                tenant = membership.tenant
        if not tenant and user.is_authenticated:
            import re
            base_slug = re.sub(r'[^a-z0-9-]', '', user.username.lower())[:30] or 'club'
            slug = base_slug
            counter = 1
            while Tenant.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            starter_plan = Plan.objects.filter(price_bdt=0, is_active=True).first()
            tenant = Tenant.objects.create(
                name=f"{user.first_name or user.username}'s Organization",
                slug=slug,
                owner=user,
                is_active=True,
                max_tournaments=starter_plan.max_tournaments if starter_plan else 1,
                max_teams_per_tournament=starter_plan.max_teams_per_tournament if starter_plan else 50,
                max_adjudicators_per_tournament=starter_plan.max_adjudicators_per_tournament if starter_plan else 30,
            )
            TenantMembership.objects.create(
                tenant=tenant,
                user=user,
                role=TenantMembership.Role.OWNER
            )
            if starter_plan:
                now = timezone.now()
                Subscription.objects.create(
                    tenant=tenant,
                    plan=starter_plan,
                    status=Subscription.Status.ACTIVE,
                    started_at=now,
                    current_period_start=now,
                    current_period_end=now + timedelta(days=36500)
                )
        return tenant

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.get_active_tenant()

        context['tenant'] = tenant
        context['base_domain'] = getattr(settings, 'TABBYCAT_BASE_DOMAIN', 'tabbycatbd.com')
        context['all_plans'] = Plan.objects.filter(is_active=True).order_by('display_order', 'price_bdt')

        if tenant:
            tournaments = tenant.tournament_set.all().order_by('-id')
            subscription = getattr(tenant, 'subscription', None)
            plan = subscription.plan if subscription else None
            payments = subscription.payments.all().order_by('-created_at') if subscription else []
            memberships = tenant.memberships.select_related('user').order_by('role', 'joined_at')

            context['tournaments'] = tournaments
            context['tournaments_count'] = tournaments.count()
            context['active_tournaments_count'] = tournaments.filter(active=True).count()
            context['subscription'] = subscription
            context['plan'] = plan
            context['payments'] = payments
            context['pending_payments'] = [p for p in payments if p.status == Payment.Status.PENDING]
            context['memberships'] = memberships
            context['domain_form'] = TenantDomainForm(tenant=tenant)
            context['manager_form'] = TenantManagerAddForm(tenant=tenant)
            context['max_tournaments'] = tenant.max_tournaments
            context['max_teams'] = tenant.max_teams_per_tournament
            context['max_adjudicators'] = tenant.max_adjudicators_per_tournament
            context['max_users'] = tenant.max_users
            context['max_storage_mb'] = tenant.max_storage_mb
        else:
            context['tournaments'] = []
            context['tournaments_count'] = 0
            context['active_tournaments_count'] = 0
            context['subscription'] = None
            context['plan'] = None
            context['payments'] = []
            context['pending_payments'] = []
            context['memberships'] = []
            context['domain_form'] = None
            context['manager_form'] = None

        return context

    def post(self, request, *args, **kwargs):
        tenant = self.get_active_tenant()
        if not tenant:
            messages.error(request, _("No organization found."))
            return redirect('accounts:dashboard')

        action = request.POST.get('action')

        # 1. Custom Domain Action
        if action == 'update_domain':
            form = TenantDomainForm(tenant, data=request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, _("Custom domain updated successfully! Please ensure your DNS CNAME points to %s.") % getattr(settings, 'TABBYCAT_BASE_DOMAIN', 'tabbycatbd.com'))
            else:
                for err in form.errors.values():
                    messages.error(request, err.as_text())
            return redirect('accounts:dashboard')

        # 2. Add Site Manager Action
        elif action == 'add_manager':
            form = TenantManagerAddForm(tenant, data=request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, _("New manager added to '%s' successfully.") % tenant.name)
            else:
                for err in form.errors.values():
                    messages.error(request, err.as_text())
            return redirect('accounts:dashboard')

        # 3. Upgrade / Renewal Action (default)
        new_plan_id = request.POST.get('new_plan_id')
        if not new_plan_id:
            messages.error(request, _("Please select a valid plan."))
            return redirect('accounts:dashboard')

        plan = get_object_or_404(Plan, id=new_plan_id, is_active=True)
        sub = getattr(tenant, 'subscription', None)
        now = timezone.now()

        if sub:
            sub.plan = plan
            sub.status = Subscription.Status.PENDING
            sub.save()
        else:
            sub = Subscription.objects.create(
                tenant=tenant,
                plan=plan,
                status=Subscription.Status.PENDING,
                started_at=now,
                current_period_start=now,
                current_period_end=now
            )

        messages.info(request, _("Plan '%s' selected! Please complete the verification payment.") % plan.name)
        return redirect('billing:checkout', subscription_id=sub.id)


class UserProfileView(LoginRequiredMixin, View):
    template_name = 'accounts/profile.html'

    def get(self, request, *args, **kwargs):
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)
        form = UserProfileUpdateForm(user=user)
        memberships = TenantMembership.objects.filter(user=user).select_related('tenant')

        return render(request, self.template_name, {
            'user_profile': profile,
            'form': form,
            'memberships': memberships,
            'current_timezone': profile.timezone or 'Asia/Dhaka',
        })

    def post(self, request, *args, **kwargs):
        user = request.user
        profile, created = UserProfile.objects.get_or_create(user=user)
        form = UserProfileUpdateForm(user=user, data=request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, _("Your profile and timezone preferences have been updated successfully!"))
            return redirect('accounts:profile')
        else:
            memberships = TenantMembership.objects.filter(user=user).select_related('tenant')
            messages.error(request, _("Please correct the errors below."))
            return render(request, self.template_name, {
                'user_profile': profile,
                'form': form,
                'memberships': memberships,
                'current_timezone': profile.timezone or 'Asia/Dhaka',
            })

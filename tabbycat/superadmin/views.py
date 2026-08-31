from datetime import timedelta
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, TemplateView, UpdateView

from billing.models import Payment, Plan, Subscription
from tenants.models import Tenant, TenantMembership
from tournaments.models import Tournament

from .forms import PaymentRejectForm, PaymentVerifyForm, PlanForm, SubscriptionForm, TenantForm
from .mixins import SuperAdminRequiredMixin

User = get_user_model()


# ==============================================================================
# Dashboard
# ==============================================================================

class SuperAdminDashboardView(SuperAdminRequiredMixin, TemplateView):
    template_name = 'superadmin/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        # KPIs
        context['total_tenants'] = Tenant.objects.count()
        context['active_tenants'] = Tenant.objects.filter(is_active=True).count()
        context['total_tournaments'] = Tournament.objects.count()
        context['active_tournaments'] = Tournament.objects.filter(active=True).count()
        context['total_users'] = User.objects.count()
        
        # Financial KPIs
        total_rev = Payment.objects.filter(status=Payment.Status.VERIFIED).aggregate(t=Sum('amount_bdt'))['t'] or 0
        month_rev = Payment.objects.filter(
            status=Payment.Status.VERIFIED, created_at__gte=thirty_days_ago
        ).aggregate(t=Sum('amount_bdt'))['t'] or 0
        context['total_revenue'] = total_rev
        context['month_revenue'] = month_rev

        # Subscriptions
        context['active_subscriptions'] = Subscription.objects.filter(status=Subscription.Status.ACTIVE).count()
        context['pending_subscriptions'] = Subscription.objects.filter(status=Subscription.Status.PENDING).count()

        # Queues
        context['pending_payments'] = Payment.objects.filter(
            status=Payment.Status.PENDING
        ).select_related('subscription__tenant', 'subscription__plan').order_by('-created_at')[:8]
        context['pending_payments_count'] = Payment.objects.filter(status=Payment.Status.PENDING).count()

        # Recent activities
        context['recent_tenants'] = Tenant.objects.select_related('owner').order_by('-created_at')[:6]
        context['recent_tournaments'] = Tournament.objects.select_related('tenant').order_by('-id')[:6]
        context['plans_count'] = Plan.objects.count()

        return context


# ==============================================================================
# Tenants Management
# ==============================================================================

class TenantListView(SuperAdminRequiredMixin, ListView):
    model = Tenant
    template_name = 'superadmin/tenants/list.html'
    context_object_name = 'tenants'
    paginate_by = 25

    def get_queryset(self):
        qs = Tenant.objects.select_related('owner').annotate(
            tournament_count=Count('tournament', distinct=True),
            member_count=Count('memberships', distinct=True),
        ).order_by('-created_at')

        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(slug__icontains=q) |
                Q(custom_domain__icontains=q) |
                Q(owner__username__icontains=q) |
                Q(owner__email__icontains=q)
            )

        status_filter = self.request.GET.get('status')
        if status_filter == 'active':
            qs = qs.filter(is_active=True)
        elif status_filter == 'inactive':
            qs = qs.filter(is_active=False)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['status_filter'] = self.request.GET.get('status', '')
        return context


class TenantDetailView(SuperAdminRequiredMixin, DetailView):
    model = Tenant
    template_name = 'superadmin/tenants/detail.html'
    context_object_name = 'tenant'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tenant = self.object
        context['tournaments'] = tenant.tournament_set.all().order_by('-id')
        context['memberships'] = tenant.memberships.select_related('user').order_by('-joined_at')
        context['subscription'] = getattr(tenant, 'subscription', None)
        context['payments'] = Payment.objects.filter(subscription__tenant=tenant).order_by('-created_at')[:10]
        
        # Usage stats vs limits
        context['tournaments_used'] = tenant.tournament_set.count()
        context['users_used'] = tenant.memberships.count()
        return context


class TenantCreateView(SuperAdminRequiredMixin, CreateView):
    model = Tenant
    form_class = TenantForm
    template_name = 'superadmin/tenants/form.html'
    success_url = reverse_lazy('superadmin:tenant-list')

    def form_valid(self, form):
        response = super().form_valid(form)
        # Create default membership for owner
        TenantMembership.objects.get_or_create(
            tenant=self.object,
            user=self.object.owner,
            defaults={'role': TenantMembership.Role.OWNER}
        )
        messages.success(self.request, _("Tenant '%s' created successfully.") % self.object.name)
        return response


class TenantUpdateView(SuperAdminRequiredMixin, UpdateView):
    model = Tenant
    form_class = TenantForm
    template_name = 'superadmin/tenants/form.html'

    def get_success_url(self):
        return reverse('superadmin:tenant-detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, _("Tenant '%s' updated successfully.") % form.instance.name)
        return super().form_valid(form)


class TenantToggleActiveView(SuperAdminRequiredMixin, View):
    def post(self, request, pk):
        tenant = get_object_or_404(Tenant, pk=pk)
        tenant.is_active = not tenant.is_active
        tenant.save(update_fields=['is_active'])
        status_text = _("activated") if tenant.is_active else _("deactivated")
        messages.info(request, _("Tenant '%(name)s' has been %(status)s.") % {'name': tenant.name, 'status': status_text})
        return redirect(request.META.get('HTTP_REFERER', reverse('superadmin:tenant-list')))


# ==============================================================================
# Plans Management
# ==============================================================================

class PlanListView(SuperAdminRequiredMixin, ListView):
    model = Plan
    template_name = 'superadmin/plans/list.html'
    context_object_name = 'plans'

    def get_queryset(self):
        return Plan.objects.annotate(
            sub_count=Count('subscription')
        ).order_by('display_order', 'price_bdt')


class PlanCreateView(SuperAdminRequiredMixin, CreateView):
    model = Plan
    form_class = PlanForm
    template_name = 'superadmin/plans/form.html'
    success_url = reverse_lazy('superadmin:plan-list')

    def form_valid(self, form):
        messages.success(self.request, _("Plan '%s' created successfully.") % form.instance.name)
        return super().form_valid(form)


class PlanUpdateView(SuperAdminRequiredMixin, UpdateView):
    model = Plan
    form_class = PlanForm
    template_name = 'superadmin/plans/form.html'
    success_url = reverse_lazy('superadmin:plan-list')

    def form_valid(self, form):
        messages.success(self.request, _("Plan '%s' updated successfully.") % form.instance.name)
        return super().form_valid(form)


class PlanDeleteView(SuperAdminRequiredMixin, DeleteView):
    model = Plan
    template_name = 'superadmin/plans/confirm_delete.html'
    success_url = reverse_lazy('superadmin:plan-list')

    def delete(self, request, *args, **kwargs):
        plan = self.get_object()
        if plan.subscription_set.exists():
            messages.error(request, _("Cannot delete plan '%s' because active subscriptions are assigned to it.") % plan.name)
            return redirect('superadmin:plan-list')
        messages.success(request, _("Plan '%s' deleted.") % plan.name)
        return super().delete(request, *args, **kwargs)


# ==============================================================================
# Subscriptions Management
# ==============================================================================

class SubscriptionListView(SuperAdminRequiredMixin, ListView):
    model = Subscription
    template_name = 'superadmin/subscriptions/list.html'
    context_object_name = 'subscriptions'
    paginate_by = 25

    def get_queryset(self):
        qs = Subscription.objects.select_related('tenant', 'plan').order_by('-started_at')
        status_filter = self.request.GET.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(tenant__name__icontains=q) |
                Q(tenant__slug__icontains=q) |
                Q(plan__name__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['query'] = self.request.GET.get('q', '')
        context['status_choices'] = Subscription.Status.choices
        return context


class SubscriptionUpdateView(SuperAdminRequiredMixin, UpdateView):
    model = Subscription
    form_class = SubscriptionForm
    template_name = 'superadmin/subscriptions/form.html'
    success_url = reverse_lazy('superadmin:subscription-list')

    def form_valid(self, form):
        # Sync limits from Plan to Tenant if status active
        sub = form.save()
        if sub.status == Subscription.Status.ACTIVE:
            tenant = sub.tenant
            plan = sub.plan
            tenant.max_tournaments = plan.max_tournaments
            tenant.max_teams_per_tournament = plan.max_teams_per_tournament
            tenant.max_adjudicators_per_tournament = plan.max_adjudicators_per_tournament
            tenant.max_users = plan.max_users
            tenant.max_storage_mb = plan.max_storage_mb
            tenant.save()
        messages.success(self.request, _("Subscription for '%s' updated.") % sub.tenant.name)
        return super().form_valid(form)


# ==============================================================================
# Payments & Verification Hub
# ==============================================================================

class PaymentListView(SuperAdminRequiredMixin, ListView):
    model = Payment
    template_name = 'superadmin/payments/list.html'
    context_object_name = 'payments'
    paginate_by = 25

    def get_queryset(self):
        qs = Payment.objects.select_related(
            'subscription__tenant', 'subscription__plan', 'verified_by'
        ).order_by('-created_at')

        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)

        method = self.request.GET.get('method')
        if method:
            qs = qs.filter(method=method)

        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(subscription__tenant__name__icontains=q) |
                Q(transaction_id__icontains=q) |
                Q(sender_phone__icontains=q)
            )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_filter'] = self.request.GET.get('status', '')
        context['method_filter'] = self.request.GET.get('method', '')
        context['query'] = self.request.GET.get('q', '')
        context['pending_count'] = Payment.objects.filter(status=Payment.Status.PENDING).count()
        context['status_choices'] = Payment.Status.choices
        context['method_choices'] = Payment.Method.choices
        return context


class PaymentDetailView(SuperAdminRequiredMixin, DetailView):
    model = Payment
    template_name = 'superadmin/payments/detail.html'
    context_object_name = 'payment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['verify_form'] = PaymentVerifyForm()
        context['reject_form'] = PaymentRejectForm()
        return context


class PaymentVerifyView(SuperAdminRequiredMixin, View):
    def post(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk)
        admin_notes = request.POST.get('admin_notes', '').strip()

        payment.status = Payment.Status.VERIFIED
        payment.verified_by = request.user
        payment.verified_at = timezone.now()
        if admin_notes:
            payment.admin_notes = admin_notes
        payment.save()

        # Automatically activate / extend the tenant's subscription
        sub = payment.subscription
        sub.status = Subscription.Status.ACTIVE
        sub.current_period_start = timezone.now()
        
        # Calculate extension based on plan billing period
        plan = sub.plan
        if plan.billing_period == 'yearly':
            sub.current_period_end = timezone.now() + timedelta(days=365)
        elif plan.billing_period == 'lifetime':
            sub.current_period_end = timezone.now() + timedelta(days=36500)
        else: # monthly default
            sub.current_period_end = timezone.now() + timedelta(days=30)
        sub.save()

        # Update tenant limits to match plan
        tenant = sub.tenant
        tenant.max_tournaments = plan.max_tournaments
        tenant.max_teams_per_tournament = plan.max_teams_per_tournament
        tenant.max_adjudicators_per_tournament = plan.max_adjudicators_per_tournament
        tenant.max_users = plan.max_users
        tenant.max_storage_mb = plan.max_storage_mb
        tenant.is_active = True
        tenant.save()

        messages.success(request, _("Payment of ৳%(amt)s for %(tenant)s verified successfully! Subscription activated until %(date)s.") % {
            'amt': payment.amount_bdt,
            'tenant': tenant.name,
            'date': sub.current_period_end.strftime('%b %d, %Y')
        })
        return redirect(request.META.get('HTTP_REFERER', reverse('superadmin:payment-list')))


class PaymentRejectView(SuperAdminRequiredMixin, View):
    def post(self, request, pk):
        payment = get_object_or_404(Payment, pk=pk)
        rejection_reason = request.POST.get('rejection_reason', '').strip()
        admin_notes = request.POST.get('admin_notes', '').strip()

        payment.status = Payment.Status.REJECTED
        payment.verified_by = request.user
        payment.verified_at = timezone.now()
        payment.rejection_reason = rejection_reason or _("Payment details could not be verified.")
        if admin_notes:
            payment.admin_notes = admin_notes
        payment.save()

        messages.warning(request, _("Payment of ৳%(amt)s for %(tenant)s marked as rejected.") % {
            'amt': payment.amount_bdt,
            'tenant': payment.subscription.tenant.name
        })
        return redirect(request.META.get('HTTP_REFERER', reverse('superadmin:payment-list')))


# ==============================================================================
# Global Directories: Tournaments & Users
# ==============================================================================

class GlobalTournamentListView(SuperAdminRequiredMixin, ListView):
    model = Tournament
    template_name = 'superadmin/tournaments/list.html'
    context_object_name = 'tournaments'
    paginate_by = 25

    def get_queryset(self):
        qs = Tournament.objects.select_related('tenant').annotate(
            team_count=Count('team', distinct=True),
            adj_count=Count('adjudicator', distinct=True),
            round_count=Count('round', distinct=True)
        ).order_by('-id')

        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(name__icontains=q) |
                Q(slug__icontains=q) |
                Q(tenant__name__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context


class GlobalUserListView(SuperAdminRequiredMixin, ListView):
    model = User
    template_name = 'superadmin/users/list.html'
    context_object_name = 'users'
    paginate_by = 25

    def get_queryset(self):
        qs = User.objects.prefetch_related('tenant_memberships__tenant').order_by('-date_joined')
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(
                Q(username__icontains=q) |
                Q(email__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context


class UserSendPasswordResetView(SuperAdminRequiredMixin, View):
    def post(self, request, pk):
        target_user = get_object_or_404(User, pk=pk)
        if not target_user.email:
            messages.error(request, _("User '%s' does not have an email address configured.") % target_user.username)
            return redirect(request.META.get('HTTP_REFERER', reverse('superadmin:user-list')))

        from django.contrib.auth.forms import PasswordResetForm
        form = PasswordResetForm({'email': target_user.email})
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@tabbycatbd.com'),
                email_template_name='registration/password_reset_email.html',
                subject_template_name='registration/password_reset_subject.txt',
            )
            messages.success(request, _("Password reset email sent to '%(email)s' for user %(username)s.") % {
                'email': target_user.email,
                'username': target_user.username
            })
        else:
            messages.error(request, _("Could not generate password reset for user '%s'.") % target_user.username)

        return redirect(request.META.get('HTTP_REFERER', reverse('superadmin:user-list')))


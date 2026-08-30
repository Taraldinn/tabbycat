from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView, DetailView, TemplateView

from .forms import ManualPaymentForm
from .models import Payment, Subscription


class PaymentCheckoutView(LoginRequiredMixin, CreateView):
    model = Payment
    form_class = ManualPaymentForm
    template_name = 'billing/checkout.html'

    def get_subscription(self):
        subscription_id = self.kwargs.get('subscription_id')
        return get_object_or_404(
            Subscription.objects.select_related('tenant', 'plan'),
            id=subscription_id,
            tenant__owner=self.request.user
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sub = self.get_subscription()
        context['subscription'] = sub
        context['tenant'] = sub.tenant
        context['plan'] = sub.plan
        context['bkash_number'] = getattr(settings, 'BKASH_PAYMENT_NUMBER', '01712-345678')
        context['nagad_number'] = getattr(settings, 'NAGAD_PAYMENT_NUMBER', '01812-345678')
        context['rocket_number'] = getattr(settings, 'ROCKET_PAYMENT_NUMBER', '01912-345678')
        return context

    def form_valid(self, form):
        sub = self.get_subscription()
        payment = form.save(commit=False)
        payment.subscription = sub
        payment.amount_bdt = sub.plan.price_bdt
        payment.status = Payment.Status.PENDING
        payment.save()

        messages.success(
            self.request,
            _("Payment details submitted successfully! Our administrators will verify your transaction shortly.")
        )
        return redirect('billing:status', subscription_id=sub.id)


class PaymentStatusView(LoginRequiredMixin, DetailView):
    model = Subscription
    template_name = 'billing/status.html'
    context_object_name = 'subscription'
    pk_url_kwarg = 'subscription_id'

    def get_queryset(self):
        return Subscription.objects.select_related('tenant', 'plan').filter(tenant__owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sub = self.object
        context['tenant'] = sub.tenant
        context['payments'] = sub.payments.all().order_by('-created_at')
        context['base_domain'] = getattr(settings, 'TABBYCAT_BASE_DOMAIN', 'tabbycatbd.com')
        return context

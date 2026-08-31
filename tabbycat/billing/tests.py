from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from billing.models import Payment, Plan, Subscription
from tenants.models import Tenant, TenantMembership

User = get_user_model()


class BillingWorkflowTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='billing_user',
            email='billing@example.com',
            password='TestPassword123!'
        )
        self.plan = Plan.objects.create(
            name="Inter Tournament",
            slug="inter-tournament",
            price_bdt=1500,
            billing_period="monthly",
            max_tournaments=3,
            max_teams_per_tournament=50,
            max_adjudicators_per_tournament=30,
            max_users=5,
            max_storage_mb=150
        )
        self.tenant = Tenant.objects.create(
            name="DU Debating Society",
            slug="duds",
            owner=self.user,
            is_active=False
        )
        TenantMembership.objects.create(tenant=self.tenant, user=self.user, role=TenantMembership.Role.OWNER)
        self.subscription = Subscription.objects.create(
            tenant=self.tenant,
            plan=self.plan,
            status=Subscription.Status.PENDING
        )
        self.client = Client()
        self.client.login(username='billing_user', password='TestPassword123!')

    def test_checkout_page_renders_merchant_numbers(self):
        res = self.client.get(reverse('billing:checkout', kwargs={'subscription_id': self.subscription.id}))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Inter Tournament')
        self.assertContains(res, '1500')
        self.assertContains(res, 'bKash')
        self.assertContains(res, 'Nagad')

    def test_submit_manual_payment_success(self):
        payload = {
            'method': Payment.Method.BKASH_MANUAL,
            'sender_phone': '01711122233',
            'transaction_id': 'TRX99887766'
        }
        res = self.client.post(
            reverse('billing:checkout', kwargs={'subscription_id': self.subscription.id}),
            payload
        )
        
        # Verify payment created in database
        payment = Payment.objects.filter(subscription=self.subscription).first()
        self.assertIsNotNone(payment)
        self.assertEqual(payment.amount_bdt, 1500)
        self.assertEqual(payment.method, Payment.Method.BKASH_MANUAL)
        self.assertEqual(payment.sender_phone, '01711122233')
        self.assertEqual(payment.transaction_id, 'TRX99887766')
        self.assertEqual(payment.status, Payment.Status.PENDING)

        # Redirect to status page
        self.assertRedirects(res, reverse('billing:status', kwargs={'subscription_id': self.subscription.id}))

    def test_status_page_renders_payment_history(self):
        Payment.objects.create(
            subscription=self.subscription,
            amount_bdt=1500,
            method=Payment.Method.NAGAD_MANUAL,
            sender_phone='01811122233',
            transaction_id='NAGAD12345',
            status=Payment.Status.PENDING
        )
        res = self.client.get(reverse('billing:status', kwargs={'subscription_id': self.subscription.id}))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'NAGAD12345')
        self.assertContains(res, 'DU Debating Society')

    def test_unauthorized_user_cannot_view_other_tenant_checkout(self):
        other_user = User.objects.create_user(username='other_user', password='TestPassword123!')
        other_client = Client()
        other_client.login(username='other_user', password='TestPassword123!')

        res = other_client.get(reverse('billing:checkout', kwargs={'subscription_id': self.subscription.id}))
        self.assertEqual(res.status_code, 404)

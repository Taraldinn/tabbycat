from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from billing.models import Payment, Plan, Subscription
from tenants.models import Tenant, TenantMembership

User = get_user_model()


class SuperAdminPanelsTestCase(TestCase):
    def setUp(self):
        # Create SuperAdmin user
        self.superadmin = User.objects.create_superuser(
            username='admin_boss',
            email='admin@tabbycat.org',
            password='AdminPassword123!'
        )
        # Create regular user
        self.regular_user = User.objects.create_user(
            username='regular_joe',
            password='UserPassword123!'
        )
        self.plan = Plan.objects.create(
            name="Large Tournament",
            slug="large-tournament",
            price_bdt=5000,
            billing_period="yearly",
            max_tournaments=10,
            max_teams_per_tournament=100,
            max_adjudicators_per_tournament=60,
            max_users=15,
            max_storage_mb=500
        )
        self.tenant = Tenant.objects.create(
            name="BRAC Debating Club",
            slug="brac-dc",
            owner=self.regular_user,
            is_active=False
        )
        self.subscription = Subscription.objects.create(
            tenant=self.tenant,
            plan=self.plan,
            status=Subscription.Status.PENDING
        )
        self.payment = Payment.objects.create(
            subscription=self.subscription,
            amount_bdt=5000,
            method=Payment.Method.BKASH_MANUAL,
            sender_phone='01700112233',
            transaction_id='BKASH778899',
            status=Payment.Status.PENDING
        )

        self.client = Client()

    def test_non_staff_cannot_access_superadmin(self):
        self.client.login(username='regular_joe', password='UserPassword123!')
        res = self.client.get(reverse('superadmin:dashboard'))
        # SuperAdminRequiredMixin redirects unauthorized users (302)
        self.assertEqual(res.status_code, 302)

    def test_superadmin_dashboard_renders_metrics(self):
        self.client.login(username='admin_boss', password='AdminPassword123!')
        res = self.client.get(reverse('superadmin:dashboard'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'BRAC Debating Club')
        self.assertContains(res, 'BKASH778899')

    def test_superadmin_tenant_list_and_search(self):
        self.client.login(username='admin_boss', password='AdminPassword123!')
        res = self.client.get(reverse('superadmin:tenant-list') + '?q=brac')
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'BRAC Debating Club')

    def test_verify_payment_workflow_and_sync_limits(self):
        self.client.login(username='admin_boss', password='AdminPassword123!')
        
        verify_url = reverse('superadmin:payment-verify', kwargs={'pk': self.payment.pk})
        res = self.client.post(verify_url, {'admin_notes': 'bKash transaction confirmed in statement.'})
        
        # Payment verified
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.VERIFIED)
        self.assertEqual(self.payment.verified_by, self.superadmin)
        self.assertIsNotNone(self.payment.verified_at)

        # Subscription active and extended
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, Subscription.Status.ACTIVE)
        self.assertGreater(self.subscription.current_period_end, timezone.now())

        # Tenant limits synced from plan
        self.tenant.refresh_from_db()
        self.assertTrue(self.tenant.is_active)
        self.assertEqual(self.tenant.max_tournaments, 10)
        self.assertEqual(self.tenant.max_teams_per_tournament, 100)
        self.assertEqual(self.tenant.max_adjudicators_per_tournament, 60)
        self.assertEqual(self.tenant.max_users, 15)

    def test_reject_payment_workflow(self):
        self.client.login(username='admin_boss', password='AdminPassword123!')
        
        reject_url = reverse('superadmin:payment-reject', kwargs={'pk': self.payment.pk})
        res = self.client.post(reject_url, {
            'rejection_reason': 'Transaction ID was not found in statement.',
            'admin_notes': 'Customer reached out via SMS'
        })
        
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.REJECTED)
        self.assertEqual(self.payment.rejection_reason, 'Transaction ID was not found in statement.')

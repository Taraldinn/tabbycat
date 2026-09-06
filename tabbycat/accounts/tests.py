from datetime import timedelta
import zoneinfo
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from billing.models import Plan, Subscription, Payment
from tenants.models import Tenant, TenantMembership
from accounts.models import UserProfile
from tournaments.models import Tournament

User = get_user_model()


class RegistrationTestCase(TestCase):
    def setUp(self):
        self.paid_plan = Plan.objects.create(
            name="Pro Plan",
            slug="pro-plan",
            description="Pro tournament plan",
            price_bdt=1500,
            billing_period="monthly",
            max_tournaments=3,
            max_teams_per_tournament=40,
            max_adjudicators_per_tournament=20,
            max_users=5,
            max_storage_mb=100
        )
        self.free_plan = Plan.objects.create(
            name="Free Trial",
            slug="free-trial",
            description="Free trial plan",
            price_bdt=0,
            billing_period="lifetime",
            max_tournaments=1,
            max_teams_per_tournament=20,
            max_adjudicators_per_tournament=10,
            max_users=2,
            max_storage_mb=50
        )
        self.client = Client()

    def test_registration_get_view_without_plans_renders_200(self):
        # Delete plans to simulate fresh database
        Plan.objects.all().delete()
        res = self.client.get(reverse('accounts:register'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "No plans are currently active")

    def test_registration_with_paid_plan_success(self):
        payload = {
            'first_name': 'Abrar',
            'last_name': 'Hasan',
            'username': 'abrar_hasan',
            'email': 'abrar@example.com',
            'phone': '01700000001',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
            'organization_name': 'North South Debating Club',
            'subdomain_slug': 'nsdc',
            'plan': self.paid_plan.id
        }
        res = self.client.post(reverse('accounts:register'), payload)
        
        # Check user created
        user = User.objects.filter(username='abrar_hasan').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.email, 'abrar@example.com')
        self.assertEqual(user.first_name, 'Abrar')

        # Check profile
        profile = UserProfile.objects.filter(user=user).first()
        self.assertIsNotNone(profile)
        self.assertEqual(profile.phone, '01700000001')

        # Check tenant created
        tenant = Tenant.objects.filter(slug='nsdc').first()
        self.assertIsNotNone(tenant)
        self.assertEqual(tenant.name, 'North South Debating Club')
        self.assertEqual(tenant.owner, user)
        self.assertFalse(tenant.is_active)  # Paid plan requires verification

        # Check membership
        membership = TenantMembership.objects.filter(tenant=tenant, user=user).first()
        self.assertIsNotNone(membership)
        self.assertEqual(membership.role, TenantMembership.Role.OWNER)

        # Check subscription
        sub = Subscription.objects.filter(tenant=tenant).first()
        self.assertIsNotNone(sub)
        self.assertEqual(sub.plan, self.paid_plan)
        self.assertEqual(sub.status, Subscription.Status.PENDING)

        # Redirects to checkout
        self.assertRedirects(res, reverse('billing:checkout', kwargs={'subscription_id': sub.id}))

    def test_registration_with_free_plan_success(self):
        payload = {
            'first_name': 'Nafis',
            'last_name': 'Ahmed',
            'username': 'nafis_ahmed',
            'email': 'nafis@example.com',
            'phone': '01700000002',
            'password': 'StrongPassword123!',
            'confirm_password': 'StrongPassword123!',
            'organization_name': 'Dhaka Debaters',
            'subdomain_slug': 'dhaka-debaters',
            'plan': self.free_plan.id
        }
        res = self.client.post(reverse('accounts:register'), payload)
        
        tenant = Tenant.objects.filter(slug='dhaka-debaters').first()
        self.assertIsNotNone(tenant)
        self.assertTrue(tenant.is_active)  # Free plan is active immediately

        sub = Subscription.objects.filter(tenant=tenant).first()
        self.assertEqual(sub.status, Subscription.Status.ACTIVE)
        self.assertRedirects(res, reverse('accounts:onboarding-success'))

    def test_registration_password_mismatch_error(self):
        payload = {
            'first_name': 'Test',
            'last_name': 'User',
            'username': 'test_user',
            'email': 'test@example.com',
            'phone': '01700000003',
            'password': 'Password123!',
            'confirm_password': 'DifferentPassword456!',
            'organization_name': 'Test Org',
            'subdomain_slug': 'test-org',
            'plan': self.paid_plan.id
        }
        res = self.client.post(reverse('accounts:register'), payload)
        self.assertEqual(res.status_code, 200)
        self.assertFalse(User.objects.filter(username='test_user').exists())
        self.assertFalse(Tenant.objects.filter(slug='test-org').exists())

    def test_registration_duplicate_username_and_slug(self):
        # Create existing user and tenant
        existing_user = User.objects.create_user(username='existinguser', email='existing@example.com', password='Password123!')
        Tenant.objects.create(name='Existing Org', slug='existing-slug', owner=existing_user, is_active=True)

        payload = {
            'first_name': 'New',
            'last_name': 'User',
            'username': 'existinguser',
            'email': 'newemail@example.com',
            'phone': '01700000004',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'organization_name': 'New Org',
            'subdomain_slug': 'existing-slug',
            'plan': self.paid_plan.id
        }
        res = self.client.post(reverse('accounts:register'), payload)
        self.assertEqual(res.status_code, 200)
        self.assertIn('username', res.context['form'].errors)
        self.assertIn('subdomain_slug', res.context['form'].errors)


class UserProfileAndTimezoneTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='samir',
            email='samir@example.com',
            password='TestPassword123!',
            first_name='Samir',
            last_name='Khan'
        )
        self.profile, created = UserProfile.objects.get_or_create(user=self.user)
        self.profile.phone = '01711111111'
        self.profile.timezone = 'Asia/Dhaka'
        self.profile.save()

        self.client = Client()
        self.client.login(username='samir', password='TestPassword123!')

    def test_get_user_profile_view(self):
        res = self.client.get(reverse('accounts:profile'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Samir')
        self.assertContains(res, 'Asia/Dhaka')

    def test_update_profile_and_timezone(self):
        payload = {
            'first_name': 'Samir Updated',
            'last_name': 'Khan Updated',
            'email': 'samir.updated@example.com',
            'phone': '01799999999',
            'timezone': 'America/New_York'
        }
        res = self.client.post(reverse('accounts:profile'), payload)
        self.assertRedirects(res, reverse('accounts:profile'))

        # Verify DB
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Samir Updated')
        self.assertEqual(self.user.email, 'samir.updated@example.com')
        
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.phone, '01799999999')
        self.assertEqual(self.profile.timezone, 'America/New_York')

    def test_timezone_middleware_activation(self):
        # Change timezone to Tokyo
        self.profile.timezone = 'Asia/Tokyo'
        self.profile.save()

        res = self.client.get(reverse('accounts:profile'))
        self.assertEqual(res.status_code, 200)
        # Verify active timezone
        current_tz = timezone.get_current_timezone_name()
        self.assertEqual(current_tz, 'Asia/Tokyo')


class ClientDashboardAndQueueTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='org_admin',
            email='org_admin@example.com',
            password='TestPassword123!'
        )
        self.plan1 = Plan.objects.create(
            name="Starter Plan", slug="starter", price_bdt=500, billing_period="monthly", max_tournaments=1
        )
        self.plan2 = Plan.objects.create(
            name="Pro Plan", slug="pro", price_bdt=2000, billing_period="yearly", max_tournaments=10
        )
        self.tenant = Tenant.objects.create(
            name="IUB Debating Club", slug="iubdc", owner=self.user, is_active=True, max_tournaments=1
        )
        TenantMembership.objects.create(tenant=self.tenant, user=self.user, role=TenantMembership.Role.OWNER)
        self.sub = Subscription.objects.create(
            tenant=self.tenant,
            plan=self.plan1,
            status=Subscription.Status.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timedelta(days=30)
        )
        self.tournament = Tournament.objects.create(name="IUB IV", slug="iub-iv", tenant=self.tenant)
        self.client = Client()
        self.client.login(username='org_admin', password='TestPassword123!')

    def test_client_dashboard_render(self):
        res = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'IUB Debating Club')
        self.assertContains(res, 'Starter Plan')

    def test_upgrade_plan_submission_from_dashboard(self):
        payload = {'new_plan_id': self.plan2.id}
        res = self.client.post(reverse('accounts:dashboard'), payload)
        
        self.sub.refresh_from_db()
        self.assertEqual(self.sub.plan, self.plan2)
        self.assertEqual(self.sub.status, Subscription.Status.PENDING)
        self.assertRedirects(res, reverse('billing:checkout', kwargs={'subscription_id': self.sub.id}))

    def test_update_custom_domain_success(self):
        payload = {
            'action': 'update_domain',
            'custom_domain': 'debates.iubdc.org'
        }
        res = self.client.post(reverse('accounts:dashboard'), payload)
        self.assertRedirects(res, reverse('accounts:dashboard'))

        self.tenant.refresh_from_db()
        self.assertEqual(self.tenant.custom_domain, 'debates.iubdc.org')

    def test_update_custom_domain_duplicate(self):
        other_user = User.objects.create_user(username='other_u', email='other@test.com', password='Password123!')
        Tenant.objects.create(name='Other Org', slug='other-org', owner=other_user, custom_domain='debates.taken.org')

        payload = {
            'action': 'update_domain',
            'custom_domain': 'debates.taken.org'
        }
        res = self.client.post(reverse('accounts:dashboard'), payload)
        self.assertRedirects(res, reverse('accounts:dashboard'))

        self.tenant.refresh_from_db()
        self.assertNotEqual(self.tenant.custom_domain, 'debates.taken.org')

    def test_delete_custom_domain_success(self):
        self.tenant.custom_domain = 'debates.iubdc.org'
        self.tenant.save()

        payload = {'action': 'delete_domain'}
        res = self.client.post(reverse('accounts:dashboard'), payload)
        self.assertRedirects(res, reverse('accounts:dashboard'))

        self.tenant.refresh_from_db()
        self.assertIsNone(self.tenant.custom_domain)

    def test_add_site_manager_success(self):
        new_manager = User.objects.create_user(
            username='manager_tara', email='tara@iubdc.org', password='Password123!'
        )
        payload = {
            'action': 'add_manager',
            'username_or_email': 'manager_tara',
            'role': TenantMembership.Role.ADMIN
        }
        res = self.client.post(reverse('accounts:dashboard'), payload)
        self.assertRedirects(res, reverse('accounts:dashboard'))

        membership = TenantMembership.objects.filter(tenant=self.tenant, user=new_manager).first()
        self.assertIsNotNone(membership)
        self.assertEqual(membership.role, TenantMembership.Role.ADMIN)

    def test_add_site_manager_nonexistent_user(self):
        payload = {
            'action': 'add_manager',
            'username_or_email': 'ghost_user',
            'role': TenantMembership.Role.MEMBER
        }
        res = self.client.post(reverse('accounts:dashboard'), payload)
        self.assertRedirects(res, reverse('accounts:dashboard'))
        self.assertEqual(TenantMembership.objects.filter(tenant=self.tenant).count(), 1)

    def test_all_dashboard_button_links_and_destinations(self):
        # 1. Dashboard loads with 200 OK
        res = self.client.get(reverse('accounts:dashboard'))
        self.assertEqual(res.status_code, 200)

        # 2. Checkout link for active subscription loads 200 OK
        res_checkout = self.client.get(reverse('billing:checkout', kwargs={'subscription_id': self.sub.id}))
        self.assertEqual(res_checkout.status_code, 200)
        self.assertContains(res_checkout, 'Payment & Plan Activation')

        # 3. Status link loads 200 OK
        res_status = self.client.get(reverse('billing:status', kwargs={'subscription_id': self.sub.id}))
        self.assertEqual(res_status.status_code, 200)
        self.assertContains(res_status, 'Subscription Overview')

        # 4. Tournament public page loads or redirects properly on tenant host
        host = f"{self.tenant.slug}.tabbycatbd.com"
        res_tournament = self.client.get(f"/{self.tournament.slug}/", HTTP_HOST=host)
        self.assertIn(res_tournament.status_code, [200, 302])

        # 5. Tournament admin page loads or redirects properly for authenticated user on tenant host
        res_tournament_admin = self.client.get(f"/{self.tournament.slug}/admin/", HTTP_HOST=host)
        self.assertIn(res_tournament_admin.status_code, [200, 302])



from django.contrib.auth import get_user_model
from django.http import Http404
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse

from tenants.middleware import TenantMiddleware
from tenants.models import Tenant, TenantMembership
from tournaments.models import Tournament

User = get_user_model()


class TenantMiddlewareAndRoutingTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='tenant_owner',
            password='Password123!'
        )
        self.tenant = Tenant.objects.create(
            name="CUET Debating Society",
            slug="cuet-ds",
            custom_domain="cuetdebating.org",
            owner=self.user,
            is_active=True,
            max_tournaments=2
        )
        self.factory = RequestFactory()
        self.middleware = TenantMiddleware(get_response=lambda r: None)

    def test_subdomain_resolution_via_middleware(self):
        request = self.factory.get('/', HTTP_HOST='cuet-ds.tabbycatbd.com')
        self.middleware(request)
        self.assertEqual(request.tenant, self.tenant)

    def test_custom_domain_resolution_via_middleware(self):
        request = self.factory.get('/', HTTP_HOST='cuetdebating.org')
        self.middleware(request)
        self.assertEqual(request.tenant, self.tenant)

    def test_unknown_host_raises_404(self):
        request = self.factory.get('/', HTTP_HOST='unknown-club.tabbycatbd.com')
        with self.assertRaises(Http404):
            self.middleware(request)

    def test_membership_roles(self):
        member = User.objects.create_user(username='member_user', password='Password123!')
        membership = TenantMembership.objects.create(
            tenant=self.tenant,
            user=member,
            role=TenantMembership.Role.MEMBER
        )
        self.assertEqual(membership.role, TenantMembership.Role.MEMBER)
        self.assertFalse(membership.role == TenantMembership.Role.OWNER)

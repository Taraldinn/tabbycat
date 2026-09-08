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

    def test_shebafi_subdomain_resolution_via_middleware(self):
        request = self.factory.get('/', HTTP_HOST='cuet-ds.shebafi.xyz')
        self.middleware(request)
        self.assertEqual(request.tenant, self.tenant)

    def test_shebafi_base_domain_is_landing(self):
        request = self.factory.get('/', HTTP_HOST='shebafi.xyz')
        self.middleware(request)
        self.assertIsNone(request.tenant)
        self.assertFalse(request.is_platform_admin)

    def test_shebafi_www_redirects_with_path(self):
        request = self.factory.get('/robots.txt', HTTP_HOST='www.shebafi.xyz')
        response = self.middleware(request)
        self.assertEqual(response.status_code, 301)
        self.assertTrue(response.url.endswith('shebafi.xyz/robots.txt'))

    def test_shebafi_admin_subdomain(self):
        request = self.factory.get('/', HTTP_HOST='admin.shebafi.xyz')
        self.middleware(request)
        self.assertTrue(request.is_platform_admin)

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


class TenantIsolationViewAndAPITestCase(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='iso_user1', password='Password123!')
        self.user2 = User.objects.create_user(username='iso_user2', password='Password123!')
        self.tenant1 = Tenant.objects.create(name="Tenant 1", slug="t1", owner=self.user1)
        self.tenant2 = Tenant.objects.create(name="Tenant 2", slug="t2", owner=self.user2)

        self.tournament1 = Tournament.objects.create(name="Tournament 1", slug="tourn-1", tenant=self.tenant1, active=True)
        self.tournament2 = Tournament.objects.create(name="Tournament 2", slug="tourn-2", tenant=self.tenant2, active=True)
        self.factory = RequestFactory()

    def test_public_site_index_scoped_to_tenant(self):
        from django.contrib.auth.models import AnonymousUser
        from tournaments.views import PublicSiteIndexView
        from django.test import override_settings

        with override_settings(MULTI_TENANT_MODE=True):
            request = self.factory.get('/?redirect=false')
            request.tenant = self.tenant1
            request.user = AnonymousUser()
            view = PublicSiteIndexView()
            view.setup(request)
            context = view.get_context_data()
            self.assertIn(self.tournament1, context['tournaments'])
            self.assertNotIn(self.tournament2, context['tournaments'])

    def test_public_site_index_base_domain_no_leaks(self):
        from django.contrib.auth.models import AnonymousUser
        from tournaments.views import PublicSiteIndexView
        from django.test import override_settings

        with override_settings(MULTI_TENANT_MODE=True):
            request = self.factory.get('/?redirect=false')
            request.tenant = None
            request.user = AnonymousUser()
            view = PublicSiteIndexView()
            view.setup(request)
            context = view.get_context_data()
            self.assertEqual(list(context['tournaments']), [])
            self.assertEqual(list(context['inactive']), [])

    def test_public_site_index_single_tournament_redirect(self):
        from django.contrib.auth.models import AnonymousUser
        from tournaments.views import PublicSiteIndexView
        from django.test import override_settings

        with override_settings(MULTI_TENANT_MODE=True):
            request = self.factory.get('/')
            request.tenant = self.tenant1
            request.user = AnonymousUser()
            response = PublicSiteIndexView.as_view()(request)
            self.assertEqual(response.status_code, 302)
            self.assertIn(self.tournament1.slug, response.url)

    def test_api_tournament_viewset_queryset_scoped_to_tenant(self):
        from api.views import TournamentViewSet
        from django.test import override_settings

        with override_settings(MULTI_TENANT_MODE=True):
            request = self.factory.get('/api/v1/tournaments/')
            request.tenant = self.tenant1
            request.user = self.user1
            viewset = TournamentViewSet()
            viewset.request = request
            qs = viewset.get_queryset()
            self.assertIn(self.tournament1, qs)
            self.assertNotIn(self.tournament2, qs)

    def test_api_tournament_viewset_base_domain_empty_for_anon(self):
        from django.contrib.auth.models import AnonymousUser
        from api.views import TournamentViewSet
        from django.test import override_settings

        with override_settings(MULTI_TENANT_MODE=True):
            request = self.factory.get('/api/v1/tournaments/')
            request.tenant = None
            request.user = AnonymousUser()
            viewset = TournamentViewSet()
            viewset.request = request
            qs = viewset.get_queryset()
            self.assertEqual(list(qs), [])

    def test_tournament_api_mixin_cross_tenant_isolation(self):
        from rest_framework.views import APIView
        from api.mixins import TournamentAPIMixin
        from django.test import override_settings

        class DummyView(TournamentAPIMixin, APIView):
            pass

        with override_settings(MULTI_TENANT_MODE=True):
            # Tenant 1 accessing Tournament 1 -> OK
            req1 = self.factory.get('/api/v1/tournaments/tourn-1/')
            req1.tenant = self.tenant1
            view1 = DummyView()
            view1.request = req1
            view1.kwargs = {'tournament_slug': 'tourn-1'}
            self.assertEqual(view1.tournament, self.tournament1)

            # Tenant 2 accessing Tournament 1 -> 404
            req2 = self.factory.get('/api/v1/tournaments/tourn-1/')
            req2.tenant = self.tenant2
            view2 = DummyView()
            view2.request = req2
            view2.kwargs = {'tournament_slug': 'tourn-1'}
            with self.assertRaises(Http404):
                _ = view2.tournament

    def test_tournament_from_url_mixin_tenant_isolation(self):
        from django.contrib.auth.models import AnonymousUser
        from tournaments.mixins import TournamentFromUrlMixin
        from django.test import override_settings

        class DummyUrlView(TournamentFromUrlMixin):
            def __init__(self, request, kwargs):
                self.request = request
                self.kwargs = kwargs

        with override_settings(MULTI_TENANT_MODE=True):
            # Tenant 1 accessing Tournament 1 -> OK
            req1 = self.factory.get('/tourn-1/')
            req1.tenant = self.tenant1
            view1 = DummyUrlView(req1, {'tournament_slug': 'tourn-1'})
            self.assertEqual(view1.tournament, self.tournament1)

            # Tenant 2 accessing Tournament 1 -> 404
            req2 = self.factory.get('/tourn-1/')
            req2.tenant = self.tenant2
            view2 = DummyUrlView(req2, {'tournament_slug': 'tourn-1'})
            with self.assertRaises(Http404):
                _ = view2.tournament

            # Base domain (no tenant) accessing Tenant 1's tournament -> 404
            req3 = self.factory.get('/tourn-1/')
            req3.tenant = None
            req3.user = AnonymousUser()
            view3 = DummyUrlView(req3, {'tournament_slug': 'tourn-1'})
            with self.assertRaises(Http404):
                _ = view3.tournament

    def test_tournament_name_readonly_for_tenant_user_in_admin(self):
        from tournaments.admin import TournamentAdmin
        from django.contrib.admin.sites import AdminSite

        admin_instance = TournamentAdmin(Tournament, AdminSite())
        
        # Non-superuser tenant owner
        req = self.factory.get('/admin/tournaments/tournament/1/change/')
        req.user = self.user1
        req.user.is_staff = True
        req.user.is_superuser = False
        readonly_fields = admin_instance.get_readonly_fields(req, obj=self.tournament1)
        self.assertIn('name', readonly_fields)
        self.assertIn('short_name', readonly_fields)
        self.assertIn('slug', readonly_fields)

        # Superuser (SaaS Admin) can edit name
        superuser = User.objects.create_superuser('admin_tester', 'admin@example.com', 'Pass123!')
        req_admin = self.factory.get('/admin/tournaments/tournament/1/change/')
        req_admin.user = superuser
        readonly_super = admin_instance.get_readonly_fields(req_admin, obj=self.tournament1)
        self.assertNotIn('name', readonly_super)

    def test_tournament_format_option_restricted_for_tenant_user(self):
        from tournaments.forms import TournamentConfigureForm
        from options.views import SetPresetPreferencesView

        # TournamentConfigureForm disables preset_rules for tenant user
        form = TournamentConfigureForm(instance=self.tournament1, user=self.user1)
        self.assertTrue(form.fields['preset_rules'].disabled)

        # SetPresetPreferencesView redirects with error for tenant user
        view = SetPresetPreferencesView()
        req = self.factory.post(f'/{self.tournament1.slug}/admin/options/presets/bp/confirm/')
        req.user = self.user1
        req.user.is_staff = True
        req.user.is_superuser = False
        req.tenant = self.tenant1
        
        # Add messages middleware support for request
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(req, 'session', 'session')
        messages = FallbackStorage(req)
        setattr(req, '_messages', messages)

        view.request = req
        view.kwargs = {'tournament_slug': self.tournament1.slug, 'preset_name': 'bp'}
        response = view.dispatch(req, tournament_slug=self.tournament1.slug, preset_name='bp')
        self.assertEqual(response.status_code, 302)

    def test_tenant_staff_user_has_database_editing_permissions(self):
        from participants.models import Team
        from participants.admin import TeamAdmin
        from django.contrib.admin.sites import AdminSite

        team_admin = TeamAdmin(Team, AdminSite())
        req = self.factory.get('/admin/participants/team/')
        req.user = self.user1
        req.user.is_staff = True
        req.user.is_superuser = False
        req.tenant = self.tenant1

        self.assertTrue(team_admin.has_module_permission(req))
        self.assertTrue(team_admin.has_view_permission(req))
        self.assertTrue(team_admin.has_change_permission(req))
        self.assertTrue(team_admin.has_add_permission(req))


class RenderSettingsTestCase(TestCase):
    def test_multi_tenant_parsing(self):
        truthy = ['true', 'True', '1', 'yes', 'YES']
        falsy = ['false', 'False', '0', 'no', 'disabled']
        for val in truthy:
            parsed = val.lower() in ('true', '1', 'yes')
            self.assertTrue(parsed, f"Failed for {val}")
        for val in falsy:
            parsed = val.lower() in ('true', '1', 'yes')
            self.assertFalse(parsed, f"Failed for {val}")


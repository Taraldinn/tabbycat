from django.test import Client, TestCase
from django.urls import reverse

from billing.models import Plan


class LandingPagesTestCase(TestCase):
    def setUp(self):
        self.plan = Plan.objects.create(
            name="Single Pro",
            slug="single-pro",
            price_bdt=800,
            billing_period="monthly",
            max_tournaments=1,
            max_teams_per_tournament=30,
            max_adjudicators_per_tournament=15,
            is_active=True
        )
        self.client = Client()

    def test_homepage_renders(self):
        res = self.client.get(reverse('landing:home'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'The Gold Standard for')
        self.assertContains(res, 'Single Pro')
        self.assertContains(res, 'Tabbycat Debate Association')

    def test_pricing_page_renders(self):
        res = self.client.get(reverse('landing:pricing'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Tournament Packages & Subscriptions')
        self.assertContains(res, 'Single Pro')

    def test_features_page_renders(self):
        res = self.client.get(reverse('landing:features'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Platform Features')

    def test_contact_page_renders(self):
        res = self.client.get(reverse('landing:contact'))
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'Get in Touch with Tabbycat')

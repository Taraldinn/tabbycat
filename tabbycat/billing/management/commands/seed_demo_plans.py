from django.core.management.base import BaseCommand
from billing.models import Plan

DEMO_PLANS = [
    {
        "name": "Intra Tournament",
        "slug": "intra-tournament",
        "description": "Ideal for internal school, college, or club tournaments with a single debate event.",
        "price_bdt": 500.00,
        "billing_period": "monthly",
        "is_active": True,
        "is_featured": False,
        "display_order": 1,
        "max_tournaments": 1,
        "max_teams_per_tournament": 24,
        "max_adjudicators_per_tournament": 16,
        "max_users": 3,
        "max_storage_mb": 50,
        "custom_domain_allowed": False,
        "priority_support": False,
        "api_access": False,
    },
    {
        "name": "Inter Tournament",
        "slug": "inter-tournament",
        "description": "Standard package for inter-institution, open circuit, and regional tournaments.",
        "price_bdt": 1500.00,
        "billing_period": "monthly",
        "is_active": True,
        "is_featured": True,
        "display_order": 2,
        "max_tournaments": 2,
        "max_teams_per_tournament": 48,
        "max_adjudicators_per_tournament": 32,
        "max_users": 6,
        "max_storage_mb": 150,
        "custom_domain_allowed": False,
        "priority_support": True,
        "api_access": False,
    },
    {
        "name": "Single Pro",
        "slug": "single-pro",
        "description": "Professional tournament edition with high team limits, custom domain, and dedicated support.",
        "price_bdt": 3000.00,
        "billing_period": "monthly",
        "is_active": True,
        "is_featured": False,
        "display_order": 3,
        "max_tournaments": 1,
        "max_teams_per_tournament": 80,
        "max_adjudicators_per_tournament": 50,
        "max_users": 10,
        "max_storage_mb": 300,
        "custom_domain_allowed": True,
        "priority_support": True,
        "api_access": True,
    },
    {
        "name": "Large Tournament",
        "slug": "large-tournament",
        "description": "Enterprise-grade power for national opens, internationals, and massive multi-category debate fests.",
        "price_bdt": 5000.00,
        "billing_period": "monthly",
        "is_active": True,
        "is_featured": False,
        "display_order": 4,
        "max_tournaments": 3,
        "max_teams_per_tournament": 140,
        "max_adjudicators_per_tournament": 90,
        "max_users": 20,
        "max_storage_mb": 500,
        "custom_domain_allowed": True,
        "priority_support": True,
        "api_access": True,
    },
    {
        "name": "Yearly Membership",
        "slug": "yearly",
        "description": "Full annual access for debate societies and institutions running multiple tournaments year-round.",
        "price_bdt": 12000.00,
        "billing_period": "yearly",
        "is_active": True,
        "is_featured": False,
        "display_order": 5,
        "max_tournaments": 20,
        "max_teams_per_tournament": 100,
        "max_adjudicators_per_tournament": 60,
        "max_users": 30,
        "max_storage_mb": 1500,
        "custom_domain_allowed": True,
        "priority_support": True,
        "api_access": True,
    },
]


class Command(BaseCommand):
    help = "Seed demo pricing plans (Intra, Inter, Single Pro, Large, Yearly)"

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo pricing plans...")
        for plan_data in DEMO_PLANS:
            slug = plan_data["slug"]
            plan, created = Plan.objects.update_or_create(
                slug=slug,
                defaults=plan_data,
            )
            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(f"{action} plan: {plan.name} (৳{plan.price_bdt}/{plan.billing_period})"))

        self.stdout.write(self.style.SUCCESS("All demo pricing plans seeded successfully!"))

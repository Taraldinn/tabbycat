from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from tenants.models import Tenant
from tournaments.models import Tournament
from participants.models import Institution

User = get_user_model()

class Command(BaseCommand):
    help = 'Backfills existing data by assigning it to a default legacy tenant.'

    def handle(self, *args, **options):
        # 1. Get or create a superuser to own the default tenant
        owner = User.objects.filter(is_superuser=True).first()
        if not owner:
            self.stdout.write(self.style.ERROR('No superuser found. Create a superuser first.'))
            return

        # 2. Get or create the default tenant
        tenant, created = Tenant.objects.get_or_create(
            slug='default',
            defaults={
                'name': 'Legacy Tabbycat Instance',
                'owner': owner,
                'is_active': True,
                'max_tournaments': 9999,
                'max_teams_per_tournament': 9999,
                'max_adjudicators_per_tournament': 9999,
                'max_users': 9999,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('Created default tenant.'))
        else:
            self.stdout.write('Default tenant already exists.')

        # 3. Assign all tenantless tournaments to the default tenant
        tournaments_updated = Tournament.objects.filter(tenant__isnull=True).update(tenant=tenant)
        self.stdout.write(self.style.SUCCESS(f'Assigned {tournaments_updated} tournaments to default tenant.'))

        # 4. Assign all tenantless institutions to the default tenant
        institutions_updated = Institution.objects.filter(tenant__isnull=True).update(tenant=tenant)
        self.stdout.write(self.style.SUCCESS(f'Assigned {institutions_updated} institutions to default tenant.'))

        self.stdout.write(self.style.SUCCESS('Backfill complete!'))

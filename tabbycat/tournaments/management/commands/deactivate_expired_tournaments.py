"""Management command to auto-deactivate expired tournaments."""
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Deactivate tournaments that have passed their expiry date (default: 6 months after creation)."

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help="Show which tournaments would be deactivated without actually deactivating them.",
        )
        parser.add_argument(
            '--tenant',
            type=str,
            default=None,
            help="Limit deactivation to a specific tenant slug.",
        )

    def handle(self, *args, **options):
        from tournaments.models import Tournament

        now = timezone.now()
        dry_run = options['dry_run']
        tenant_slug = options.get('tenant')

        qs = Tournament.objects.filter(
            active=True,
            expires_at__isnull=False,
            expires_at__lte=now,
        )

        if tenant_slug:
            qs = qs.filter(tenant__slug=tenant_slug)

        count = qs.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS("No expired tournaments found."))
            return

        for t in qs:
            expiry_str = t.expires_at.strftime('%Y-%m-%d')
            tenant_name = t.tenant.name if t.tenant else "—"
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f"[DRY RUN] Would deactivate: [{tenant_name}] {t.name} "
                        f"(slug={t.slug}, expired={expiry_str})"
                    )
                )
            else:
                t.active = False
                t.save(update_fields=['active'])
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Deactivated: [{tenant_name}] {t.name} "
                        f"(slug={t.slug}, expired={expiry_str})"
                    )
                )

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(f"\nDone. Deactivated {count} tournament(s).")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f"\nDry run: {count} tournament(s) would be deactivated.")
            )

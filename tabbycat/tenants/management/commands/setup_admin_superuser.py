import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update superuser with default or environment credentials"

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            default=os.environ.get('DJANGO_SUPERUSER_USERNAME', 'aldinn'),
            help='Superuser username'
        )
        parser.add_argument(
            '--email',
            default=os.environ.get('DJANGO_SUPERUSER_EMAIL', 'kferdoush617@gmail.com'),
            help='Superuser email'
        )
        parser.add_argument(
            '--password',
            default=os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'tara45@@'),
            help='Superuser password'
        )

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        email = options['email']
        password = options['password']

        user, created = User.objects.get_or_create(username=username, defaults={'email': email})
        user.email = email
        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"{action} superuser '{username}' ({email}) successfully."))

        # Ensure all existing tenant owners and members have staff status for database editing
        updated_count = User.objects.filter(tenant_memberships__isnull=False, is_staff=False).update(is_staff=True)
        if updated_count:
            self.stdout.write(self.style.SUCCESS(f"Granted database editing access (staff status) to {updated_count} tenant users."))

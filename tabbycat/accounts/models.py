from django.db import models
from django.conf import settings

class UserProfile(models.Model):
    """Extends auth.User with phone number, timezone, and personal preferences."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='profile')
    phone = models.CharField(max_length=20, blank=True,
        help_text="Phone number, e.g. 01XXXXXXXXX")
    phone_verified = models.BooleanField(default=False)
    timezone = models.CharField(max_length=50, default='Asia/Dhaka', blank=True,
        help_text="User's preferred timezone for tournament schedules and timestamps")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile for {self.user.username} ({self.timezone})"

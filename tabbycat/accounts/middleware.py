import zoneinfo
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin


class TimezoneMiddleware(MiddlewareMixin):
    """
    Activates the authenticated user's preferred timezone for the duration of the request.
    """
    def process_request(self, request):
        if request.user.is_authenticated:
            try:
                profile = getattr(request.user, 'profile', None)
                if profile and profile.timezone:
                    try:
                        timezone.activate(zoneinfo.ZoneInfo(profile.timezone))
                        return
                    except Exception:
                        pass
            except Exception:
                pass
        timezone.deactivate()

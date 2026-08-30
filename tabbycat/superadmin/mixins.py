from django.contrib.auth.mixins import AccessMixin
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.translation import gettext_lazy as _


class SuperAdminRequiredMixin(AccessMixin):
    """Verify that the current user is authenticated and is a superuser or platform admin."""

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        is_allowed = (
            request.user.is_superuser or
            getattr(request, 'is_platform_admin', False) or
            request.user.is_staff
        )

        if not is_allowed:
            messages.error(request, _("Access restricted to platform administrators."))
            return redirect('tabbycat-index')

        return super().dispatch(request, *args, **kwargs)

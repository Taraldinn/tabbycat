from functools import wraps
from django.core.exceptions import PermissionDenied
from django.http import Http404

from .models import TenantMembership

def require_tenant(view_func):
    """Ensure the view is only accessed within a tenant context."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not getattr(request, 'tenant', None):
            raise Http404("This view requires a valid tenant.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def require_tenant_role(min_role):
    """
    Ensure the user has at least `min_role` for the current tenant.
    Roles are ordered: OWNER > ADMIN > MEMBER.
    """
    role_weights = {
        TenantMembership.Role.OWNER: 3,
        TenantMembership.Role.ADMIN: 2,
        TenantMembership.Role.MEMBER: 1,
    }

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            tenant = getattr(request, 'tenant', None)
            if not tenant:
                raise Http404("This view requires a valid tenant.")

            if not request.user.is_authenticated:
                raise PermissionDenied("Authentication required.")

            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)

            membership = tenant.memberships.filter(user=request.user).first()
            if not membership:
                raise PermissionDenied("You are not a member of this tenant.")

            user_weight = role_weights.get(membership.role, 0)
            required_weight = role_weights.get(min_role, 1)

            if user_weight < required_weight:
                raise PermissionDenied(f"This action requires {min_role} access.")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

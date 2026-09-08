from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .misc import get_ip_address

""" General utilities for extending filters/lists in the admin area """

# ==============================================================================
# Utilities
# ==============================================================================


class ModelAdmin(admin.ModelAdmin):

    def add_ip_to_message(self, request, message):
        ip_address = get_ip_address(request)
        if type(message) is list:  # JSON
            message.append({'identity': {'ip': ip_address}})
        else:
            message += "\nIP: %s" % (ip_address,)
        return message

    def log_addition(self, request, object, message):
        return super().log_addition(request, object, self.add_ip_to_message(request, message))

    def log_change(self, request, object, message):
        return super().log_change(request, object, self.add_ip_to_message(request, message))

    def log_deletions(self, request, queryset):
        from django.contrib.admin.models import DELETION, LogEntry
        return LogEntry.objects.log_actions(
            user_id=request.user.pk,
            queryset=queryset,
            action_flag=DELETION,
            change_message=self.add_ip_to_message(request, ''),
        )

    def has_module_permission(self, request):
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser or getattr(request, 'is_platform_admin', False)):
            return True
        return super().has_module_permission(request)

    def has_view_permission(self, request, obj=None):
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser or getattr(request, 'is_platform_admin', False)):
            return True
        return super().has_view_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser or getattr(request, 'is_platform_admin', False)):
            return True
        return super().has_change_permission(request, obj)

    def has_add_permission(self, request):
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser or getattr(request, 'is_platform_admin', False)):
            return True
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        if request.user.is_authenticated and (request.user.is_staff or request.user.is_superuser or getattr(request, 'is_platform_admin', False)):
            return True
        return super().has_delete_permission(request, obj)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser or getattr(request, 'is_platform_admin', False):
            return qs

        # Determine user's tenant(s)
        tenant = getattr(request, 'tenant', None)
        user_tenants = list(request.user.tenant_memberships.values_list('tenant_id', flat=True)) if hasattr(request.user, 'tenant_memberships') else []
        if tenant and tenant.id not in user_tenants:
            user_tenants.append(tenant.id)

        if not user_tenants:
            return qs

        model = self.model
        field_names = [f.name for f in model._meta.get_fields()]

        if 'tenant' in field_names:
            return qs.filter(tenant_id__in=user_tenants)
        elif 'tournament' in field_names:
            return qs.filter(tournament__tenant_id__in=user_tenants)
        elif 'round' in field_names:
            return qs.filter(round__tournament__tenant_id__in=user_tenants)
        elif 'debate' in field_names:
            return qs.filter(debate__round__tournament__tenant_id__in=user_tenants)

        return qs


class TabbycatModelAdminFieldsMixin:

    @admin.display(description=_("Round"))
    def get_round(self, obj):
        if hasattr(obj, 'debate'):
            return obj.debate.round.name
        else:
            return obj.debate_team.debate.round.name

    @admin.display(description=_("Team"))
    def get_team(self, obj):
        return obj.debate_team.team

    @admin.display(description=_("Speaker"))
    def get_speaker_name(self, obj):
        return obj.speaker.name

    @admin.display(description=_("Tournament"))
    def get_tournament(self, obj):
        if hasattr(obj, 'round'):
            return obj.round.tournament
        else:
            return obj.debate.round.tournament

    @admin.display(description=_("Side"))
    def get_team_side(self, obj):
        return obj.debate_team.side

    @admin.display(description=_("Motion"))
    def get_motion_ref(self, obj):
        return obj.motion.reference

    @admin.display(description=_("Confirmed"))
    def get_confirmed(self, obj):
        return obj.ballot_submission.confirmed

    @admin.display(description=_("Adjudicator"))
    def get_adj_name(self, obj):
        return obj.debate_adjudicator.adjudicator.name


def custom_titled_filter(title):
    class Wrapper(admin.RelatedFieldListFilter):
        def __new__(cls, *args, **kwargs):
            instance = admin.FieldListFilter.create(*args, **kwargs)
            instance.title = title
            return instance
    return Wrapper

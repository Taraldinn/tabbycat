from django.contrib import admin

from utils.admin import ModelAdmin

from .models import Round, ScheduleEvent, Tournament


# ==============================================================================
# Tournament
# ==============================================================================

@admin.register(Tournament)
class TournamentAdmin(ModelAdmin):
    list_display = ('name', 'slug', 'seq', 'short_name', 'current_round', 'active')
    ordering = ('seq', )

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        # Non-superusers cannot rename an existing tournament
        if obj and not (request.user.is_superuser or getattr(request, 'is_platform_admin', False)):
            for f in ['name', 'short_name', 'slug']:
                if f not in readonly:
                    readonly.append(f)
        return readonly

    def has_delete_permission(self, request, obj=None):
        # Non-superusers cannot delete a tournament directly
        if request.user.is_superuser or getattr(request, 'is_platform_admin', False):
            return True
        return False


# ==============================================================================
# Round
# ==============================================================================

@admin.register(Round)
class RoundAdmin(ModelAdmin):
    list_display = ('name', 'tournament', 'seq', 'abbreviation', 'stage',
                    'draw_type', 'draw_status', 'feedback_weight', 'silent',
                    'motions_status', 'starts_at', 'completed')
    list_editable = ('feedback_weight', 'silent', 'motions_status', 'completed')
    list_filter = ('tournament', )
    search_fields = ('name', 'seq', 'abbreviation', 'stage', 'draw_type', 'draw_status')
    ordering = ('tournament__slug', 'seq')


@admin.register(ScheduleEvent)
class ScheduleEventAdmin(ModelAdmin):
    list_display = ('tournament', 'title', 'type', 'start_time', 'end_time', 'round')
    list_filter = ('tournament', 'type')
    search_fields = ('title',)
    ordering = ('tournament', 'start_time')

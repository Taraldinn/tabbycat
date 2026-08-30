from django.conf import settings

from tournaments.models import Tournament


def debate_context(request):

    all_tournaments = Tournament.objects.none()
    if hasattr(request, 'tenant') and request.tenant:
        all_tournaments = Tournament.objects.filter(active=True, tenant=request.tenant)
    elif not getattr(settings, 'MULTI_TENANT_MODE', False):
        all_tournaments = Tournament.objects.filter(active=True)

    context = {
        'tabbycat_version': settings.TABBYCAT_VERSION or "",
        'tabbycat_codename': settings.TABBYCAT_CODENAME or "no codename",
        'all_tournaments': all_tournaments,
        'disable_sentry': getattr(settings, 'DISABLE_SENTRY', False),
        'on_local': getattr(settings, 'ON_LOCAL', False),
        'hmr': getattr(settings, 'USE_WEBPACK_SERVER', False),
    }

    if hasattr(request, 'tournament'):
        current_round = request.tournament.current_round

        context.update({
            'tournament': request.tournament,
            'pref': request.tournament.preferences.by_name(),
            'current_round': current_round,
        })
        if hasattr(request, 'round'):
            context['round'] = request.round

    return context

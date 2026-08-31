from django.core.cache import cache
from django.shortcuts import get_object_or_404

from tournaments.models import Round, Tournament


class DebateMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

        if 'tournament_slug' in view_kwargs and request.path.split('/')[1] != 'api':
            tenant = getattr(request, 'tenant', None)
            tenant_prefix = f"t{getattr(tenant, 'id', 0)}_"
            cached_key = f"{tenant_prefix}{view_kwargs['tournament_slug']}_object"
            cached_tournament_object = cache.get(cached_key)

            if cached_tournament_object:
                request.tournament = cached_tournament_object
            else:
                if tenant:
                    request.tournament = get_object_or_404(
                        Tournament,
                        slug=view_kwargs['tournament_slug'],
                        tenant=tenant
                    )
                else:
                    request.tournament = get_object_or_404(
                        Tournament,
                        slug=view_kwargs['tournament_slug']
                    )
                cache.set(cached_key, request.tournament, None)

            if 'round_seq' in view_kwargs:
                cached_key = f"{tenant_prefix}{view_kwargs['tournament_slug']}_{view_kwargs['round_seq']}_object"
                cached_round_object = cache.get(cached_key)
                if cached_round_object:
                    request.round = cached_round_object
                else:
                    request.round = get_object_or_404(
                        Round,
                        tournament=request.tournament,
                        seq=view_kwargs['round_seq'])
                    cache.set(cached_key, request.round, None)

        return None

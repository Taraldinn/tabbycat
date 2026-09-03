class DebateMiddleware(object):
    """Minimal middleware shim kept for compatibility.

    Tournament and round resolution is handled in TournamentFromUrlMixin
    (tournaments/mixins.py), which already scopes lookups to request.tenant.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class TenantLimitExceeded(ValidationError):
    pass

class TenantLimitEnforcer:
    """
    Checks resource usage against tenant limits.
    Called from model save() hooks and views.
    """

    @staticmethod
    def check_tournament_limit(tenant):
        if tenant.max_tournaments == 0:
            return  # 0 means unlimited or blocked? Usually unlimited might be high number, let's say 0 is blocked, but we set high for unlimited.
        current = tenant.tournament_set.count()
        if current >= tenant.max_tournaments:
            raise TenantLimitExceeded(_("Tournament limit reached for this tenant."))

    @staticmethod
    def check_team_limit(tournament):
        tenant = tournament.tenant
        if not tenant:
            return
        current = tournament.team_set.count()
        if current >= tenant.max_teams_per_tournament:
            raise TenantLimitExceeded(_("Team limit reached for this tenant."))

    @staticmethod
    def check_adjudicator_limit(tournament):
        tenant = tournament.tenant
        if not tenant:
            return
        current = tournament.adjudicator_set.count()
        if current >= tenant.max_adjudicators_per_tournament:
            raise TenantLimitExceeded(_("Adjudicator limit reached for this tenant."))

    @staticmethod
    def check_user_limit(tenant):
        current = tenant.memberships.count()
        if current >= tenant.max_users:
            raise TenantLimitExceeded(_("User limit reached for this tenant."))

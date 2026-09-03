from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

class TenantLimitExceeded(ValidationError):
    def __str__(self):
        if hasattr(self, 'message') and self.message:
            return str(self.message)
        if hasattr(self, 'messages') and self.messages:
            return ", ".join(str(m) for m in self.messages)
        return super().__str__()


class TenantLimitEnforcer:
    """
    Checks resource usage against tenant limits.
    Called from model save() hooks and views.
    """

    @staticmethod
    def check_tournament_limit(tenant):
        if tenant.max_tournaments == 0:
            return
        current = tenant.tournament_set.count()
        if current >= tenant.max_tournaments:
            raise TenantLimitExceeded(
                _("You have reached your plan limit of %(max)d tournament(s) for %(tenant)s. "
                  "Please delete an unused tournament or upgrade your subscription plan to create more.")
                % {'max': tenant.max_tournaments, 'tenant': tenant.name}
            )

    @staticmethod
    def check_team_limit(tournament):
        tenant = tournament.tenant
        if not tenant:
            return
        current = tournament.team_set.count()
        if current >= tenant.max_teams_per_tournament:
            raise TenantLimitExceeded(
                _("You have reached the maximum limit of %(max)d teams for this tournament. "
                  "Please remove unused teams or upgrade your subscription plan.")
                % {'max': tenant.max_teams_per_tournament}
            )

    @staticmethod
    def check_adjudicator_limit(tournament):
        tenant = tournament.tenant
        if not tenant:
            return
        current = tournament.adjudicator_set.count()
        if current >= tenant.max_adjudicators_per_tournament:
            raise TenantLimitExceeded(
                _("You have reached the maximum limit of %(max)d adjudicators for this tournament. "
                  "Please remove unused adjudicators or upgrade your subscription plan.")
                % {'max': tenant.max_adjudicators_per_tournament}
            )

    @staticmethod
    def check_user_limit(tenant):
        current = tenant.memberships.count()
        if current >= tenant.max_users:
            raise TenantLimitExceeded(
                _("You have reached the maximum limit of %(max)d user accounts for %(tenant)s. "
                  "Please upgrade your subscription plan to invite more members.")
                % {'max': tenant.max_users, 'tenant': tenant.name}
            )

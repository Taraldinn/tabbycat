from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

RESERVED_SLUGS = [
    'admin', 'www', 'api', 'static', 'media', 'mail', 'smtp',
    'ftp', 'ssh', 'ns1', 'ns2', 'cdn', 'assets', 'app',
    'staging', 'dev', 'test', 'demo', 'help', 'support',
    'billing', 'status', 'blog', 'docs',
]

def validate_tenant_slug(value):
    if value.lower() in RESERVED_SLUGS:
        raise ValidationError(_("%(value)s is a reserved subdomain."), params={'value': value})

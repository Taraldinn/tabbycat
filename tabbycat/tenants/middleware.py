from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect
from .models import Tenant
from .utils import set_current_tenant

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not getattr(settings, 'MULTI_TENANT_MODE', False):
            set_current_tenant(None)
            return self.get_response(request)

        host = request.get_host().split(':')[0].lower()
        
        # Build set of recognized base domains
        configured_domains = {
            getattr(settings, 'TENANT_BASE_DOMAIN', ''),
            getattr(settings, 'TABBYCAT_BASE_DOMAIN', ''),
            'shebafi.xyz',
            'tabbycatbd.com',
        }
        base_domains = {d.strip().lower() for d in configured_domains if d and d.strip()}

        request.tenant = None
        request.is_platform_admin = False

        if host in base_domains or host in ('localhost', '127.0.0.1', '0.0.0.0', 'testserver'):
            # Landing page / base domain — no tenant
            pass
        elif host.endswith('.onrender.com'):
            # Render's own internal hostname (e.g. tabbycat-web.onrender.com)
            # Treat as landing/admin — no tenant isolation needed
            pass
        elif host.startswith('www.'):
            bare = host[4:]
            if bare in base_domains or bare == 'localhost':
                # Redirect www to bare domain preserving path
                return redirect(f"{request.scheme}://{bare}{request.get_full_path()}", permanent=True)
            else:
                # Custom domain with www (e.g. www.debates.org)
                try:
                    request.tenant = Tenant.objects.get(custom_domain=host, is_active=True)
                except Tenant.DoesNotExist:
                    try:
                        request.tenant = Tenant.objects.get(custom_domain=bare, is_active=True)
                    except Tenant.DoesNotExist:
                        raise Http404("Tenant custom domain does not exist or is inactive.")
        elif host.startswith('admin.'):
            bare = host[6:]
            if bare in base_domains or bare == 'localhost':
                # Platform Admin
                request.is_platform_admin = True
            else:
                try:
                    request.tenant = Tenant.objects.get(custom_domain=host, is_active=True)
                except Tenant.DoesNotExist:
                    raise Http404("Tenant custom domain does not exist or is inactive.")
        else:
            # Tenant Subdomain check
            matched_base = None
            if host.endswith('.localhost'):
                matched_base = '.localhost'
            else:
                for b_domain in base_domains:
                    if host.endswith(f'.{b_domain}'):
                        matched_base = f'.{b_domain}'
                        break

            if matched_base:
                slug = host[:-len(matched_base)]
                try:
                    request.tenant = Tenant.objects.get(slug=slug, is_active=True)
                except Tenant.DoesNotExist:
                    raise Http404("Tenant does not exist or is inactive.")
            else:
                # Custom Domain
                try:
                    request.tenant = Tenant.objects.get(custom_domain=host, is_active=True)
                except Tenant.DoesNotExist:
                    raise Http404("Tenant custom domain does not exist or is inactive.")

        set_current_tenant(request.tenant)
        response = self.get_response(request)
        
        # Clear tenant for thread cleanup
        set_current_tenant(None)
        
        return response

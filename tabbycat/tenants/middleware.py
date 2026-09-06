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
        base_domain = getattr(settings, 'TENANT_BASE_DOMAIN', 'tabbycatbd.com').lower()

        request.tenant = None
        request.is_platform_admin = False

        if host in (base_domain, 'localhost', '127.0.0.1', '0.0.0.0', 'testserver'):
            # Landing page / base domain — no tenant
            pass
        elif host.endswith('.onrender.com'):
            # Render's own internal hostname (e.g. tabbycat-web.onrender.com)
            # Treat as landing/admin — no tenant isolation needed
            pass
        elif host in (f'www.{base_domain}', 'www.localhost'):
            # Redirect www to bare domain
            return redirect(f"{request.scheme}://{base_domain}/", permanent=True)
        elif host in (f'admin.{base_domain}', 'admin.localhost'):
            # Platform Admin
            request.is_platform_admin = True
        elif host.endswith(f'.{base_domain}') or host.endswith('.localhost'):
            # Tenant Subdomain
            suffix = f'.{base_domain}' if host.endswith(f'.{base_domain}') else '.localhost'
            slug = host.replace(suffix, '')
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

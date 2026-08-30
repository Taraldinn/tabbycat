def tenant_context(request):
    """
    Adds the current tenant to the context of all templates.
    """
    return {
        'tenant': getattr(request, 'tenant', None),
        'is_platform_admin': getattr(request, 'is_platform_admin', False)
    }

import threading

_thread_locals = threading.local()

def set_current_tenant(tenant):
    """Sets the tenant for the current request thread."""
    _thread_locals.tenant = tenant

def get_current_tenant():
    """Gets the tenant for the current request thread."""
    return getattr(_thread_locals, 'tenant', None)

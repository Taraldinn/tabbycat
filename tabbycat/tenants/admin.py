from django.contrib import admin
from .models import Tenant, TenantMembership

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'owner', 'custom_domain', 'is_active', 'created_at')
    search_fields = ('name', 'slug', 'custom_domain', 'owner__username', 'owner__email')
    list_filter = ('is_active', 'created_at')

@admin.register(TenantMembership)
class TenantMembershipAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'user', 'role', 'joined_at')
    search_fields = ('tenant__name', 'user__username', 'user__email')
    list_filter = ('role', 'joined_at')


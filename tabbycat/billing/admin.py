from django.contrib import admin
from .models import Plan, Subscription, Payment

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price_bdt', 'billing_period', 'max_tournaments', 'max_users', 'is_active')
    search_fields = ('name', 'slug')
    list_filter = ('billing_period', 'is_active')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'plan', 'status', 'started_at', 'current_period_end')
    search_fields = ('tenant__name', 'plan__name')
    list_filter = ('status', 'plan')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('subscription', 'amount_bdt', 'method', 'status', 'sender_phone', 'transaction_id', 'created_at')
    search_fields = ('subscription__tenant__name', 'transaction_id', 'sender_phone')
    list_filter = ('status', 'method', 'created_at')

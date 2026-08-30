from django.contrib import admin
from .models import EmailConfig, SMSConfig, MessageLog

@admin.register(EmailConfig)
class EmailConfigAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'backend', 'host', 'port')

@admin.register(SMSConfig)
class SMSConfigAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'provider', 'sender_id')

@admin.register(MessageLog)
class MessageLogAdmin(admin.ModelAdmin):
    list_display = ('tenant', 'type', 'recipient', 'status', 'sent_at')
    list_filter = ('type', 'status', 'sent_at')
    search_fields = ('recipient', 'subject')

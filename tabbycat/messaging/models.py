from django.db import models
from django.conf import settings

class EmailConfig(models.Model):
    tenant = models.OneToOneField('tenants.Tenant', on_delete=models.CASCADE, related_name='email_config', null=True, blank=True)
    backend = models.CharField(max_length=50, default='django.core.mail.backends.smtp.EmailBackend')
    host = models.CharField(max_length=255, blank=True)
    port = models.PositiveIntegerField(default=587)
    use_tls = models.BooleanField(default=True)
    use_ssl = models.BooleanField(default=False)
    username = models.CharField(max_length=255, blank=True)
    password = models.CharField(max_length=255, blank=True)
    default_from_email = models.EmailField(blank=True)
    
    def __str__(self):
        return f"Email Config ({self.tenant.name if self.tenant else 'Global'})"

class SMSConfig(models.Model):
    class Provider(models.TextChoices):
        TWILIO = 'twilio', 'Twilio'
        BULKSMSBD = 'bulksmsbd', 'BulkSMSBD'
        SSLWIRELESS = 'sslwireless', 'SSL Wireless'
        
    tenant = models.OneToOneField('tenants.Tenant', on_delete=models.CASCADE, related_name='sms_config', null=True, blank=True)
    provider = models.CharField(max_length=20, choices=Provider.choices, default=Provider.TWILIO)
    api_key = models.CharField(max_length=255, blank=True)
    api_secret = models.CharField(max_length=255, blank=True)
    sender_id = models.CharField(max_length=50, blank=True)
    
    def __str__(self):
        return f"SMS Config ({self.tenant.name if self.tenant else 'Global'})"

class MessageLog(models.Model):
    class Type(models.TextChoices):
        EMAIL = 'email', 'Email'
        SMS = 'sms', 'SMS'
        
    class Status(models.TextChoices):
        SENT = 'sent', 'Sent'
        FAILED = 'failed', 'Failed'
        
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.CASCADE, related_name='message_logs', null=True, blank=True)
    type = models.CharField(max_length=10, choices=Type.choices)
    recipient = models.CharField(max_length=255)
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices)
    error_message = models.TextField(blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.get_type_display()} to {self.recipient} at {self.sent_at}"

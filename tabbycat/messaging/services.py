from django.core.mail import get_connection, EmailMultiAlternatives
from django.conf import settings
from .models import EmailConfig, SMSConfig, MessageLog
import logging
import requests

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self, tenant=None):
        self.tenant = tenant
        self.config = EmailConfig.objects.filter(tenant=tenant).first() or EmailConfig.objects.filter(tenant__isnull=True).first()

    def get_connection(self):
        if not self.config:
            return get_connection()
        return get_connection(
            backend=self.config.backend,
            host=self.config.host,
            port=self.config.port,
            username=self.config.username,
            password=self.config.password,
            use_tls=self.config.use_tls,
            use_ssl=self.config.use_ssl,
        )

    def send(self, to, subject, body_html, body_text=""):
        from_email = self.config.default_from_email if self.config else settings.DEFAULT_FROM_EMAIL
        msg = EmailMultiAlternatives(subject, body_text, from_email, [to], connection=self.get_connection())
        if body_html:
            msg.attach_alternative(body_html, "text/html")
        
        try:
            msg.send()
            MessageLog.objects.create(
                tenant=self.tenant, type=MessageLog.Type.EMAIL, recipient=to,
                subject=subject, body=body_html or body_text, status=MessageLog.Status.SENT
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            MessageLog.objects.create(
                tenant=self.tenant, type=MessageLog.Type.EMAIL, recipient=to,
                subject=subject, body=body_html or body_text, status=MessageLog.Status.FAILED,
                error_message=str(e)
            )
            return False

class SMSService:
    def __init__(self, tenant=None):
        self.tenant = tenant
        self.config = SMSConfig.objects.filter(tenant=tenant).first() or SMSConfig.objects.filter(tenant__isnull=True).first()

    def send(self, to_phone, message):
        if not self.config:
            logger.error("No SMS config found")
            return False
            
        try:
            if self.config.provider == SMSConfig.Provider.TWILIO:
                self._send_twilio(to_phone, message)
            elif self.config.provider == SMSConfig.Provider.BULKSMSBD:
                self._send_bulksmsbd(to_phone, message)
            elif self.config.provider == SMSConfig.Provider.SSLWIRELESS:
                self._send_sslwireless(to_phone, message)
                
            MessageLog.objects.create(
                tenant=self.tenant, type=MessageLog.Type.SMS, recipient=to_phone,
                body=message, status=MessageLog.Status.SENT
            )
            return True
        except Exception as e:
            logger.error(f"Failed to send SMS to {to_phone}: {e}")
            MessageLog.objects.create(
                tenant=self.tenant, type=MessageLog.Type.SMS, recipient=to_phone,
                body=message, status=MessageLog.Status.FAILED, error_message=str(e)
            )
            return False

    def _send_twilio(self, to_phone, message):
        # Implementation using twilio client
        pass

    def _send_bulksmsbd(self, to_phone, message):
        payload = {
            "api_key": self.config.api_key,
            "senderid": self.config.sender_id,
            "number": to_phone,
            "message": message
        }
        response = requests.post("http://bulksmsbd.net/api/smsapi", data=payload)
        response.raise_for_status()
        
    def _send_sslwireless(self, to_phone, message):
        # SSL Wireless implementation
        pass

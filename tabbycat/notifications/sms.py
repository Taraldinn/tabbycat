import json
import logging
import re
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.utils.module_loading import import_string
from django.utils.translation import gettext_lazy as _

logger = logging.getLogger(__name__)


def normalize_phone_number(phone: str) -> str:
    """
    Normalizes phone numbers to standard format (e.g. +88017XXXXXXXX or +1XXXXXXXXXX).
    """
    if not phone:
        return ""
    # Strip spaces, dashes, parentheses
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    
    # If Bangladesh local format (e.g. 017XXXXXXXX), prefix with country code +88
    if re.match(r'^01[3-9]\d{8}$', cleaned):
        return f"+88{cleaned}"
    elif re.match(r'^8801[3-9]\d{8}$', cleaned):
        return f"+{cleaned}"
    elif cleaned.startswith('+'):
        return cleaned
    
    return cleaned


class BaseSMSBackend:
    """Abstract base class for SMS notification providers."""
    def send(self, to: str, message: str) -> bool:
        raise NotImplementedError("Subclasses must implement send(to, message)")


class ConsoleSMSBackend(BaseSMSBackend):
    """Logs SMS dispatches to console/logger for development and testing."""
    def send(self, to: str, message: str) -> bool:
        normalized = normalize_phone_number(to)
        logger.info(f"[SMS CONSOLE DISPATCH] To: {normalized} | Message: {message}")
        print(f"\n📱 [SMS DISPATCH] To: {normalized}\nMessage:\n{message}\n" + "-" * 40)
        return True


class GreenwebSMSBackend(BaseSMSBackend):
    """Greenweb Bangladesh SMS Gateway."""
    API_URL = "https://api.greenweb.com.bd/api.php"

    def send(self, to: str, message: str) -> bool:
        token = getattr(settings, 'SMS_API_KEY', '')
        if not token:
            logger.error("Greenweb SMS token is not configured in settings.SMS_API_KEY")
            return False

        normalized = normalize_phone_number(to).replace('+', '')
        params = urllib.parse.urlencode({
            'token': token,
            'to': normalized,
            'message': message,
        })

        try:
            req = urllib.request.Request(f"{self.API_URL}?{params}", headers={'User-Agent': 'Tabbycat/2.11'})
            with urllib.request.urlopen(req, timeout=10) as response:
                resp_text = response.read().decode('utf-8')
                logger.info(f"Greenweb SMS response for {normalized}: {resp_text}")
                return "Ok" in resp_text or "100" in resp_text
        except Exception as e:
            logger.error(f"Failed to send SMS via Greenweb to {normalized}: {e}")
            return False


class SSLWirelessSMSBackend(BaseSMSBackend):
    """SSL Wireless Bangladesh SMS Gateway."""
    API_URL = "https://smsplus.sslwireless.com/api/v3/send-sms"

    def send(self, to: str, message: str) -> bool:
        api_token = getattr(settings, 'SMS_API_KEY', '')
        sid = getattr(settings, 'SMS_SENDER_ID', 'Tabbycat')
        if not api_token:
            logger.error("SSL Wireless API key is not configured in settings.SMS_API_KEY")
            return False

        normalized = normalize_phone_number(to).replace('+', '')
        payload = json.dumps({
            "api_token": api_token,
            "sid": sid,
            "msisdn": normalized,
            "sms": message,
            "csms_id": f"tc_{int(urllib.request.time.time())}"
        }).encode('utf-8')

        try:
            req = urllib.request.Request(
                self.API_URL,
                data=payload,
                headers={'Content-Type': 'application/json', 'User-Agent': 'Tabbycat/2.11'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                resp_text = response.read().decode('utf-8')
                logger.info(f"SSL Wireless SMS response for {normalized}: {resp_text}")
                return "SUCCESS" in resp_text.upper()
        except Exception as e:
            logger.error(f"Failed to send SMS via SSL Wireless to {normalized}: {e}")
            return False


class GenericWebhookSMSBackend(BaseSMSBackend):
    """Generic HTTP Webhook SMS Gateway."""
    def send(self, to: str, message: str) -> bool:
        webhook_url = getattr(settings, 'SMS_WEBHOOK_URL', '')
        if not webhook_url:
            logger.error("SMS_WEBHOOK_URL is not set")
            return False

        normalized = normalize_phone_number(to)
        payload = json.dumps({"to": normalized, "message": message}).encode('utf-8')
        try:
            req = urllib.request.Request(
                webhook_url,
                data=payload,
                headers={'Content-Type': 'application/json', 'User-Agent': 'Tabbycat/2.11'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status in (200, 201, 202)
        except Exception as e:
            logger.error(f"Failed to send SMS via Webhook to {normalized}: {e}")
            return False


def get_sms_backend() -> BaseSMSBackend:
    """Instantiates and returns the configured SMS backend."""
    backend_path = getattr(settings, 'SMS_BACKEND', 'notifications.sms.ConsoleSMSBackend')
    try:
        backend_cls = import_string(backend_path)
        return backend_cls()
    except Exception as e:
        logger.warning(f"Could not load SMS backend '{backend_path}', falling back to Console: {e}")
        return ConsoleSMSBackend()


def send_participant_sms(person, message_text: str, bulk_notification=None) -> bool:
    """
    Sends an SMS notification to a tournament participant/adjudicator (Person).
    Records sent record in SentMessage with method='s'.
    """
    from .models import SentMessage

    if not getattr(person, 'phone', None):
        logger.warning(f"Person '{person}' has no phone number registered. SMS skipped.")
        return False

    backend = get_sms_backend()
    success = backend.send(person.phone, message_text)

    if success and bulk_notification:
        try:
            SentMessage.objects.create(
                recipient=person,
                method=SentMessage.METHOD_TYPE_SMS,
                notification=bulk_notification,
                context={'sms_body': message_text, 'phone': person.phone}
            )
        except Exception as e:
            logger.error(f"Error logging sent SMS message: {e}")

    return success

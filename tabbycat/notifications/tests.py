from django.contrib.auth import get_user_model
from django.test import TestCase

from notifications.models import BulkNotification, SentMessage
from notifications.sms import (
    ConsoleSMSBackend,
    get_sms_backend,
    normalize_phone_number,
    send_participant_sms,
)
from participants.models import Institution, Person
from tenants.models import Tenant
from tournaments.models import Tournament

User = get_user_model()


class SMSNotificationTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='sms_admin', password='Password123!')
        self.tenant = Tenant.objects.create(name='SMS Org', slug='sms-org', owner=self.user)
        self.tournament = Tournament.objects.create(
            name='National Debates',
            slug='national-debates',
            tenant=self.tenant
        )
        self.institution = Institution.objects.create(
            name='Dhaka University',
            code='DU',
            tenant=self.tenant
        )
        self.person = Person.objects.create(
            name='Tanvir Rahman',
            email='tanvir@example.com',
            phone='01712345678'
        )

    def test_phone_number_normalization(self):
        # Local Bangladesh format
        self.assertEqual(normalize_phone_number('01712345678'), '+8801712345678')
        # Already prefixed with 88
        self.assertEqual(normalize_phone_number('8801712345678'), '+8801712345678')
        # International with +
        self.assertEqual(normalize_phone_number('+14155552671'), '+14155552671')
        # Formatting with spaces and dashes
        self.assertEqual(normalize_phone_number('018-12 345 679'), '+8801812345679')

    def test_console_sms_backend(self):
        backend = ConsoleSMSBackend()
        result = backend.send('01712345678', 'Test Round 1 Pairing: Team A vs Team B')
        self.assertTrue(result)

    def test_get_sms_backend(self):
        backend = get_sms_backend()
        self.assertIsInstance(backend, ConsoleSMSBackend)

    def test_send_participant_sms_logging(self):
        bulk_notif = BulkNotification.objects.create(
            tournament=self.tournament,
            event=BulkNotification.EventType.MOTIONS,
            subject_template="Motion Released",
            body_template="THW adopt renewable energy."
        )

        success = send_participant_sms(
            person=self.person,
            message_text="Round 1 Motion: THW adopt renewable energy.",
            bulk_notification=bulk_notif
        )
        self.assertTrue(success)

        # Verify SentMessage record created
        msg = SentMessage.objects.filter(recipient=self.person).first()
        self.assertIsNotNone(msg)
        self.assertEqual(msg.method, SentMessage.METHOD_TYPE_SMS)
        self.assertEqual(msg.notification, bulk_notif)
        self.assertEqual(msg.context.get('phone'), '01712345678')

    def test_send_participant_without_phone_skips(self):
        person_no_phone = Person.objects.create(
            name='No Phone User',
            email='nophone@example.com',
            phone=''
        )
        success = send_participant_sms(person_no_phone, "Hello!")
        self.assertFalse(success)

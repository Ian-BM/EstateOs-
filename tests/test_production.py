import io
from django.test import TestCase,override_settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.contrib.auth.models import User
from properties.models import Property

class ShowcaseTests(TestCase):
    @override_settings(DEBUG=False,SECURE_SSL_REDIRECT=False)
    def test_public_showcase_has_no_default_login_accounts(self):
        call_command('seed_demo',showcase_only=True,stdout=io.StringIO())
        self.assertEqual(Property.objects.count(),25)
        self.assertEqual(User.objects.count(),10)
        self.assertFalse(User.objects.filter(is_active=True).exists())
        self.assertTrue(all(not u.has_usable_password() for u in User.objects.all()))
        self.assertFalse(self.client.login(username='demo_admin',password='EstateDemo2026!'))
        self.assertEqual(self.client.get('/').status_code,200)
        call_command('seed_demo',showcase_only=True,stdout=io.StringIO())
        self.assertEqual(User.objects.count(),10)
    @override_settings(DEBUG=False)
    def test_showcase_refuses_existing_active_demo_username(self):
        User.objects.create_user('demo_admin',password='existing-private-password')
        with self.assertRaises(CommandError):
            call_command('seed_demo',showcase_only=True,stdout=io.StringIO())
        self.assertEqual(Property.objects.count(),0)

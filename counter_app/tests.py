# counter_app/tests.py

from django.test import TestCase, Client
from django.urls import reverse
from django.test.utils import override_settings
from .models import ViewCount, Visitor

@override_settings(MIDDLEWARE=[
    # Include necessary middleware
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django_user_agents.middleware.UserAgentMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
])
class HomeViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Ensure the ViewCount object exists
        ViewCount.objects.get_or_create(pk=1)

    def test_view_count_increments(self):
        initial_count = ViewCount.objects.get(pk=1).total_views
        response = self.client.get(reverse('home'))
        new_count = ViewCount.objects.get(pk=1).total_views
        self.assertEqual(new_count, initial_count + 1)
        self.assertEqual(response.status_code, 200)

    def test_visitor_record_created(self):
        initial_visitors = Visitor.objects.count()
        self.client.get(reverse('home'))
        new_visitors = Visitor.objects.count()
        self.assertEqual(new_visitors, initial_visitors + 1)

    def test_device_type_detection(self):
        # Test with a mobile user agent
        mobile_ua = (
            'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) '
            'AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'
        )
        self.client.get(reverse('home'), HTTP_USER_AGENT=mobile_ua)
        visitor = Visitor.objects.last()
        self.assertEqual(visitor.device_type, 'Mobile')

        # Test with a desktop user agent
        desktop_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
        self.client.get(reverse('home'), HTTP_USER_AGENT=desktop_ua)
        visitor = Visitor.objects.last()
        self.assertEqual(visitor.device_type, 'Desktop')

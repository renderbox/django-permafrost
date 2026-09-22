from django.test import TestCase
from django.urls import reverse

# from django.core.management import call_command

# class SystemTests(TestCase):

#     def test_for_missing_migrations(self):
#         """ If no migrations are detected as needed, `result`
#         will be `None`. In all other cases, the call will fail,
#         alerting your team that someone is trying to make a
#         change that requires a migration and that migration is
#         absent.
#         Based on example by Scott Hacker
#         """

#         result = call_command("makemigrations", check=True, dry_run=True)
#         self.assertIsNone(result)


class DevelopmentProjectTests(TestCase):
    def test_home_page_renders(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)

    def test_login_page_renders(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="username"')
        self.assertContains(response, 'name="password"')

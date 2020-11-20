from django.test import TestCase
from django.core.management import call_command

class SystemTests(TestCase):

    def test_for_missing_migrations(self):
        """ If no migrations are detected as needed, `result`
        will be `None`. In all other cases, the call will fail,
        alerting your team that someone is trying to make a
        change that requires a migration and that migration is
        absent.
        Based on example by Scott Hacker
        """

        result = call_command("makemigrations", check=True, dry_run=True)
        self.assertIsNone(result)

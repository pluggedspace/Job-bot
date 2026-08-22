from django.test import TestCase
from bot.models import User


class UserModelTests(TestCase):
    def test_get_default_user(self):
        user = User.get_default_user()
        self.assertEqual(user.user_id, "default")
        self.assertEqual(user.platform_type, "api")

    def test_get_default_user_is_idempotent(self):
        first = User.get_default_user()
        second = User.get_default_user()
        self.assertEqual(first.pk, second.pk)

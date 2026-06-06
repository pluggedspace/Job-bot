from django.test import SimpleTestCase
from bot.functions.jobs import parse_relative_date
import datetime

class UtilsTest(SimpleTestCase):
    def test_parse_relative_date_hours(self):
        date_str = "15 hours ago"
        result = parse_relative_date(date_str)
        self.assertIsInstance(result, datetime.datetime)
        
        # Should be roughly 15 hours before now
        now = datetime.datetime.utcnow()
        expected = now - datetime.timedelta(hours=15)
        diff = abs((now - result).total_seconds() - 15 * 3600)
        self.assertLess(diff, 60) # within 1 minute

    def test_parse_relative_date_days(self):
        date_str = "5 days ago"
        result = parse_relative_date(date_str)
        self.assertIsInstance(result, datetime.datetime)
        
        now = datetime.datetime.utcnow()
        expected = now - datetime.timedelta(days=5)
        diff = abs((now - result).total_seconds() - 5 * 24 * 3600)
        self.assertLess(diff, 60)

    def test_parse_relative_date_iso(self):
        date_str = "2026-04-19T06:08:29"
        result = parse_relative_date(date_str)
        self.assertIsInstance(result, datetime.datetime)
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 4)
        self.assertEqual(result.day, 19)

    def test_parse_relative_date_invalid(self):
        self.assertIsNone(parse_relative_date("invalid date"))
        self.assertIsNone(parse_relative_date(None))
        self.assertIsNone(parse_relative_date(123))

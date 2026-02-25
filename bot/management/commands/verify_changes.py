from django.core.management.base import BaseCommand
import sys

class Command(BaseCommand):
    help = 'Verify that recent code changes (imports, Prompts, etc.) are valid.'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Starting System Verification...")
        
        has_error = False

        # 1. Test PROMPTS & IMPROVE module
        try:
            from bot.improve import generate_cover_letter, review_cv
            self.stdout.write(self.style.SUCCESS("✅ bot.improve imported"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ bot.improve FAILED: {e}"))
            has_error = True

        # 2. Test INTERVIEW module
        try:
            from bot.services.interview import handle_interview_practice
            self.stdout.write(self.style.SUCCESS("✅ bot.services.interview imported"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ bot.services.interview FAILED: {e}"))
            has_error = True

        # 3. Test CV BUILDER module
        try:
            from bot.cv_builder import get_cv_handler
            self.stdout.write(self.style.SUCCESS("✅ bot.cv_builder imported"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ bot.cv_builder FAILED: {e}"))
            has_error = True

        # 4. Test TASKS module (fixes for imports)
        try:
            from bot.tasks import check_alerts
            self.stdout.write(self.style.SUCCESS("✅ bot.tasks imported"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ bot.tasks FAILED: {e}"))
            has_error = True

        # 5. DB Check
        from django.conf import settings
        db_host = settings.DATABASES['default']['HOST']
        self.stdout.write(f"ℹ️ Database Configured Host: {db_host}")
        
        if not has_error:
            self.stdout.write(self.style.SUCCESS("\n✨ All modules verified successfully! System is consistent."))
        else:
            self.stdout.write(self.style.ERROR("\n💥 Verification failed. See errors above."))
            sys.exit(1)

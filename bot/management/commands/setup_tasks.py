from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule

class Command(BaseCommand):
    help = 'Setup system periodic tasks'

    def handle(self, *args, **kwargs):
        # Create Schedule
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=30,
            period='minutes',
        )
        
        # Create or Update Task
        task, created = PeriodicTask.objects.update_or_create(
            name='Check Job Alerts (Every 30m)',
            defaults={
                'interval': schedule,
                'task': 'bot.tasks.check_alerts',
                'enabled': True,
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Created task: {task.name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Updated task: {task.name}'))

from django.db import migrations

def create_periodic_task(apps, schema_editor):
    try:
        IntervalSchedule = apps.get_model('django_celery_beat', 'IntervalSchedule')
        PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')
        
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=30,
            period='minutes',
        )
        
        # Check if task already exists to avoid duplication if migration runs multiple times (though RunPython is usually once)
        if not PeriodicTask.objects.filter(task='check_alerts').exists():
            PeriodicTask.objects.create(
                interval=schedule,
                name='Check Job Alerts (Every 30m)',
                task='check_alerts',
                enabled=True,
            )
    except LookupError:
        # In case django_celery_beat is not installed or available for some reason
        pass

class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0009_tenantuser_payment_provider'),
        ('django_celery_beat', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_periodic_task),
    ]

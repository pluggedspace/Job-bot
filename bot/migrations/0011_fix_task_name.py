from django.db import migrations

def fix_task_name(apps, schema_editor):
    try:
        PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')
        
        # Update the task name to the full path
        tasks = PeriodicTask.objects.filter(task='check_alerts')
        for task in tasks:
            task.task = 'bot.tasks.check_alerts'
            task.save()
            
    except LookupError:
        pass

class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0010_setup_periodic_tasks'),
    ]

    operations = [
        migrations.RunPython(fix_task_name),
    ]

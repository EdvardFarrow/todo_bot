from django.core.management.base import BaseCommand
from django_celery_beat.models import IntervalSchedule, PeriodicTask


class Command(BaseCommand):
    help = "Creates periodic tasks in the database (Celery Beat)"

    def handle(self, *args, **kwargs):
        try:
            schedule, created = IntervalSchedule.objects.get_or_create(
                every=10,
                period=IntervalSchedule.SECONDS,
            )
        except IntervalSchedule.MultipleObjectsReturned:
            schedules = IntervalSchedule.objects.filter(
                every=10,
                period=IntervalSchedule.SECONDS,
            ).order_by("id")

            schedule = schedules.first()

            for dup in schedules[1:]:
                dup.delete()

            created = False
            self.stdout.write(self.style.WARNING("⚠️ Duplicate schedules found (10 sec). Unnecessary ones removed."))

        task_name = "Check Deadlines (Every 10s)"

        task_func = "apps.tasks.tasks.check_deadlines"

        task, created = PeriodicTask.objects.get_or_create(
            name=task_name,
            defaults={
                "interval": schedule,
                "task": task_func,
                "enabled": True,
            },
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Task "{task_name}" created!'))
        else:
            task.interval = schedule
            task.task = task_func
            task.enabled = True
            task.save()
            self.stdout.write(self.style.SUCCESS(f'🔄 Task "{task_name}" updated/already exists.'))

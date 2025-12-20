from django.core.management.base import BaseCommand
from django_celery_beat.models import IntervalSchedule, CrontabSchedule, PeriodicTask


class Command(BaseCommand):
    help = "Creates periodic tasks in the database (Celery Beat)"

    def handle(self, *args, **kwargs):
        self.setup_interval_task()
        self.setup_crontab_task()

    def setup_interval_task(self):
        """Setting up a deadline check task (every 10 seconds)"""
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
            self.stdout.write(self.style.WARNING("⚠️ Duplicate interval schedules found. Removed extras."))

        task_name = "Check Deadlines (Every 10s)"
        task_func = "apps.tasks.tasks.check_deadlines"

        self._create_or_update_task(task_name, task_func, interval=schedule)

    def setup_crontab_task(self):
        """Setting up a morning newsletter (every day at 7:00)"""
        try:
            schedule, created = CrontabSchedule.objects.get_or_create(
                minute="0",
                hour="7",
                day_of_week="*",
                day_of_month="*",
                month_of_year="*",
            )
        except CrontabSchedule.MultipleObjectsReturned:
            schedules = CrontabSchedule.objects.filter(
                minute="0", hour="7"
            ).order_by("id")
            schedule = schedules.first()
            for dup in schedules[1:]:
                dup.delete()
            self.stdout.write(self.style.WARNING("⚠️ Duplicate crontab schedules found. Removed extras."))

        task_name = "Daily Morning Briefing (7:00 AM)"
        task_func = "apps.tasks.tasks.send_daily_morning_briefing"

        self._create_or_update_task(task_name, task_func, crontab=schedule)

    def _create_or_update_task(self, name, func, interval=None, crontab=None):
        """A generic method for creating/updating a task"""
        defaults = {
            "task": func,
            "enabled": True,
        }
        if interval:
            defaults["interval"] = interval
            defaults["crontab"] = None 
        if crontab:
            defaults["crontab"] = crontab
            defaults["interval"] = None 

        task, created = PeriodicTask.objects.get_or_create(
            name=name,
            defaults=defaults,
        )

        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Task "{name}" created!'))
        else:
            task.task = func
            task.enabled = True
            if interval:
                task.interval = interval
                task.crontab = None
            if crontab:
                task.crontab = crontab
                task.interval = None
            task.save()
            self.stdout.write(self.style.SUCCESS(f'🔄 Task "{name}" updated.'))
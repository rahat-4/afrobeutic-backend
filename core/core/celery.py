import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "process-auto-renewals": {
        "task": "apps.billing.tasks.process_auto_renewals",
        "schedule": crontab(hour=0, minute=5),  # daily at 00:05 UTC
    },
    "send-renewal-reminders": {
        "task": "apps.billing.tasks.send_renewal_reminders",
        "schedule": crontab(hour=9, minute=0),  # daily 09:00 UTC — morning reminder
    },
    "send-trial-expiry-warnings": {
        "task": "apps.billing.tasks.send_trial_expiry_warnings",
        "schedule": crontab(hour=9, minute=5),  # daily 09:05 UTC
    },
}

app.conf.timezone = "UTC"

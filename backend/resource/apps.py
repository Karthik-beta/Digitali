from django.apps import AppConfig
from django.core.management import call_command
import sys

class ResourceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'resource'


    def ready(self):
        # Prevent the scheduler from starting during migrations
        if 'runserver' in sys.argv or 'uwsgi' in sys.argv:
            from . import scheduler
            # Delayed scheduler start after migrations are checked/applied
            try:
                call_command('migrate', interactive=False)  # Ensure all migrations are applied
                scheduler.start()
            except Exception as e:
                print(f"Scheduler failed to start: {e}")
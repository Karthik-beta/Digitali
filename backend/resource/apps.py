from django.apps import AppConfig
from django.core.management import call_command
import sys
import os
from dotenv import load_dotenv

# Load the correct environment file
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

class ResourceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'resource'


    def ready(self):
        # Prevent the scheduler from starting during migrations
        if 'runserver' in sys.argv or 'uwsgi' in sys.argv:
            from . import scheduler
            # Delayed scheduler start after migrations are checked/applied
            try:
                if ENVIRONMENT != 'local':
                    call_command('migrate', interactive=False)  # Ensure all migrations are applied
                    call_command('absentees', days=400)
                    call_command('reset_sequences')
                    scheduler.start()
                    print("Scheduler started.")
            except Exception as e:
                print(f"Scheduler failed to start: {e}")
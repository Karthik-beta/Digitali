import logging
from django.db import transaction
from celery import shared_task

from resource.models import Logs, LastLogId
from resource.models import Attendance

# Set up logging
logger = logging.getLogger(__name__)

from django.core.management.base import BaseCommand, CommandError
from resource.models import Logs, LastLogId  # Import your models
from resource.attendance3 import process_logs   # Import the function to execute
from resource.attendance4 import process_attendance_data
from resource.attendance5 import process_missed_punches

class Command(BaseCommand):
    help = 'Processes new logs from the database.'

    def handle(self, *args, **options):
        process_logs()
        # process_attendance_data()
        process_missed_punches()
        self.stdout.write(self.style.SUCCESS('Successfully processed logs.'))

import logging
from django.db import transaction
from celery import shared_task

from resource.models import Logs, LastLogId
from resource.models import Attendance

# Set up logging
logger = logging.getLogger(__name__)

from django.core.management.base import BaseCommand, CommandError
from resource.models import Logs, LastLogId  # Import your models
# from resource.tasks import scan_for_data   # Import the function to execute

from resource.attendance2 import AttendanceProcessor

class Command(BaseCommand):
    help = 'Processes new logs from the database.'

    def handle(self, *args, **options):
        # scan_for_data()
        processor = AttendanceProcessor()
        processor.process_new_logs()
        
        self.stdout.write(self.style.SUCCESS('Successfully processed logs.'))


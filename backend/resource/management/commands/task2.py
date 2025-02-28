import logging
from django.core.management.base import BaseCommand

# Set up logging
logger = logging.getLogger(__name__)

from resource.attendance6 import AttendanceProcessor
# from resource.attendance5 import AttendanceProcessor

class Command(BaseCommand):
    help = 'Processes new logs from the database.'

    def handle(self, *args, **options):
        processor = AttendanceProcessor()
        success = processor.process_new_logs()
        if success:
            print("Attendance logs processed successfully.")
        else:
            print("Attendance log processing failed. Check logs for errors.")



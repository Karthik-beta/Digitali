from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from resource.models import Attendance, Employee
from tqdm import tqdm
from typing import List, Dict, Set
from datetime import date
from collections import defaultdict

from value_config import WEEK_OFF_CONFIG

class Command(BaseCommand):
    help = "Creates new fields in Attendance model and marks absent employees for a given number of days starting from today"
    BATCH_SIZE = 1000  # Number of records to create at once

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Number of days to process starting from today'
        )

    def get_dates_to_process(self, num_days: int) -> List[date]:
        """Generate list of dates to process."""
        today = timezone.now().date()
        return [today - timezone.timedelta(days=i) for i in range(num_days)]

    def get_existing_attendance(self, dates: List[date], employee_ids: List[int]) -> Set[tuple]:
        """Get existing attendance records for the given dates and employees."""
        existing = Attendance.objects.filter(
            logdate__in=dates,
            employeeid_id__in=employee_ids
        ).values_list('employeeid_id', 'logdate')
        return set(map(tuple, existing))

    def create_attendance_objects(self, 
                                employees: List[Employee], 
                                dates: List[date],
                                existing_records: Set[tuple]) -> List[Attendance]:
        """Create attendance objects for bulk insertion."""
        attendance_objects = []
        
        for process_date in dates:
            is_sunday = process_date.weekday() in WEEK_OFF_CONFIG['DEFAULT_WEEK_OFF']
            
            for employee in employees:
                # Skip if attendance already exists
                if (employee.id, process_date) in existing_records:
                    continue
                
                # Create new attendance object
                attendance_objects.append(
                    Attendance(
                        employeeid=employee,
                        logdate=process_date,
                        shift_status='WO' if is_sunday else 'A'
                    )
                )
                
                # If we've reached batch size, yield the current batch
                if len(attendance_objects) >= self.BATCH_SIZE:
                    yield attendance_objects
                    attendance_objects = []
        
        # Yield any remaining objects
        if attendance_objects:
            yield attendance_objects

    @transaction.atomic
    def handle(self, *args, **options):
        num_days = options['days']
        dates = self.get_dates_to_process(num_days)
        
        # Get all employees at once
        employees = list(Employee.objects.all())
        if not employees:
            self.stdout.write(self.style.WARNING("No employees found"))
            return
        
        employee_ids = [emp.id for emp in employees]
        
        # Get existing attendance records
        existing_records = self.get_existing_attendance(dates, employee_ids)
        
        # Calculate total number of records to be created
        total_records = len(dates) * len(employees) - len(existing_records)
        
        with tqdm(total=total_records, desc="Creating attendance records", unit="records") as pbar:
            # Process in batches
            for batch in self.create_attendance_objects(employees, dates, existing_records):
                # Bulk create the batch
                Attendance.objects.bulk_create(batch)
                pbar.update(len(batch))

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully processed attendance for {num_days} days with {len(employees)} employees"
            )
        )
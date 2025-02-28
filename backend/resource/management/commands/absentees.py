from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from resource.models import Attendance, Employee, HolidayList
from tqdm import tqdm
from typing import List, Dict, Set
from datetime import date, timedelta
from collections import defaultdict
from value_config import WEEK_OFF_CONFIG

class Command(BaseCommand):
    help = "Creates new fields in Attendance model and marks absent employees for a given number of days starting from today"
    BATCH_SIZE = 1000  # Number of records to create at once

    def add_arguments(self, parser):
        """Define command arguments."""
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Number of days to process starting from today'
        )

    def get_dates_to_process(self, num_days: int) -> List[date]:
        """Generate list of dates to process."""
        today = timezone.now().date()
        return [today - timedelta(days=i) for i in range(num_days)]

    def fetch_existing_attendance(self, dates: List[date]) -> Dict[int, Set[date]]:
        """Fetch existing attendance records grouped by employee ID."""
        existing_records = defaultdict(set)
        queryset = Attendance.objects.filter(logdate__in=dates).values_list('employeeid_id', 'logdate')
        for employee_id, logdate in queryset:
            existing_records[employee_id].add(logdate)
        return existing_records

    def create_attendance_objects(self, employees: List[Employee], dates: List[date], existing_records: Dict[int, Set[date]]):
        """Generate attendance objects for batch insertion."""
        attendance_objects = []

        # Fetch all holidays for the given date range
        holidays = HolidayList.objects.filter(holiday_date__in=dates)
        holiday_dict = {holiday.holiday_date: holiday.holiday_type for holiday in holidays}

        for employee in employees:
            join_date = employee.date_of_joining or dates[-1]
            leave_date = employee.date_of_leaving or dates[0]
            # Convert first_weekoff to an integer if it's a string
            first_weekoff = employee.first_weekly_off
            if isinstance(first_weekoff, str):
                try:
                    first_weekoff = int(first_weekoff)
                except ValueError:
                    raise ValueError

            for process_date in dates:
                if process_date < join_date or process_date > leave_date:
                    continue

                # is_week_off = process_date.weekday() in WEEK_OFF_CONFIG['DEFAULT_WEEK_OFF']
                if first_weekoff:
                    is_week_off = process_date.weekday() == first_weekoff
                else:
                    is_week_off = process_date.weekday() in WEEK_OFF_CONFIG['DEFAULT_WEEK_OFF']

                if process_date in existing_records.get(employee.id, set()):
                    continue

                shift_status = 'WO' if is_week_off else 'A'
                
                # Check if the current date is a holiday
                if process_date in holiday_dict:
                    shift_status = holiday_dict[process_date]
                

                attendance_objects.append(
                    Attendance(
                        employeeid=employee,
                        logdate=process_date,
                        shift_status=shift_status
                    )
                )

                if len(attendance_objects) >= self.BATCH_SIZE:
                    yield attendance_objects
                    attendance_objects = []

        if attendance_objects:
            yield attendance_objects

    @transaction.atomic
    def handle(self, *args, **options):
        """Main command logic."""
        num_days = options['days']
        dates = self.get_dates_to_process(num_days)

        employees = Employee.objects.only('id', 'date_of_joining', 'date_of_leaving', 'first_weekly_off')  # Fetch only required fields
        if not employees.exists():
            self.stdout.write(self.style.WARNING("No employees found"))
            return

        existing_records = self.fetch_existing_attendance(dates)

        records_to_create = 0
        for employee in employees:
            join_date = employee.date_of_joining or dates[-1]
            leave_date = employee.date_of_leaving or dates[0]
            valid_dates = [date for date in dates if join_date <= date <= leave_date]
            existing_dates_for_employee = existing_records.get(employee.id, set())
            records_to_create += len(valid_dates) - len(existing_dates_for_employee)

        with tqdm(total=records_to_create, desc="Creating attendance records", unit="records") as pbar:
            for batch in self.create_attendance_objects(employees, dates, existing_records):
                Attendance.objects.bulk_create(batch)
                pbar.update(len(batch))

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully processed attendance for {num_days} days with {employees.count()} employees"
            )
        )
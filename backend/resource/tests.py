from django.test import TestCase
from datetime import datetime, timedelta
from resource.models import Logs, LastLogIdMandays, ManDaysAttendance, Employee
from django.utils import timezone
from resource.attendance3 import process_logs  # Import your function

class ProcessLogsTestCase(TestCase):
    def setUp(self):
        # Create a test employee
        self.employee = Employee.objects.create(employee_id=123, employee_name="Test Employee")

        # Create a LastLogIdMandays instance (optional, but good practice)
        self.last_log = LastLogIdMandays.objects.create(last_log_id=0)

    def test_process_logs_single_in_out(self):
        # Create a single In and Out log
        log_in = Logs.objects.create(
            id=1,
            employeeid=123,
            log_datetime=timezone.make_aware(datetime(2024, 11, 1, 9, 0, 0)),
            direction="In Device",
        )
        log_out = Logs.objects.create(
            id=2,
            employeeid=123,
            log_datetime=timezone.make_aware(datetime(2024, 11, 1, 17, 0, 0)),
            direction="Out Device",
        )

        process_logs()

        attendance = ManDaysAttendance.objects.get(employeeid=self.employee, logdate=datetime(2024, 11, 1).date())
        self.assertEqual(attendance.duty_in_1, log_in.log_datetime.time())
        self.assertEqual(attendance.duty_out_1, log_out.log_datetime.time())
        self.assertEqual(attendance.total_hours_worked, timedelta(hours=8))
        self.assertEqual(attendance.total_time_1, timedelta(hours=8))
        self.assertEqual(LastLogIdMandays.objects.first().last_log_id, 2) # Check if last_log_id is updated

    def test_process_logs_multiple_in_out(self):
        # Create multiple In and Out logs for the same day
        logs = [
            Logs(id=i, employeeid=123, log_datetime=datetime(2024, 11, 2, 9 + i, 0, 0), direction="In Device" if i % 2 == 0 else "Out Device")
            for i in range(1, 7)
        ]
        Logs.objects.bulk_create(logs) # Bulk create for efficiency

        process_logs()

        attendance = ManDaysAttendance.objects.get(employeeid=self.employee, logdate=datetime(2024, 11, 2).date())
        self.assertEqual(attendance.duty_in_1.hour, 9+1)
        self.assertEqual(attendance.duty_out_1.hour, 9+2)
        self.assertEqual(attendance.duty_in_2.hour, 9+3)
        self.assertEqual(attendance.duty_out_2.hour, 9+4)
        self.assertEqual(attendance.duty_in_3.hour, 9+5)
        self.assertEqual(attendance.duty_out_3.hour, 9+6)


        self.assertEqual(attendance.total_hours_worked, timedelta(hours=3))  # 3 shifts of 1 hour each

        self.assertEqual(LastLogIdMandays.objects.first().last_log_id, 6) # Check if last_log_id is updated



    def test_process_logs_overnight_shift(self):
        # Test an overnight shift
        log_in = Logs.objects.create(
            id=1,
            employeeid=123,
            log_datetime=timezone.make_aware(datetime(2024, 11, 3, 22, 0, 0)), # 10 PM
            direction="In Device",
        )
        log_out = Logs.objects.create(
            id=2,
            employeeid=123,
            log_datetime=timezone.make_aware(datetime(2024, 11, 4, 6, 0, 0)),  # 6 AM next day
            direction="Out Device",
        )

        process_logs()

        # Check the previous day's record 
        attendance = ManDaysAttendance.objects.get(employeeid=self.employee, logdate=log_in.log_datetime.date())
        self.assertEqual(attendance.duty_in_1, log_in.log_datetime.time())
        self.assertEqual(attendance.total_hours_worked, timedelta(hours=8))



    # Add more test cases as needed (e.g., missing employee, multiple days, etc.)
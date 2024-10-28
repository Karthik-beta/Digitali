from django.test import TestCase
from django.utils import timezone
from .models import Employee, Logs, LastLogIdMandays, ManDaysAttendance
from resource.attendance4 import process_attendance_data, find_available_slot, find_last_used_slot
from datetime import datetime, timedelta

class AttendanceProcessorTestCase(TestCase):

    def setUp(self):
        self.employee = Employee.objects.create(employee_id="12345", employee_name="Test Employee")
        LastLogIdMandays.objects.create(pk=1, last_log_id=0)

    def test_process_attendance_data_new_logs(self):
        # Create some logs
        Logs.objects.create(employeeid="12345", log_datetime=timezone.now(), direction="In Device")
        Logs.objects.create(employeeid="12345", log_datetime=timezone.now() + timedelta(hours=8), direction="Out Device")

        # Process the data
        process_attendance_data()

        # Check that the ManDaysAttendance record was created correctly
        attendance = ManDaysAttendance.objects.get(employeeid=self.employee, logdate=timezone.now().date())
        self.assertEqual(attendance.duty_in_1.hour, timezone.now().hour)
        self.assertEqual(attendance.duty_out_1.hour, (timezone.now() + timedelta(hours=8)).hour)
        self.assertEqual(LastLogIdMandays.objects.get(pk=1).last_log_id, 2)

    def test_process_attendance_data_no_new_logs(self):
        # Update last processed log id
        last_log_obj = LastLogIdMandays.objects.get(pk=1)
        last_log_obj.last_log_id = 1
        last_log_obj.save()

        # Process the data (shouldn't do anything)
        process_attendance_data()

        # Check that no new ManDaysAttendance records were created
        self.assertEqual(ManDaysAttendance.objects.count(), 0)
        self.assertEqual(LastLogIdMandays.objects.get(pk=1).last_log_id, 1)

    def test_process_attendance_data_multiple_checkins(self):
        # Create multiple check-in/check-out logs for the same day
        Logs.objects.create(employeeid="12345", log_datetime=timezone.now(), direction="In Device")
        Logs.objects.create(employeeid="12345", log_datetime=timezone.now() + timedelta(hours=2), direction="Out Device")
        Logs.objects.create(employeeid="12345", log_datetime=timezone.now() + timedelta(hours=3), direction="In Device")
        Logs.objects.create(employeeid="12345", log_datetime=timezone.now() + timedelta(hours=9), direction="Out Device")

        # Process the data
        process_attendance_data()

        # Check that the ManDaysAttendance record was created correctly
        attendance = ManDaysAttendance.objects.get(employeeid=self.employee, logdate=timezone.now().date())
        self.assertEqual(attendance.duty_in_1.hour, timezone.now().hour)
        self.assertEqual(attendance.duty_out_1.hour, (timezone.now() + timedelta(hours=2)).hour)
        self.assertEqual(attendance.duty_in_2.hour, (timezone.now() + timedelta(hours=3)).hour)
        self.assertEqual(attendance.duty_out_2.hour, (timezone.now() + timedelta(hours=9)).hour)
        self.assertEqual(LastLogIdMandays.objects.get(pk=1).last_log_id, 4)


    def test_process_attendance_data_night_shift(self):
        # Create logs for a night shift spanning two days
        yesterday = timezone.now() - timedelta(days=1)
        Logs.objects.create(employeeid="12345", log_datetime=yesterday.replace(hour=22), direction="In Device")
        Logs.objects.create(employeeid="12345", log_datetime=timezone.now().replace(hour=6), direction="Out Device")

        # Process the data
        process_attendance_data()

        # Check that the ManDaysAttendance records for both days are correct
        yesterday_attendance = ManDaysAttendance.objects.get(employeeid=self.employee, logdate=yesterday.date())
        today_attendance = ManDaysAttendance.objects.get(employeeid=self.employee, logdate=timezone.now().date())
        self.assertEqual(yesterday_attendance.duty_in_1.hour, 22)
        self.assertEqual(yesterday_attendance.duty_out_1.hour, 6)
        self.assertIsNone(today_attendance.duty_in_1) 
        self.assertIsNone(today_attendance.duty_out_1)
        self.assertEqual(LastLogIdMandays.objects.get(pk=1).last_log_id, 2)


    def test_find_available_slot(self):
        attendance = ManDaysAttendance(employeeid=self.employee, logdate=timezone.now().date())
        self.assertEqual(find_available_slot(attendance), 1)
        attendance.duty_in_1 = timezone.now().time()
        self.assertEqual(find_available_slot(attendance), 2)

        # Fill all slots
        for i in range(1, 11):
            setattr(attendance, f"duty_in_{i}", timezone.now().time())
        self.assertIsNone(find_available_slot(attendance))

    def test_find_last_used_slot(self):
        attendance = ManDaysAttendance(employeeid=self.employee, logdate=timezone.now().date())
        self.assertIsNone(find_last_used_slot(attendance))
        attendance.duty_in_5 = timezone.now().time()
        self.assertEqual(find_last_used_slot(attendance), 5)
        attendance.duty_out_10 = timezone.now().time()
        self.assertEqual(find_last_used_slot(attendance), 10)
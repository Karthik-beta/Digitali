from django.db import transaction
from .models import Employee, Logs, LastLogIdMandays, ManDaysAttendance
from datetime import datetime, timedelta
from tqdm import tqdm

def process_attendance_data():
    """
    Processes attendance data from Logs table and updates ManDaysAttendance table.
    Handles multiple check-ins and check-outs, missed punches, and night shifts.
    """

    with transaction.atomic():
        # Get the last processed log ID
        try:
            last_log_obj = LastLogIdMandays.objects.get(pk=1)
            last_log_id = last_log_obj.last_log_id
        except LastLogIdMandays.DoesNotExist:
            last_log_id = 0

        # Get new logs
        logs = Logs.objects.filter(id__gt=last_log_id).order_by('log_datetime')

        if not logs:
            # print("No new logs found.")
            return

        # Use tqdm for progress bar
        for log in tqdm(logs, desc="Processing Logs"):
            employee_id = log.employeeid
            log_datetime = log.log_datetime
            direction = log.direction

            try:
                employee = Employee.objects.get(employee_id=employee_id)
            except Employee.DoesNotExist:
                # print(f"Employee with ID {employee_id} not found. Skipping log.")
                continue

            # Get existing attendance record for the date, if any
            log_date = log_datetime.date()
            try:
                attendance = ManDaysAttendance.objects.get(employeeid=employee, logdate=log_date)
            except ManDaysAttendance.DoesNotExist:
                attendance = ManDaysAttendance(employeeid=employee, logdate=log_date)

            # Determine the punch in/out slot (1 to 10)
            slot = find_available_slot(attendance)

            if slot is None:
                # print(f"No available slots for employee {employee_id} on {log_date}. Skipping log.")
                continue

            # Handle night shift scenario
            if slot == 1 and direction == "Out Device":
                previous_day = log_date - timedelta(days=1)
                try:
                    previous_day_attendance = ManDaysAttendance.objects.get(
                        employeeid=employee, logdate=previous_day
                    )
                    previous_slot = find_last_used_slot(previous_day_attendance)
                    if previous_slot is not None and getattr(previous_day_attendance, f"duty_in_{previous_slot}") is not None:
                        setattr(previous_day_attendance, f"duty_out_{previous_slot}", log_datetime.time())
                        previous_day_attendance.save()
                        continue  # Skip processing this log further as it's already handled
                except ManDaysAttendance.DoesNotExist:
                    pass  # No previous day's attendance found, treat as normal out punch

            # Update the attendance record with the punch time
            if direction == "In Device":
                setattr(attendance, f"duty_in_{slot}", log_datetime.time())
            elif direction == "Out Device":
                setattr(attendance, f"duty_out_{slot}", log_datetime.time())

            attendance.save()

        # Update the last processed log ID
        last_log_obj.last_log_id = logs.last().id
        last_log_obj.save()

def find_available_slot(attendance):
    """
    Finds the first available duty_in/duty_out slot in the attendance record.
    Returns the slot number (1 to 10) or None if no slots are available.
    """
    for i in range(1, 11):
        if getattr(attendance, f"duty_in_{i}") is None:
            return i
    return None

def find_last_used_slot(attendance):
    """
    Finds the last used duty_in/duty_out slot in the attendance record.
    Returns the slot number (1 to 10) or None if no slots are used.
    """
    for i in range(10, 0, -1):
        if getattr(attendance, f"duty_in_{i}") is not None or getattr(attendance, f"duty_out_{i}") is not None:
            return i
    return None
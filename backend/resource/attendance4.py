from django.core.cache import cache
from django.db import transaction
from django.db.models import Q
from datetime import timedelta, datetime
from resource.models import Logs, LastLogIdMandays, ManDaysAttendance, Employee
from tqdm import tqdm

def process_logs():
    try:
        # Start a transaction
        with transaction.atomic():
            # Get the latest last_log_id
            last_log = LastLogIdMandays.objects.first()
            last_log_id = last_log.last_log_id if last_log else 0

            # Fetch new logs greater than last_log_id
            new_logs = Logs.objects.filter(id__gt=last_log_id).order_by('log_datetime')

            # Caching employee data
            employees_cache_key = 'employees_cache'
            employees = cache.get(employees_cache_key)

            if employees is None:
                employees = {emp.employee_id: emp for emp in Employee.objects.all()}
                cache.set(employees_cache_key, employees)

            # Initialize a dictionary to collect attendance updates
            attendance_updates = {}
            

            # Process logs for each employee with a progress bar
            total_new_logs = new_logs.count()  # Count the total new logs for tqdm
            for log in tqdm(new_logs, desc="Processing new logs", total=total_new_logs, unit="log"):
                employee_id = log.employeeid

                # Use cached employees data
                employee = employees.get(employee_id)
                if not employee:
                    # print(f"Error: Employee with ID {employee_id} does not exist. Skipping log ID {log.id}.")
                    continue  # Skip this log if the employee doesn't exist

                log_date = log.log_datetime.date()

                # Fetch or create ManDaysAttendance in memory
                attendance_key = (employee_id, log_date)
                if attendance_key not in attendance_updates:
                    attendance, created = ManDaysAttendance.objects.get_or_create(
                        employeeid=employee,
                        logdate=log_date,
                        defaults={
                            'shift': '',  # Set default values as needed
                            'shift_status': ''
                        }
                    )
                    attendance_updates[attendance_key] = attendance
                else:
                    attendance = attendance_updates[attendance_key]

                # Update duty_in or duty_out based on 'In Device' or 'Out Device'
                if log.direction == 'In Device':
                    # Find the first available duty_in (duty_in_1, duty_in_2, etc.)
                    for i in range(1, 11):
                        duty_in_field = f'duty_in_{i}'
                        if not getattr(attendance, duty_in_field):  # If field is empty
                            setattr(attendance, duty_in_field, log.log_datetime.time())
                            break

                elif log.direction == 'Out Device':
                    last_duty_in = None

                    # Find the last "In Device" for the current day
                    for i in range(10, 0, -1):  # Reverse search through duty_in fields
                        duty_in_field = f'duty_in_{i}'
                        duty_out_field = f'duty_out_{i}'

                        if getattr(attendance, duty_in_field) and not getattr(attendance, duty_out_field):
                            last_duty_in = getattr(attendance, duty_in_field)
                            setattr(attendance, duty_out_field, log.log_datetime.time())
                            break

                    # If no "In Device" found, search previous days
                    if not last_duty_in:
                        previous_attendance = ManDaysAttendance.objects.filter(
                            employeeid=employee,
                            logdate__lt=log_date  # Previous days
                        ).order_by('-logdate').first()

                        if previous_attendance:
                            for i in range(10, 0, -1):
                                duty_in_field = f'duty_in_{i}'
                                duty_out_field = f'duty_out_{i}'

                                if getattr(previous_attendance, duty_in_field) and not getattr(previous_attendance, duty_out_field):
                                    last_duty_in = getattr(previous_attendance, duty_in_field)
                                    attendance = previous_attendance  # Update attendance to previous day's record
                                    break

                    # If still no valid "In Device", log the error and skip
                    if not last_duty_in:
                        # print(f"Error: No duty_in found for employee {employee_id} on {log_date} or previous days. Skipping log ID {log.id}.")
                        continue

                    # Find the first available duty_out (duty_out_1, duty_out_2, etc.)
                    for i in range(1, 11):
                        duty_out_field = f'duty_out_{i}'
                        if not getattr(attendance, duty_out_field):  # If field is empty
                            setattr(attendance, duty_out_field, log.log_datetime.time())
                            break

                # After processing the In/Out, recalculate total_hours_worked
                total_hours_worked = timedelta()  # Initialize a zero timedelta
                for i in range(1, 11):
                    duty_in_field = f'duty_in_{i}'
                    duty_out_field = f'duty_out_{i}'
                    total_time_field = f'total_time_{i}'

                    duty_in = getattr(attendance, duty_in_field)
                    duty_out = getattr(attendance, duty_out_field)

                    if duty_in and duty_out:
                        # Combine the date from log_date with the duty_in time
                        in_time = datetime.combine(log_date, duty_in)
                        out_time = datetime.combine(log_date, log.log_datetime.time())

                        # Ensure out_time is greater than in_time
                        if out_time < in_time:
                            # print(f"Warning: out_time {out_time} is less than in_time {in_time} for shift {i}.")
                            total_time = timedelta()  # Or any default value you'd like
                        else:
                            total_time = out_time - in_time

                        # Update total_time_X field
                        setattr(attendance, total_time_field, total_time)

                        # Accumulate the total time for all shifts
                        total_hours_worked += total_time

                # Update total_hours_worked after all shifts are processed
                attendance.total_hours_worked = total_hours_worked

                # Update last_log_id after successful processing of this log
                if last_log:
                    last_log_id = log.id
                else:
                    print("No last_log_id found. Initializing to 0.")
                    last_log_id = 0
                    last_log = LastLogIdMandays()  # Create a new instance for saving later

                # Now you can safely save the last_log if it's a valid instance
                last_log.last_log_id = last_log_id  # Set the last_log_id
                last_log.save()

            # Bulk save all attendance records
            if attendance_updates:
                ManDaysAttendance.objects.bulk_update(
                    attendance_updates.values(),
                    ['duty_in_1', 'duty_out_1', 'total_time_1', 'duty_in_2', 'duty_out_2', 'total_time_2', 'duty_in_3', 'duty_out_3', 'total_time_3', 'duty_in_4', 'duty_out_4', 'total_time_4', 'duty_in_5', 'duty_out_5', 'total_time_5', 'duty_in_6', 'duty_out_6', 'total_time_6', 'duty_in_7', 'duty_out_7', 'total_time_7', 'duty_in_8', 'duty_out_8', 'total_time_8', 'duty_in_9', 'duty_out_9', 'total_time_9', 'duty_in_10', 'duty_out_10', 'total_time_10', 'total_hours_worked']
                )

            # Invalidate cache after successful processing
            cache.delete(employees_cache_key)

    except Exception as e:
        # Handle exceptions, such as rollback the transaction
        print(f"Error occurred during log processing: {e}")

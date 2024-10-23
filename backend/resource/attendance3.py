from django.db import transaction
from django.db.models import Q
from datetime import timedelta, datetime
from resource.models import Logs, LastLogIdMandays, ManDaysAttendance, Employee

def process_logs():
    try:
        # Start a transaction
        with transaction.atomic():
            # Get the latest last_log_id
            last_log = LastLogIdMandays.objects.first()
            last_log_id = last_log.last_log_id if last_log else 0

            # Fetch new logs greater than last_log_id
            new_logs = Logs.objects.filter(id__gt=last_log_id).order_by('log_datetime')

            # Process logs for each employee
            for log in new_logs:
                employee_id = log.employeeid

                # Fetch the employee instance
                employee = Employee.objects.filter(employee_id=employee_id).first()
                if not employee:
                    print(f"Error: Employee with ID {employee_id} does not exist. Skipping log ID {log.id}.")
                    continue  # Skip this log if the employee doesn't exist

                log_date = log.log_datetime.date()

                # Find or create the employee's ManDaysAttendance for that day
                attendance, created = ManDaysAttendance.objects.get_or_create(
                    employeeid=employee,  # Use the employee instance here
                    logdate=log_date,
                    defaults={
                        'shift': '',  # Set default values as needed
                        'shift_status': ''
                    }
                )

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

                    # First, try to find the last "In Device" for the current day
                    for i in range(10, 0, -1):  # Reverse search through duty_in fields
                        duty_in_field = f'duty_in_{i}'
                        duty_out_field = f'duty_out_{i}'
                        total_time_field = f'total_time_{i}'

                        if getattr(attendance, duty_in_field) and not getattr(attendance, duty_out_field):
                            last_duty_in = getattr(attendance, duty_in_field)
                            setattr(attendance, duty_out_field, log.log_datetime.time())
                            break

                    # If no "In Device" found for the current day, search the previous days
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
                                    attendance = previous_attendance  # Update the attendance to the previous day's record
                                    break

                    # If still no valid "In Device" is found, log the error and skip
                    if not last_duty_in:
                        print(f"Error: No duty_in found for employee {employee_id} on {log_date} or previous days. Skipping log ID {log.id}.")
                        continue

                    found_duty_out = False  # Flag to track if duty_out is found

                    # Find the first available duty_out (duty_out_1, duty_out_2, etc.)
                    for i in range(1, 11):
                        duty_out_field = f'duty_out_{i}'
                        duty_in_field = f'duty_in_{i}'
                        # if not getattr(attendance, duty_out_field):
                        #     if last_duty_in and log.log_datetime.time() > last_duty_in:  # Validate
                        #         setattr(attendance, duty_out_field, log.log_datetime.time())
                        #         break
                        #     elif last_duty_in:
                        #         print(f"Error: duty_out time {log.log_datetime.time()} is before or equal to duty_in time {last_duty_in}. Skipping log ID {log.id}")
                        #         continue # Skip this log and check the next

                        if not getattr(attendance, duty_out_field) and last_duty_in:
                            # Check for subsequent duty_in entries
                            next_duty_in = None
                            for j in range(i + 1, 11):  # Check from next shift onwards
                                next_duty_in_field = f'duty_in_{j}'
                                if getattr(attendance, next_duty_in_field):
                                    next_duty_in = getattr(attendance, next_duty_in_field)
                                    break  # Found a subsequent duty_in

                            if next_duty_in: # Means there's already a duty_in_2 entry before duty_out_1, that needs to be handled
                                if last_duty_in and log.log_datetime.time() > last_duty_in and log.log_datetime.time() <= next_duty_in:
                                    setattr(attendance, duty_out_field, log.log_datetime.time())
                                    found_duty_out = True
                                    break
                                elif last_duty_in:
                                    print(f"Error: duty_out time {log.log_datetime.time()} falls after duty_in_{j}. Skipping log ID {log.id}")
                                    found_duty_out = True # this is a problem in this case as duty_out_1 doesn't fall before duty_in_2, hence duty_out_1 shouldn't be considered
                                    break
                            elif last_duty_in and log.log_datetime.time() > last_duty_in:  # Check if duty_out is greater than duty_in
                                setattr(attendance, duty_out_field, log.log_datetime.time())
                                found_duty_out = True
                                break
                            else:
                                print(f"Error: duty_out time {log.log_datetime.time()} is before duty_in. Skipping log ID {log.id}")
                                continue # Skip this log entry and check the next

                    if not found_duty_out and last_duty_in:
                        print(f"Warning: No suitable duty_out slot found for log ID {log.id} after duty_in {last_duty_in}")


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
                        # out_time = datetime.combine(log_date, log.log_datetime.time())
                        out_time = datetime.combine(log_date, duty_out)

                        # Ensure out_time is greater than in_time
                        if out_time < in_time:
                            print(f"Warning: out_time {out_time} is less than in_time {in_time} for shift {i}.")
                            total_time = timedelta()  # Or any default value you'd like, like 0
                        else:
                            total_time = out_time - in_time

                        # Update total_time_X field
                        setattr(attendance, total_time_field, total_time)

                        # Accumulate the total time for all shifts
                        total_hours_worked += total_time

                # Update total_hours_worked after all shifts are processed
                attendance.total_hours_worked = total_hours_worked

                # Save the attendance record
                attendance.save()

                # Update last_log_id after successful processing of this log
                # last_log.last_log_id = log.id
                # Check if a last_log exists, otherwise set last_log_id to 0
                if last_log:
                    last_log_id = log.id
                else:
                    print("No last_log_id found. Initializing to 0.")
                    last_log_id = 0
                    last_log = LastLogIdMandays() # Create a new instance for saving later

                # Now you can safely save the last_log if it's a valid instance
                last_log.last_log_id = last_log_id  # Set the last_log_id
                # last_log.save()

    except Exception as e:
        # Handle exceptions, such as rollback the transaction
        print(f"Error occurred during log processing: {e}")

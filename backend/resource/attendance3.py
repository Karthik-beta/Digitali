from django.db import transaction
from django.db.models import Q
from datetime import timedelta, datetime
from tqdm import tqdm
from resource.models import Logs, LastLogIdMandays, ManDaysAttendance, Employee


def process_employee_log(log, last_log, last_log_id):
    """Process a single employee log."""
    employee = Employee.objects.filter(employee_id=log.employeeid).first()
    if not employee:
        # print(f"Error: Employee with ID {log.employeeid} does not exist. Skipping log ID {log.id}.")
        return

    log_date = log.log_datetime.date()
    attendance, created = ManDaysAttendance.objects.get_or_create(
        employeeid=employee,
        logdate=log_date,
        defaults={'shift': '', 'shift_status': ''}
    )

    if log.direction == 'In Device':
        handle_duty_in(log, attendance)
    elif log.direction == 'Out Device':
        handle_duty_out(log, attendance, employee, log_date)

    calculate_total_hours(attendance, log_date)
    attendance.save()

    last_log.last_log_id = log.id
    # last_log.save()


def handle_duty_in(log, attendance):
    """Handles 'In Device' logs, managing overlapping shifts."""
    for i in range(1, 11):
        duty_in_field = f'duty_in_{i}'
        duty_out_field = f'duty_out_{i}'

        if not getattr(attendance, duty_in_field) and not getattr(attendance, duty_out_field):  # Empty duty_in slot
            setattr(attendance, duty_in_field, log.log_datetime.time())
            return

        elif getattr(attendance, duty_in_field) and not getattr(attendance, duty_out_field):
            # Previous duty_in exists without duty_out, handle overlapping shift. This is where we can handle a duty_in before duty_out
            # Here we decide how to deal with overlapping shifts. For example:
            # 1. Ignore the new duty_in (as implemented below)
            # 2. Overwrite previous duty_in (if it makes sense in your business logic)
            # print(f"Overlapping shift detected for employee {attendance.employeeid.employee_id} on {attendance.logdate}. Ignoring new duty_in.")
            return

    # No previous duty_in or previous has duty_out, start a new shift  
    for i in range(1, 11):  
        duty_in_field = f'duty_in_{i}'
        if not getattr(attendance, duty_in_field):
            setattr(attendance, duty_in_field, log.log_datetime.time())
            break


def handle_duty_out(log, attendance, employee, log_date):
    """Handles 'Out Device' logs, skipping if no corresponding duty_in."""

    has_open_duty_in = False # flag to track open duty_in
    for i in range(1, 11):
        duty_in_field = f'duty_in_{i}'
        duty_out_field = f'duty_out_{i}'

        if getattr(attendance, duty_in_field) and not getattr(attendance, duty_out_field):
            has_open_duty_in = True
            if log.log_datetime.time() > getattr(attendance, duty_in_field):
                setattr(attendance, duty_out_field, log.log_datetime.time())
                return  # Exit after setting a duty_out
            else:
                #  print(f"Error: duty_out time {log.log_datetime.time()} is before or equal to duty_in time {getattr(attendance, duty_in_field)}. Skipping log ID {log.id}.")
                 return #Added a return here, to prevent a scenario where a duty_out could still be registered after an invalid time


    if not has_open_duty_in:
        # print(f"Skipping 'Out Device' log with ID {log.id} as no corresponding 'In Device' log found.")
        return


def find_last_duty_in(attendance, log_date):
    """Find the most recent duty_in time for an attendance record."""
    for i in range(10, 0, -1):
        duty_in_field = f'duty_in_{i}'
        if getattr(attendance, duty_in_field):
            return getattr(attendance, duty_in_field)
    return None


def find_last_duty_in_index(attendance):
    """Find the index of the most recent duty_in time."""
    for i in range(10, 0, -1):
        duty_in_field = f'duty_in_{i}'
        if getattr(attendance, duty_in_field):
            return i
    return None


def find_previous_attendance(employee, log_date):
    """Find the most recent attendance record before the current log date."""
    return ManDaysAttendance.objects.filter(employeeid=employee, logdate__lt=log_date).order_by('-logdate').first()


def set_duty_out(log, attendance, last_duty_in):
    """Set duty_out if the time is valid, otherwise log an error."""
    for i in range(1, 11):
        duty_out_field = f'duty_out_{i}'
        if not getattr(attendance, duty_out_field):
            if log.log_datetime.time() > last_duty_in:
                setattr(attendance, duty_out_field, log.log_datetime.time())
            else:
                # print(f"Error: duty_out time {log.log_datetime.time()} is before or equal to duty_in time {last_duty_in}. Skipping log ID {log.id}.")
                continue
            break


def calculate_total_hours(attendance, log_date):
    """Calculate total hours worked based on the duty_in and duty_out times."""
    total_hours_worked = timedelta()

    for i in range(1, 11):
        duty_in = getattr(attendance, f'duty_in_{i}')
        duty_out = getattr(attendance, f'duty_out_{i}')

        if duty_in and duty_out:
            in_time = datetime.combine(log_date, duty_in)
            out_time = datetime.combine(log_date, duty_out)
            
            # Handle cases where out_time is on the next day
            if out_time < in_time:
                out_time += timedelta(days=1) 

            total_time = out_time - in_time
            setattr(attendance, f'total_time_{i}', total_time)
            total_hours_worked += total_time

    attendance.total_hours_worked = total_hours_worked


def process_logs():
    """Main function to process all logs."""
    try:
        with transaction.atomic():
            last_log = LastLogIdMandays.objects.first() or LastLogIdMandays(last_log_id=0)
            last_log_id = last_log.last_log_id

            new_logs = Logs.objects.filter(id__gt=last_log_id).order_by('log_datetime')

            # Use tqdm to wrap the iterable (new_logs)
            with tqdm(total=new_logs.count(), desc="Processing Logs", unit="log") as pbar:
                for log in new_logs:
                    process_employee_log(log, last_log, last_log_id)
                    pbar.update(1)

    except Exception as e:
        print(f"Error occurred during log processing: {e}")
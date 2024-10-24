from django.db import transaction
from django.db.models import Q
from datetime import timedelta, datetime
from resource.models import Logs, LastLogIdMandays, ManDaysAttendance, Employee


def process_employee_log(log, last_log, last_log_id):
    """Process a single employee log."""
    employee = Employee.objects.filter(employee_id=log.employeeid).first()
    if not employee:
        print(f"Error: Employee with ID {log.employeeid} does not exist. Skipping log ID {log.id}.")
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
    last_log.save()


def handle_duty_in(log, attendance):
    """Handle 'In Device' logs and set the first available duty_in."""
    # Check if the previous duty_in has a corresponding duty_out
    last_duty_in_index = find_last_duty_in_index(attendance)
    if last_duty_in_index:
        duty_out_field = f'duty_out_{last_duty_in_index}'
        if not getattr(attendance, duty_out_field):
            # Previous duty_in doesn't have a duty_out, treat this as a correction
            setattr(attendance, f'duty_in_{last_duty_in_index}', log.log_datetime.time())
            return

    # Find the next available duty_in slot
    for i in range(1, 11):
        duty_in_field = f'duty_in_{i}'
        if not getattr(attendance, duty_in_field):
            setattr(attendance, duty_in_field, log.log_datetime.time())
            break


def handle_duty_out(log, attendance, employee, log_date):
    """Handle 'Out Device' logs and find the corresponding duty_in."""
    last_duty_in = find_last_duty_in(attendance, log_date)

    if not last_duty_in:
        previous_attendance = find_previous_attendance(employee, log_date)
        if previous_attendance:
            last_duty_in = find_last_duty_in(previous_attendance, previous_attendance.logdate)
            attendance = previous_attendance

    if not last_duty_in:
        print(f"Error: No duty_in found for employee {employee.employee_id} on {log_date} or previous days. Skipping log ID {log.id}.")
        return

    set_duty_out(log, attendance, last_duty_in)


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
                print(f"Error: duty_out time {log.log_datetime.time()} is before or equal to duty_in time {last_duty_in}. Skipping log ID {log.id}.")
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

            if out_time > in_time:
                total_time = out_time - in_time
                setattr(attendance, f'total_time_{i}', total_time)
                total_hours_worked += total_time
            else:
                print(f"Warning: out_time {out_time} is less than in_time {in_time} for shift {i}.")
                setattr(attendance, f'total_time_{i}', timedelta())

    attendance.total_hours_worked = total_hours_worked


def process_logs():
    """Main function to process all logs."""
    try:
        with transaction.atomic():
            last_log = LastLogIdMandays.objects.first() or LastLogIdMandays(last_log_id=0)
            last_log_id = last_log.last_log_id

            new_logs = Logs.objects.filter(id__gt=last_log_id).order_by('log_datetime')

            for log in new_logs:
                process_employee_log(log, last_log, last_log_id)

    except Exception as e:
        print(f"Error occurred during log processing: {e}")
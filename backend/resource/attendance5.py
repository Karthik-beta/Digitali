from .models import Logs, ManDaysMissedPunchAttendance, Employee
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

def process_missed_punches():
    """
    Processes logs to identify and store ONLY missed punches in 
    ManDaysMissedPunchAttendance, separating records by day.
    """

    logs = Logs.objects.all().order_by('employeeid', 'log_datetime')

    missed_punches_data = {}

    for log in logs:
        try:
            employee_id = Employee.objects.get(employee_id=log.employeeid)
        except ObjectDoesNotExist:
            # Handle the case where Employee is not found (e.g., log it, skip it)
            print(f"Warning: Employee with employee_id '{log.employeeid}' not found. Skipping log entry.")
            continue  # Skip to the next log entry

        log_date = log.log_datetime.date()

        if employee_id not in missed_punches_data:
            missed_punches_data[employee_id] = {}

        if log_date not in missed_punches_data[employee_id]:
            missed_punches_data[employee_id][log_date] = {
                'duty_times': [],
                'in_out_counter': 0,
                'last_direction': None,  # Track the last direction (In/Out)
            }

        data = missed_punches_data[employee_id][log_date]
        counter = data['in_out_counter']
        last_direction = data['last_direction']

        # Limit to 10 In/Out pairs
        if counter >= 10:
            continue  # Skip this log entry if we've already reached the limit

        if log.direction == 'In Device':
            if last_direction == 'In Device':  # Missed punch (consecutive In)
                if len(data['duty_times']) <= counter:
                    data['duty_times'].append({'in': log.log_datetime.time(), 'out': None})
                else:
                    if data['duty_times'][counter]['in'] is None:
                        data['duty_times'][counter]['in'] = log.log_datetime.time()
                        if counter < 9:
                            data['in_out_counter'] += 1
                    else:
                        if counter < 9:  # Only increment if counter is less than 9
                            data['in_out_counter'] += 1
                        data['duty_times'].append({'in': log.log_datetime.time(), 'out': None})  # Append regardless of counter limit
            

            data['last_direction'] = 'In Device'

        elif log.direction == 'Out Device':
            if last_direction == 'Out Device' or last_direction is None:  # Missed punch (consecutive Out or first Out without In)
                if len(data['duty_times']) <= counter:
                    data['duty_times'].append({'in': None, 'out': log.log_datetime.time()})
                else:
                    if data['duty_times'][counter]['out'] is None:
                        data['duty_times'][counter]['out'] = log.log_datetime.time()
                        if counter < 9:  # Only increment if counter is less than 9
                            data['in_out_counter'] += 1
                    else:
                        if counter < 9:  # Only increment if counter is less than 9
                            data['in_out_counter'] += 1
                        data['duty_times'].append({'in': None, 'out': log.log_datetime.time()})  # Append regardless of counter limit

            elif last_direction == 'In Device':
                if len(data['duty_times']) > counter and data['duty_times'][counter]['out'] is None:
                    data['duty_times'][counter]['out'] = log.log_datetime.time()
                    if counter < 9:  # Only increment if counter is less than 9
                        data['in_out_counter'] += 1

            data['last_direction'] = 'Out Device'

    for employee_id, dates_data in missed_punches_data.items():
        for log_date, data in dates_data.items():
            duty_times = data['duty_times'][:10]  # Limit duty_times to the first 10 entries
            # Create ManDaysMissedPunchAttendance instance with dynamic duty times (up to 10)
            attendance_data = {
                'employeeid': employee_id,
                'logdate': log_date,
            }
            for i, times in enumerate(duty_times):
                attendance_data[f'duty_in_{i + 1}'] = times['in']
                attendance_data[f'duty_out_{i + 1}'] = times['out']

            if any(times['in'] is not None or times['out'] is not None for times in duty_times):  # Check if there are any duty times
                ManDaysMissedPunchAttendance.objects.create(**attendance_data)
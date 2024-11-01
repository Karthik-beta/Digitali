from .models import Logs, ManDaysMissedPunchAttendance, Employee, LastLogId, Attendance
from config.models import AutoShift
from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from collections import defaultdict

def process_attendance():
    # Start a transaction block
    with transaction.atomic():

        In_Direction = "In Device"
        Out_Direction = "Out Device"

        # Get all the employees into a dictionary
        employees = {employee.employee_id: employee for employee in Employee.objects.all()}
        # print(f"Processing attendance for {len(employees)} employees...", employees)

        auto_shifts = [auto_shift for auto_shift in AutoShift.objects.all()]
        for entry in auto_shifts:
            print(f"Auto Shifts: {entry.name} - {entry.start_time} - {entry.end_time}")
        # print(f"Processing attendance for {len(auto_shifts)} auto shifts... {auto_shifts.name}", auto_shifts)

        # Get the last log ID
        last_log_id_record = LastLogId.objects.select_for_update().first()
        last_log_id = last_log_id_record.last_log_id if last_log_id_record else 0

        # Fetch logs greater than the last log ID
        logs = Logs.objects.filter(id__gt=last_log_id).order_by('log_datetime')

        # Bind logs to a list
        logs_list = list(logs)
        # print(f"Processing {len(logs_list)} logs...", logs_list)

        if logs_list:
            # Get the lowest log_date from logs
            lowest_log_date = min(log.log_datetime.date() for log in logs_list)

            # Fetch all attendance records starting from the lowest log_date
            attendance_records = Attendance.objects.filter(logdate__gte=lowest_log_date).order_by('logdate')

            attendance_dict = {
                record.employeeid.employee_id: {
                    "log_date": record.logdate,
                    "first_logtime": record.first_logtime,
                    "last_logtime": record.last_logtime,
                    "direction": record.direction,
                    "shortname": record.shortname,
                    "total_time": record.total_time,
                    "late_entry": record.late_entry,
                    "early_exit": record.early_exit,
                    "overtime": record.overtime,
                    "shift": record.shift,
                    "shift_status": record.shift_status,
                }
                for record in attendance_records
            }

            print(f"Processing {len(attendance_records)} attendance records...", attendance_dict)

            # Create a dictionary to hold log entries grouped by employee and date
            log_entries = defaultdict(list)

            # Group logs by employee ID and date
            for log in logs_list:
                log_date = log.log_datetime.date()
                log_entries[(log.employeeid, log_date)].append(log)

            # Prepare the final attendance array
            attendance_array = []

            # Iterate over the grouped log entries to match log_in and log_out
            for (employee_id, log_date), entries in log_entries.items():
                # Sort entries by log_datetime to ensure correct pairing
                entries.sort(key=lambda x: x.log_datetime)

                # Initialize variables to store log_in and log_out
                log_in = None
                log_out = None

                # Find the first log_in and the last log_out of the day
                for entry in entries:
                    if entry.direction.lower() == In_Direction and log_in is None:
                        log_in = entry  # Set log_in only if it hasn't been set yet
                    elif entry.direction.lower() == Out_Direction:
                        log_out = entry  # Keep updating log_out, so the last entry is captured

                # Store the log details, even if only one of them is present
                attendance_entry = {
                    "employee_id": employee_id,
                    "log_date": log_date,
                    "log_in": log_in.log_datetime if log_in else None,
                    "log_out": log_out.log_datetime if log_out else None
                }
                attendance_array.append(attendance_entry)

                # for entry in attendance_array:
                #     print(f"{entry['employee_id']} - Date : {entry['log_date']} - In : {entry['log_in']} - Out : {entry['log_out']}")

            return attendance_array  # Return the array of attendance records if needed
        else:
            print("No logs found after the last log ID.")
            return []
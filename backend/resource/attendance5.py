from datetime import datetime, timedelta
from typing import Optional, Dict, List

from django.db import models
from django.utils import timezone
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from config.models import Shift, AutoShift
from resource.models import Employee, Attendance

import logging

logger = logging.getLogger(__name__)

# Cache for AutoShift objects
auto_shift_cache: Dict[str, AutoShift] = {}
cache_valid = True

def load_auto_shifts():
    """Load AutoShift objects into cache."""
    global auto_shift_cache, cache_valid
    auto_shift_cache = {auto_shift.name: auto_shift for auto_shift in AutoShift.objects.all()}
    cache_valid = True

def invalidate_cache():
    """Invalidate the cache and optionally reload it."""
    global auto_shift_cache, cache_valid
    auto_shift_cache.clear()
    cache_valid = False
    load_auto_shifts()  # Optionally refresh the cache immediately

def get_auto_shift_by_name(name: str) -> Optional[AutoShift]:
    """Get AutoShift by name from cache or return None if not valid."""
    if cache_valid:
        return auto_shift_cache.get(name)
    return None

def on_auto_shift_change():
    """Function to call when AutoShift records are modified."""
    invalidate_cache()

def process_attendance(employeeid: str, log_datetime: datetime, direction: str) -> bool:
    if not employeeid:
        return False

    # Fetch all required AutoShifts once
    auto_shifts = list(AutoShift.objects.all())

    try:
        employee = Employee.objects.get(employee_id=employeeid)
    except Employee.DoesNotExist:
        logger.error(f"Employee with ID: {employeeid} not found.")
        return False

    week_off = [6]

    if employee.shift is None:
        log_time = log_datetime.time()
        log_date = log_datetime.date()

        if direction == 'In Device':
            for auto_shift in auto_shifts:
                start_time = auto_shift.start_time
                end_time = auto_shift.end_time
                tolerance_start = auto_shift.tolerance_start_time
                tolerance_end = auto_shift.tolerance_end_time
                grace_period_at_start_time = auto_shift.grace_period_at_start_time

                start_window = (datetime.combine(log_date, start_time) - tolerance_start).time()
                end_window = (datetime.combine(log_date, start_time) + tolerance_end).time()
                start_time_with_grace = (datetime.combine(log_date, start_time) + grace_period_at_start_time).time()

                if start_window <= log_time <= end_window:
                    if log_datetime.weekday() not in week_off:
                        # Batch update/create
                        attendance, created = Attendance.objects.update_or_create(
                            employeeid=employee,
                            logdate=log_date,
                            defaults={
                                'first_logtime': log_time,
                                'shift': auto_shift.name,
                                'direction': 'Machine',
                                'shift_status': 'MP'
                            }
                        )

                        if created:
                            if log_time > start_time_with_grace:
                                start_time_aware = timezone.make_aware(datetime.combine(log_date, start_time))
                                attendance.late_entry = log_datetime - start_time_aware
                            attendance.save()
                            logger.info(f"Attendance record created for employee {employeeid} on {log_date}")
                        else:
                            if log_time > start_time_with_grace:
                                start_time_aware = timezone.make_aware(datetime.combine(log_date, start_time))
                                attendance.late_entry = log_datetime - start_time_aware
                            attendance.first_logtime = log_time
                            attendance.shift = auto_shift.name
                            attendance.direction = 'Machine'
                            attendance.save()
                    else:
                        # Handle week off
                        Attendance.objects.update_or_create(
                            employeeid=employee,
                            logdate=log_date,
                            defaults={
                                'first_logtime': log_time,
                                'shift': auto_shift.name,
                                'direction': 'Machine',
                                'shift_status': 'WW'
                            }
                        )
                    return True

            logger.warning(f"No matching AutoShift found for employee {employeeid} with first log time {log_datetime}")
            return False

        elif direction == 'Out Device':
            # Try to get the attendance record for the current date
            try:
                attendance = Attendance.objects.get(
                    employeeid=employee,
                    logdate=log_date,
                    first_logtime__isnull=False
                )
            except Attendance.DoesNotExist:
                # If not found, check for the previous day (useful for night shifts)
                previous_day = log_date - timedelta(days=1)
                try:
                    attendance = Attendance.objects.get(
                        employeeid=employee,
                        logdate=previous_day,
                        first_logtime__isnull=False
                    )
                    logger.info(f"Attendance record found for the previous day {previous_day} for employee {employee.employee_id}")
                except Attendance.DoesNotExist:
                    logger.warning(f"No IN log found for employee {employee.employee_id} on {log_date}")
                    # Logic for creating an attendance record if no IN log is found
                    return handle_out_device_log(employee, log_datetime, auto_shifts, week_off)

            if attendance and log_datetime > timezone.make_aware(datetime.combine(attendance.logdate, attendance.first_logtime)):
                shift = attendance.shift
                night_shift = AutoShift.objects.get(name=shift).night_shift if shift else False
                first_logtime = attendance.first_logtime

                # Handle attendance update for day or night shift
                if not night_shift:
                    update_day_shift_attendance(attendance, log_datetime, week_off)
                else:
                    update_night_shift_attendance(attendance, log_datetime, week_off)

                try:
                    attendance.save()
                    logger.info(f"Attendance processed for employee: {employeeid} at {log_datetime}")
                    return True 
                except Exception as e:
                    logger.error(f"Error saving attendance record for employee {employeeid}: {e}")
                    return False

    return True  

def handle_out_device_log(employee, log_datetime, auto_shifts, week_off):
    """Handles the attendance logic when an out device log is recorded."""
    log_time = log_datetime.time()
    log_date = log_datetime.date()

    for auto_shift in auto_shifts:
        end_time = auto_shift.end_time
        tolerance_start = auto_shift.tolerance_start_time
        tolerance_end = auto_shift.tolerance_end_time
        grace_period_at_end_time = auto_shift.grace_period_at_end_time

        start_window = (datetime.combine(log_date, end_time) - tolerance_start).time()
        end_window = (datetime.combine(log_date, end_time) + tolerance_end).time()

        if start_window <= log_time <= end_window:
            if log_datetime.weekday() not in week_off:
                Attendance.objects.update_or_create(
                    employeeid=employee,
                    logdate=log_date,
                    defaults={
                        'last_logtime': log_time,
                        'shift': auto_shift.name,
                        'direction': 'Machine',
                        'shift_status': 'MP'
                    }
                )
            return True

    return False

def update_day_shift_attendance(attendance, log_datetime, week_off):
    """Updates the attendance record for day shifts."""
    log_time = log_datetime.time()
    log_date = attendance.logdate

    start_time = AutoShift.objects.get(name=attendance.shift).start_time
    end_time = AutoShift.objects.get(name=attendance.shift).end_time
    half_day_threshold = AutoShift.objects.get(name=attendance.shift).half_day_threshold

    attendance.last_logtime = log_time
    attendance.direction = 'Machine'
    attendance.total_time = log_datetime - timezone.make_aware(datetime.combine(log_date, attendance.first_logtime))

    if log_datetime.weekday() not in week_off:
        if attendance.total_time > half_day_threshold:
            attendance.shift_status = 'P'
        else: 
            attendance.shift_status = 'HD'
    else:
        attendance.shift_status = 'WW'

def update_night_shift_attendance(attendance, log_datetime, week_off):
    """Updates the attendance record for night shifts."""
    log_time = log_datetime.time()
    log_date = attendance.logdate + timedelta(days=1)

    start_time = AutoShift.objects.get(name=attendance.shift).start_time
    end_time = AutoShift.objects.get(name=attendance.shift).end_time

    attendance.last_logtime = log_time
    attendance.direction = 'Machine'

    attendance.total_time = timezone.make_aware(datetime.combine(log_date, attendance.last_logtime)) - timezone.make_aware(datetime.combine(attendance.logdate, attendance.first_logtime))

    if attendance.logdate.weekday() not in week_off:
        # Set shift status and calculate overtime if needed
        attendance.shift_status = 'P' if attendance.total_time > AutoShift.objects.get(name=attendance.shift).half_day_threshold else 'HD'
    else:
        attendance.shift_status = 'WW'

# Connect signals to invalidate cache on AutoShift changes
@receiver(post_save, sender=AutoShift)
def auto_shift_saved(sender, instance, created, **kwargs):
    on_auto_shift_change()

@receiver(post_delete, sender=AutoShift)
def auto_shift_deleted(sender, instance, **kwargs):
    on_auto_shift_change()

# Load AutoShifts into cache initially
load_auto_shifts()

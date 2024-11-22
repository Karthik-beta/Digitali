from datetime import datetime, timedelta, time
from dataclasses import dataclass
from typing import Optional, Tuple
from tqdm import tqdm

from django.db import models, transaction
from django.utils import timezone

from config.models import AutoShift
from resource.models import Employee, Logs, Attendance, LastLogId
from value_config import WEEK_OFF_CONFIG

import logging

logger = logging.getLogger(__name__)

@dataclass
class ShiftWindow:
    start_time: datetime
    end_time: datetime
    start_window: time
    end_window: time
    start_time_with_grace: time
    end_time_with_grace: time
    overtime_before_start: timedelta
    overtime_after_end: timedelta
    half_day_threshold: timedelta

class AttendanceProcessor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @transaction.atomic
    def process_new_logs(self) -> bool:
        """Process all new logs since last processed ID."""
        try:
            last_log_id_record = LastLogId.objects.select_for_update().first()
            if not last_log_id_record:
                last_log_id_record = LastLogId.objects.create(last_log_id=0)
            
            last_processed_id = last_log_id_record.last_log_id
            new_logs = Logs.objects.filter(id__gt=last_processed_id).order_by('log_datetime')
            # for log in new_logs:
            #     print(f"Log ID: {log.id}, Employee ID: {log.employeeid}, Log Datetime: {log.log_datetime}, Direction: {log.direction}")

            total_logs = new_logs.count()
            
            if total_logs == 0:
                # self.logger.info("No new logs to process")
                return True
            
            success = True
            with tqdm(total=total_logs, desc="Processing attendance logs", 
                     unit="log", ncols=80) as pbar:
                for log in new_logs:
                    if not self.process_single_log(log):
                        # self.logger.error(f"Failed to process log ID: {log.id}")
                        success = False
                    last_log_id_record.last_log_id = log.id
                    last_log_id_record.save()
                    pbar.update(1)
            
            return success
        except Exception as e:
            # self.logger.error(f"Error in process_new_logs: {str(e)}")
            return False

    def process_single_log(self, log: Logs) -> bool:
        """Process a single attendance log."""
        if not log.employeeid:
            # self.logger.error("Empty employee ID in log")
            return False

        try:
            employee = Employee.objects.get(employee_id=log.employeeid)
        except Employee.DoesNotExist:
            # self.logger.error(f"Employee with ID: {log.employeeid} not found.")
            return False
        except Exception as e:
            # self.logger.error(f"Error fetching employee {log.employeeid}: {str(e)}")
            return False

        try:
            if not employee.shift:
                if log.direction.lower() == 'in device':
                    return self._handle_in_log(employee, log)
                elif log.direction.lower() == 'out device':
                    return self._handle_out_log(employee, log)
            return False
        except Exception as e:
            # self.logger.error(f"Error processing log for employee {log.employeeid}: {str(e)}")
            return False

    def _handle_in_log(self, employee: Employee, log: Logs) -> bool:
        """
        Handle incoming attendance log.
        Only creates attendance if it's the first valid IN of the day.
        """
        try:
            # Convert to naive datetime if timezone-aware
            if timezone.is_aware(log.log_datetime):
                log_datetime = timezone.make_naive(log.log_datetime)
            else:
                log_datetime = log.log_datetime
                
            log_time = log_datetime.time()
            log_date = log_datetime.date()
            
            # Check if there's already an attendance record for this day
            existing_attendance = Attendance.objects.filter(
                employeeid=employee,
                logdate=log_date
            ).first()

            # Find the matching shift for this IN punch
            for auto_shift in AutoShift.objects.all():
                try:
                    shift_window = self._calculate_shift_window(auto_shift, log_datetime)
                        
                    if shift_window.start_window <= log_time <= shift_window.end_window:

                        if existing_attendance and existing_attendance.first_logtime is None:
                            # Only update existing attendance if first_logtime is None
                            attendance = existing_attendance
                            attendance.first_logtime = log_time
                            attendance.shift = auto_shift.name
                            attendance.direction = 'Machine'
                            attendance.shift_status = 'MP'
                        
                        else:
                            attendance = Attendance.objects.create(
                                employeeid=employee,
                                logdate=log_date,
                                first_logtime=log_time,
                                shift=auto_shift.name,
                                direction='Machine',
                                shift_status='MP'
                            )

                        if log_time > shift_window.start_time_with_grace:
                            attendance.late_entry = datetime.combine(
                                log_date,
                                log_time
                            ) - datetime.combine(
                                log_date,
                                auto_shift.start_time
                            )
                            
                        attendance.save()
                        # self.logger.info(
                        #     f"Created attendance record for employee {employee.employee_id} "
                        #     f"with first IN at {log_time}"
                        # )
                        return True
                except Exception as e:
                    # self.logger.error(f"Error processing shift {auto_shift.name}: {str(e)}")
                    continue

            return True

        except Exception as e:
            # self.logger.error(f"Error in _handle_in_log: {str(e)}")
            return False

    def _handle_out_log(self, employee: Employee, log: Logs) -> bool:
        """
        Handle outgoing attendance log.
        Updates the last OUT time of an existing attendance record.
        """
        try:
            # Convert to naive datetime if timezone-aware
            if timezone.is_aware(log.log_datetime):
                log_datetime = timezone.make_naive(log.log_datetime)
            else:
                log_datetime = log.log_datetime
                
                
            log_time = log_datetime.time()
            log_date = log_datetime.date()

            # First check if there are any earlier logs for this day
            attendance = Attendance.objects.filter(
                employeeid=employee,
                logdate=log_date,
                first_logtime__isnull=False
            ).first()

            if not attendance:
                prev_date = log_date - timedelta(days=1)
                attendance = Attendance.objects.filter(
                    employeeid=employee,
                    logdate=prev_date,
                    first_logtime__isnull=False,
                    last_logtime__isnull=True  # Must not have an OUT punch already
                ).first()

                if not attendance:
                    # self.logger.warning(f"No valid IN log found for employee {employee.employee_id} before OUT")
                    return True
            
            if not attendance:
                # self.logger.warning(f"No valid IN log found for employee {employee.employee_id} before OUT")
                return True

            # Get the shift details
            try:
                auto_shift = AutoShift.objects.get(name=attendance.shift)
            except AutoShift.DoesNotExist:
                # self.logger.error(f"Shift {attendance.shift} not found for employee {employee.employee_id}")
                return False
            
            # Check if this is a valid OUT punch for the attendance
            in_datetime = datetime.combine(attendance.logdate, attendance.first_logtime)
            if auto_shift.is_night_shift() and log_date > attendance.logdate:
                # If it's next day and night shift, adjust OUT time comparison
                out_datetime = log_datetime
            else:
                # For same day comparison
                out_datetime = datetime.combine(attendance.logdate, log_time)
            
            if auto_shift.is_night_shift():
                # For night shift, OUT can be next day
                shift_end = datetime.combine(
                    attendance.logdate + timedelta(days=1) if auto_shift.is_night_shift() else attendance.logdate, 
                    auto_shift.end_time
                )
            else:
                # For regular shift, OUT should be same day
                shift_end = datetime.combine(
                    attendance.logdate, 
                    auto_shift.end_time
                )

            # Update attendance if this OUT is after IN and the latest one
            if out_datetime > in_datetime:
                if not attendance.last_logtime or out_datetime.time() > attendance.last_logtime:
                    attendance.last_logtime = log_time
                    attendance.direction = 'Machine'

                    # Calculate total time
                    total_time = out_datetime - in_datetime
                    attendance.total_time = total_time

                    # Calculate early exit
                    if out_datetime < shift_end:
                        attendance.early_exit = shift_end - out_datetime
                    else:
                        attendance.early_exit = None

                    # Calculate overtime
                    overtime_threshold = shift_end + auto_shift.overtime_threshold_after_end
                    if out_datetime > overtime_threshold:
                        attendance.overtime = out_datetime - shift_end
                    else:
                        attendance.overtime = None

                    # Update status
                    if attendance.logdate.weekday() in WEEK_OFF_CONFIG['DEFAULT_WEEK_OFF']:
                        attendance.shift_status = 'WW'
                    else:
                        attendance.shift_status = (
                            'P' if total_time > auto_shift.half_day_threshold 
                            else 'HD'
                        )

                    attendance.save()
                    # self.logger.info(
                    #     f"Updated attendance for employee {employee.employee_id}: "
                    #     f"Date: {attendance.logdate}, "
                    #     f"IN: {attendance.first_logtime}, "
                    #     f"OUT: {log_time}"
                    # )

            return True

        except Exception as e:
            # self.logger.error(f"Error in _handle_out_log for employee {employee.employee_id}: {str(e)}")
            return False

    def _calculate_shift_window(self, auto_shift: AutoShift, log_datetime: datetime) -> ShiftWindow:
        """Calculate shift time windows handling timezone-aware datetimes."""
        try:
            # Ensure we're working with naive datetime
            if timezone.is_aware(log_datetime):
                log_datetime = timezone.make_naive(log_datetime)
                
            base_date = log_datetime.date()
            
            # Calculate start and end times
            start_time = datetime.combine(base_date, auto_shift.start_time)
            end_time = datetime.combine(
                base_date + timedelta(days=1) if auto_shift.is_night_shift() else base_date,
                auto_shift.end_time
            )
            
            # Calculate window times
            start_window = (start_time - auto_shift.tolerance_start_time).time()
            end_window = (start_time + auto_shift.tolerance_end_time).time()
            
            return ShiftWindow(
                start_time=start_time,
                end_time=end_time,
                start_window=start_window,
                end_window=end_window,
                start_time_with_grace=(start_time + auto_shift.grace_period_at_start_time).time(),
                end_time_with_grace=(end_time - auto_shift.grace_period_at_end_time).time(),
                overtime_before_start=auto_shift.overtime_threshold_before_start,
                overtime_after_end=auto_shift.overtime_threshold_after_end,
                half_day_threshold=auto_shift.half_day_threshold
            )
        except Exception as e:
            # self.logger.error(f"Error in _calculate_shift_window: {str(e)}")
            raise

    def _create_or_update_attendance(self, employee: Employee, log_datetime: datetime, 
                                   shift_name: str, shift_window: ShiftWindow) -> Optional[Attendance]:
        """Create or update attendance record for incoming log."""
        try:
            log_time = log_datetime.time()
            attendance, created = Attendance.objects.update_or_create(
                employeeid=employee,
                logdate=log_datetime.date(),
                defaults={
                    'first_logtime': log_time,
                    'shift': shift_name,
                    'direction': 'Machine',
                    'shift_status': 'MP'
                }
            )

            if log_time > shift_window.start_time_with_grace:
                attendance.late_entry = log_datetime - shift_window.start_time
                
            attendance.save()
            return attendance
        except Exception as e:
            # self.logger.error(f"Error in _create_or_update_attendance: {str(e)}")
            return None

    def _get_attendance_record(self, employee: Employee, log_datetime: datetime) -> Optional[Attendance]:
        """
        Get existing attendance record for outgoing log.
        Only matches with attendance records that have an in-time before this out-time.
        """
        try:
            # First try to find an attendance record from the same day
            # but only if the first_logtime is before our out-time
            current_day_attendance = Attendance.objects.filter(
                employeeid=employee,
                logdate=log_datetime.date(),
                first_logtime__isnull=False,
                first_logtime__lt=log_datetime.time(),
                last_logtime__isnull=True  # Ensure we haven't already processed an out-time
            ).first()
            
            if current_day_attendance:
                return current_day_attendance

            # If no valid same-day record found, check previous day
            # This handles overnight shifts
            previous_day = log_datetime.date() - timedelta(days=1)
            previous_day_attendance = Attendance.objects.filter(
                employeeid=employee,
                logdate=previous_day,
                first_logtime__isnull=False,
                last_logtime__isnull=True  # Ensure we haven't already processed an out-time
            ).first()
            
            if previous_day_attendance:
                return previous_day_attendance

            # self.logger.warning(
            #     f"No valid IN log found for employee {employee.employee_id} "
            #     f"before out-time {log_datetime}"
            # )
            return None
            
        except Exception as e:
            # self.logger.error(
            #     f"Error in _get_attendance_record for employee {employee.employee_id}: {str(e)}"
            # )
            return None

    def _update_attendance_out_log(self, attendance: Attendance, log_datetime: datetime, 
                                 shift_window: ShiftWindow, is_night_shift: bool):
        """Update attendance record for outgoing log."""
        try:
            log_time = log_datetime.time()
            attendance.last_logtime = log_time
            attendance.direction = 'Machine'

            if log_time < shift_window.end_time_with_grace:
                attendance.early_exit = shift_window.end_time - log_datetime

            if is_night_shift:
                attendance.total_time = (
                    timezone.make_aware(datetime.combine(attendance.logdate, attendance.last_logtime) + 
                                      timedelta(days=1)) - 
                    timezone.make_aware(datetime.combine(attendance.logdate, attendance.first_logtime))
                )
            else:
                attendance.total_time = (
                    log_datetime - 
                    timezone.make_aware(datetime.combine(log_datetime.date(), attendance.first_logtime))
                )
            
            if attendance.logdate.weekday() in WEEK_OFF_CONFIG['DEFAULT_WEEK_OFF']:
                attendance.shift_status = 'WW' 
            else:
                attendance.shift_status = 'P' if attendance.total_time > shift_window.half_day_threshold else 'HD'
            
            self._calculate_overtime(attendance, shift_window)
            attendance.save()
        except Exception as e:
            # self.logger.error(f"Error in _update_attendance_out_log: {str(e)}")
            raise

    def _calculate_overtime(self, attendance: Attendance, shift_window: ShiftWindow):
        """Calculate overtime for attendance record."""
        try:
            first_log_time = timezone.make_aware(
                datetime.combine(attendance.logdate, attendance.first_logtime)
            )
            last_log_time = timezone.make_aware(
                datetime.combine(attendance.logdate, attendance.last_logtime)
            )

            if (first_log_time < (shift_window.start_time - shift_window.overtime_before_start) or 
                last_log_time > (shift_window.end_time + shift_window.overtime_after_end)):
                
                start_overtime = (
                    (shift_window.start_time - first_log_time)
                    if first_log_time < (shift_window.start_time - shift_window.overtime_before_start)
                    else timedelta(0)
                )
                
                end_overtime = (
                    (last_log_time - shift_window.end_time)
                    if last_log_time > (shift_window.end_time + shift_window.overtime_after_end)
                    else timedelta(0)
                )
                
                total_overtime = start_overtime + end_overtime
                if total_overtime > timedelta(0):
                    attendance.overtime = total_overtime

        except Exception as e:
            # self.logger.error(f"Error in _calculate_overtime: {str(e)}")
            raise

# Function to be imported by tasks.py
def process_attendance(employeeid: str, log_datetime: datetime, direction: str) -> bool:
    """
    Process attendance record for a given log.
    
    Args:
        employeeid: Employee ID string
        log_datetime: Datetime of the log
        direction: Direction of the log ('In Device' or 'Out Device')
        
    Returns:
        bool: True if processing was successful, False otherwise
    """
    processor = AttendanceProcessor()
    log = Logs(
        employeeid=employeeid,
        log_datetime=log_datetime,
        direction=direction
    )
    return processor.process_single_log(log)
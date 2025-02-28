# attendance_business_logic.py (New file name for better organization)
from datetime import datetime, timedelta, time
from dataclasses import dataclass
from typing import Optional, Tuple
from functools import reduce
import operator
from django.db.models import Q, F, Max
from tqdm import tqdm
import gc
from django.db import models, transaction
from django.utils import timezone
from django.utils.timezone import make_aware, timezone, now

from config.models import AutoShift, Shift
from resource.models import Employee, Logs, Attendance, LastLogId
from value_config import WEEK_OFF_CONFIG

import logging

logger = logging.getLogger(__name__)

@dataclass
class ShiftWindow:
    """
    Data class to represent a shift window with various time boundaries.

    Attributes:
        name (str): Name of the shift.
        start_time (datetime): The official start time of the shift.
        end_time (datetime): The official end time of the shift.
        start_window (datetime): The earliest time a log can be considered for this shift (start time - tolerance).
        end_window (datetime): The latest time a log can be considered for this shift (start time + tolerance).
        start_time_with_grace (datetime): Start time with added grace period for late entry.
        end_time_with_grace (datetime): End time with grace period for early exit.
        overtime_before_start (timedelta): Overtime threshold before the shift start.
        overtime_after_end (timedelta): Overtime threshold after the shift end.
        half_day_threshold (timedelta): Threshold for considering attendance as half-day.
    """
    name: str
    start_time: datetime
    end_time: datetime
    start_window: datetime
    end_window: datetime
    start_time_with_grace: datetime
    end_time_with_grace: datetime
    overtime_before_start: timedelta
    overtime_after_end: timedelta
    half_day_threshold: timedelta


class ShiftCalculator:
    """
    Module responsible for calculating shift windows based on AutoShift configurations.
    """
    def __init__(self, auto_shifts):
        """
        Initializes ShiftCalculator with a list of AutoShift objects.

        Args:
            auto_shifts (list[AutoShift]): List of AutoShift configurations.
        """
        self.auto_shifts = auto_shifts
        self.logger = logging.getLogger(__name__)

    def calculate_autoshift_window(self, auto_shift: AutoShift, log_datetime: datetime) -> ShiftWindow:
        """
        Calculates the shift window for a given AutoShift and log datetime.

        This method determines the appropriate shift window by considering the shift timings,
        tolerance periods, and special cases like midnight shifts. It handles both regular day shifts
        and night shifts that may cross midnight.

        Args:
            auto_shift (AutoShift): The AutoShift configuration to calculate the window for.
            log_datetime (datetime): The datetime of the log being processed.

        Returns:
            ShiftWindow: A ShiftWindow object representing the calculated shift window.

        Raises:
            Exception: If there is an error during shift window calculation.

        Edge Cases Handled:
            - Midnight shifts (start_time or end_time at 00:00).
            - Night shifts crossing midnight (end_time < start_time).
            - Timezone awareness of log_datetime is handled by converting to naive datetime.
        """
        try:
            # Ensure we're working with naive datetime
            if timezone.is_aware(log_datetime):
                log_datetime = timezone.make_naive(log_datetime)

            base_date = log_datetime.date()
            log_time = log_datetime.time()

            name = auto_shift.name

            # Special handling for midnight shift (00:00 start time)
            if auto_shift.start_time == time(0, 0):
                # If log time is between 23:00 and midnight
                if time(23, 0) <= log_time <= time(23, 59, 59):
                    base_date = base_date + timedelta(days=1)

            if auto_shift.end_time == time(0, 0):
                # If log time is between midnight and 01:00
                if time(0, 0) <= log_time <= time(1, 0):
                    base_date = base_date - timedelta(days=1)

            # Calculate start and end times
            start_time = datetime.combine(base_date, auto_shift.start_time)
            end_time = datetime.combine(
                base_date + timedelta(days=1) if auto_shift.is_night_shift() and auto_shift.end_time < auto_shift.start_time else base_date,
                auto_shift.end_time
            )

            # Calculate window times
            if auto_shift.start_time == time(0, 0):
                start_window = start_time - timedelta(hours=1)  # One hour before midnight
            else:
                start_window = start_time - auto_shift.tolerance_start_time

            end_window = start_time + auto_shift.tolerance_end_time

            return ShiftWindow(
                name=name,
                start_time=start_time,
                end_time=end_time,
                start_window=start_window,
                end_window=end_window,
                start_time_with_grace=start_time + auto_shift.grace_period_at_start_time,
                end_time_with_grace=end_time - auto_shift.grace_period_at_end_time,
                overtime_before_start=auto_shift.overtime_threshold_before_start,
                overtime_after_end=auto_shift.overtime_threshold_after_end,
                half_day_threshold=auto_shift.half_day_threshold
            )
        except Exception as e:
            self.logger.error(f"Error in calculate_autoshift_window: {str(e)}")
            raise


class AttendanceCalculator:
    """
    Module responsible for calculating attendance details like total time, overtime, and shift status.
    """
    def __init__(self, shifts, auto_shifts, employees):
        """
        Initializes AttendanceCalculator with shift configurations and employee data.

        Args:
            shifts (dict[int, Shift]): Dictionary of Shift objects, keyed by shift ID.
            auto_shifts (dict[str, AutoShift]): Dictionary of AutoShift objects, keyed by shift name.
            employees (dict[str, Employee]): Dictionary of Employee objects, keyed by employee ID.
        """
        self.shifts = shifts
        self.auto_shifts = auto_shifts
        self.employees = employees
        self.logger = logging.getLogger(__name__)

    def calculate_attendance_details_autoshift(self, attendance: Attendance, auto_shift: AutoShift):
        """
        Calculates and updates attendance details for an employee under AutoShift.

        This method calculates total time, early exit, overtime, and shift status based on
        the IN and OUT times in the attendance record and the provided AutoShift configuration.

        Args:
            attendance (Attendance): The Attendance record to update.
            auto_shift (AutoShift): The AutoShift configuration associated with the attendance.

        Edge Cases Handled:
            - Night shifts crossing midnight are correctly handled for time calculations.
            - Lunch break deduction based on AutoShift configuration.
            - Week off status based on employee's week off day configuration.
            - Absent, Half-Day, Incomplete Half-day, and Present statuses based on thresholds.
        """
        try:
            in_datetime = datetime.combine(attendance.logdate, attendance.first_logtime)
            out_datetime = datetime.combine(attendance.logdate, attendance.last_logtime)

            total_time = out_datetime - in_datetime

            # Deduct lunch break if applicable
            if auto_shift.include_lunch_break_in_half_day or auto_shift.include_lunch_break_in_full_day:
                if auto_shift.lunch_duration:
                    total_time -= auto_shift.lunch_duration
                    if total_time < timedelta():
                        total_time = timedelta()
            attendance.total_time = total_time

            # Calculate shift timing
            shift_start = datetime.combine(in_datetime.date(), auto_shift.start_time)

            if not auto_shift.is_night_shift():
                if auto_shift.start_time == time(0, 0):
                    if in_datetime.time() > auto_shift.end_time:
                        shift_end = datetime.combine(in_datetime.date() + timedelta(days=1), auto_shift.end_time)
                else:
                    shift_end = datetime.combine(in_datetime.date(), auto_shift.end_time)
            else:
                shift_end = datetime.combine(in_datetime.date() + timedelta(days=1), auto_shift.end_time)
            shift_end_with_grace = shift_end - auto_shift.grace_period_at_end_time

            # Early exit calculation
            if out_datetime < shift_end_with_grace:
                attendance.early_exit = shift_end - out_datetime
            else:
                attendance.early_exit = None

            # Overtime calculation
            overtime_threshold_before = shift_start - auto_shift.overtime_threshold_before_start
            overtime_threshold_after = shift_end + auto_shift.overtime_threshold_after_end

            overtime_before = max(timedelta(), shift_start - in_datetime) if in_datetime < overtime_threshold_before else timedelta()
            overtime_after = max(timedelta(), out_datetime - shift_end) if out_datetime > overtime_threshold_after else timedelta()

            # Shift status determination
            employee = attendance.employeeid
            first_weekoff = employee.first_weekly_off
            weekoff_days = [first_weekoff] if first_weekoff is not None else WEEK_OFF_CONFIG.get('DEFAULT_WEEK_OFF', [])

            if attendance.logdate.weekday() in weekoff_days:
                attendance.overtime = total_time
            else:
                attendance.overtime = overtime_before + overtime_after if (overtime_before + overtime_after) > timedelta() else None

            if attendance.logdate.weekday() in weekoff_days:
                attendance.shift_status = 'WW'
            elif auto_shift.absent_threshold is not None and total_time < auto_shift.absent_threshold:
                attendance.shift_status = 'A'
            elif auto_shift.half_day_threshold is not None and total_time < auto_shift.half_day_threshold:
                attendance.shift_status = 'HD'
            elif auto_shift.full_day_threshold is not None and total_time < auto_shift.full_day_threshold:
                attendance.shift_status = 'IH'
            else:
                attendance.shift_status = 'P'

        except Exception as e:
            self.logger.error(f"Error calculating attendance details for auto shift: {str(e)}")
            raise

    def calculate_attendance_details_fixedshift(self, attendance: Attendance, shift: Shift):
        """
        Calculates and updates attendance details for an employee under Fixed Shift.

        Similar to `calculate_attendance_details_autoshift`, but tailored for Fixed Shift configurations.

        Args:
            attendance (Attendance): The Attendance record to update.
            shift (Shift): The Shift configuration associated with the attendance.

        Edge Cases Handled:
            - Night shifts and lunch break deductions are handled based on Shift configuration.
            - Week off and status calculations are based on Shift and Employee configurations.
        """
        try:
            in_datetime = datetime.combine(attendance.logdate, attendance.first_logtime)
            out_datetime = datetime.combine(attendance.logdate, attendance.last_logtime)

            # Adjust for night shifts crossing midnight
            if shift.is_night_shift() and in_datetime > out_datetime:
                in_datetime -= timedelta(days=1)

            total_time = out_datetime - in_datetime

            # Deduct lunch break if applicable
            if shift.include_lunch_break_in_half_day or shift.include_lunch_break_in_full_day:
                if shift.lunch_duration:
                    total_time -= shift.lunch_duration
                    if total_time < timedelta():
                        total_time = timedelta()
            attendance.total_time = total_time

            # Calculate shift timing
            shift_start = datetime.combine(in_datetime.date(), shift.start_time)
            shift_end = datetime.combine(out_datetime.date(), shift.end_time)
            shift_end_with_grace = shift_end - shift.grace_period_at_end_time

            # Early exit calculation
            if out_datetime < shift_end_with_grace:
                attendance.early_exit = shift_end - out_datetime
            else:
                attendance.early_exit = None

            # Overtime calculation
            overtime_threshold_before = shift_start - shift.overtime_threshold_before_start
            overtime_threshold_after = shift_end + shift.overtime_threshold_after_end

            overtime_before = max(timedelta(), shift_start - in_datetime) if in_datetime < overtime_threshold_before else timedelta()
            overtime_after = max(timedelta(), out_datetime - shift_end) if out_datetime > overtime_threshold_after else timedelta()

            # Shift status determination
            employee = attendance.employeeid
            first_weekoff = employee.first_weekly_off
            weekoff_days = [first_weekoff] if first_weekoff is not None else WEEK_OFF_CONFIG.get('DEFAULT_WEEK_OFF', [])

            if attendance.logdate.weekday() in weekoff_days:
                attendance.overtime = total_time
            else:
                attendance.overtime = overtime_before + overtime_after if (overtime_before + overtime_after) > timedelta() else None

            if attendance.logdate.weekday() in weekoff_days:
                attendance.shift_status = 'WW'
            elif shift.absent_threshold is not None and total_time < shift.absent_threshold:
                attendance.shift_status = 'A'
            elif shift.half_day_threshold is not None and total_time < shift.half_day_threshold:
                attendance.shift_status = 'HD'
            elif shift.full_day_threshold is not None and total_time < shift.full_day_threshold:
                attendance.shift_status = 'IH'
            else:
                attendance.shift_status = 'P'

        except Exception as e:
            self.logger.error(f"Error calculating attendance details for fixed shift: {str(e)}")
            raise


class LogProcessor:
    """
    Module responsible for processing individual attendance logs and updating Attendance records.

    This module handles both 'IN' and 'OUT' logs, distinguishes between AutoShift and Fixed Shift employees,
    and delegates shift window calculations and attendance detail calculations to respective modules.
    """
    def __init__(self, auto_shifts, shifts, employees, shift_calculator, attendance_calculator):
        """
        Initializes LogProcessor with shift configurations, employee data, and calculator modules.

        Args:
            auto_shifts (dict[str, AutoShift]): Dictionary of AutoShift objects, keyed by shift name.
            shifts (dict[int, Shift]): Dictionary of Shift objects, keyed by shift ID.
            employees (dict[str, Employee]): Dictionary of Employee objects, keyed by employee ID.
            shift_calculator (ShiftCalculator): Instance of ShiftCalculator for shift window calculations.
            attendance_calculator (AttendanceCalculator): Instance of AttendanceCalculator for attendance detail calculations.
        """
        self.auto_shifts = auto_shifts
        self.shifts = shifts
        self.employees = employees
        self.shift_calculator = shift_calculator
        self.attendance_calculator = attendance_calculator
        self.logger = logging.getLogger(__name__)

    def process_single_log(self, log: Logs, is_manual=False) -> bool:
        """
        Processes a single attendance log entry.

        This method determines if the log is an 'IN' or 'OUT' log, identifies the employee's shift type (Auto or Fixed),
        and calls the appropriate handler function to process the log and update the Attendance record.

        Args:
            log (Logs): The Logs object representing the attendance log entry.
            is_manual (bool, optional): Flag indicating if the log is manually entered. Defaults to False.

        Returns:
            bool: True if the log was processed successfully, False otherwise.

        Edge Cases Handled:
            - Empty or non-existent employee IDs in logs are handled gracefully.
            - Employees not found in the system are logged and processing continues.
            - Delegates processing to different handlers based on employee's shift type.
        """
        print(f"Processing log for employee: {log} {log.employeeid}, Time: {log.log_datetime}, Direction: {log.direction}, Manual: {is_manual}")

        if not log.employeeid:
            self.logger.error("Empty employee ID in log")
            return False

        employee = self.employees.get(log.employeeid)
        if not employee:
            self.logger.error(f"Employee with ID: {log.employeeid} not found.")
            return False

        try:
            direction = log.direction.lower()
            if employee.shift: # Fixed Shift Employee
                if direction == 'in device':
                    return self._handle_in_log_fixedshift(employee, log, is_manual)
                elif direction == 'out device':
                    return self._handle_out_log_fixedshift(employee, log, is_manual)
            else: # Auto Shift Employee
                if direction == 'in device':
                    return self._handle_in_log_autoshift(employee, log, is_manual)
                elif direction == 'out device':
                    return self._handle_out_log_autoshift(employee, log, is_manual)
            return False # Should not reach here unless direction is invalid

        except Exception as e:
            self.logger.error(f"Error processing log for employee {log.employeeid}: {str(e)}")
            return False

    def _handle_in_log_autoshift(self, employee: Employee, log: Logs, is_manual: bool = False) -> bool:
        """
        Handles processing of 'IN' logs for AutoShift employees.

        Finds the matching AutoShift based on the log time, and updates or creates an Attendance record.

        Args:
            employee (Employee): The Employee object.
            log (Logs): The Logs object representing the 'IN' log.
            is_manual (bool, optional): Flag indicating if the log is manually entered. Defaults to False.

        Returns:
            bool: True if the log was processed successfully, False otherwise.
        """
        try:
            if timezone.is_aware(log.log_datetime):
                log_datetime = timezone.make_naive(log.log_datetime)
            else:
                log_datetime = log.log_datetime

            log_time = log_datetime.time()
            log_date = log_datetime.date()

            # Find the matching shift for this IN punch
            for auto_shift in self.auto_shifts.values(): # Iterate through auto_shifts dictionary
                try:
                    shift_window = self.shift_calculator.calculate_autoshift_window(auto_shift, log_datetime)

                    if shift_window.start_window <= log_datetime <= shift_window.end_window:
                        with transaction.atomic():  # Use a nested atomic block
                            existing_attendance = Attendance.objects.select_for_update().filter(
                                employeeid=employee,
                                logdate=shift_window.start_time.date()
                            ).first()

                            if existing_attendance:
                                if existing_attendance.first_logtime is None:
                                    attendance = existing_attendance
                                    attendance.first_logtime = log_time
                                    attendance.shift = auto_shift.name
                                    attendance.direction = 'Manual' if is_manual else 'Machine'
                                    attendance.shift_status = 'MP'
                                else:
                                    return True  # Already has first logtime, nothing to update for IN log
                            else:
                                attendance = Attendance(
                                    employeeid=employee,
                                    logdate=log_date,
                                    first_logtime=log_time,
                                    shift=auto_shift.name,
                                    direction='Manual' if is_manual else 'Machine',
                                    shift_status='MP'
                                )

                            if log_datetime > shift_window.start_time_with_grace:
                                attendance.late_entry = log_datetime - shift_window.start_time

                            attendance.save()
                            return True

                except Exception as e:
                    self.logger.error(f"Error processing shift {auto_shift.name} for employee {employee.employee_id} in _handle_in_log_autoshift: {str(e)}")
                    continue # Continue to next auto_shift if error occurs

            return True # Return True even if no shift is matched (as per original logic)

        except Exception as e:
            self.logger.exception(f"Error in _handle_in_log_autoshift for employee {employee.employee_id}: {str(e)}")
            return False

    def _handle_out_log_autoshift(self, employee: Employee, log: Logs, is_manual: bool = False) -> bool:
        """
        Handles processing of 'OUT' logs for AutoShift employees.

        Finds the corresponding 'IN' log, calculates attendance details, and updates or creates an Attendance record.

        Args:
            employee (Employee): The Employee object.
            log (Logs): The Logs object representing the 'OUT' log.
            is_manual (bool, optional): Flag indicating if the log is manually entered. Defaults to False.

        Returns:
            bool: True if the log was processed successfully, False otherwise.
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
                ).first()

                if not attendance:
                    # Create or update an OUT log with shift_status as 'MP' if no valid IN found
                    attendance = Attendance.objects.update_or_create(
                        employeeid=employee,
                        logdate=log_date,
                        defaults={
                            'last_logtime': log_time,
                            'shift': '',  # Or set it as needed
                            'direction': 'Manual' if is_manual else 'Machine',
                            'shift_status': 'MP',
                            'total_time': None, # set total_time to None for recalculation later
                            'early_exit': None, # set early_exit to None for recalculation later
                            'overtime': None, # set overtime to None for recalculation later
                        }
                    )[0]
                    attendance.save()
                    return True # Processed as OUT only, recalculation will handle details later

            if not attendance:
                self.logger.warning(f"No valid IN log found for employee {employee.employee_id} before OUT")
                return True # Return True even if no IN log found (as per original logic)

            # Get the shift details
            auto_shift = self.auto_shifts.get(attendance.shift)
            if not auto_shift:
                self.logger.error(f"Shift {attendance.shift} not found for employee {employee.employee_id}")
                return False

            # Check if this is a valid OUT punch for the attendance
            in_datetime = datetime.combine(attendance.logdate, attendance.first_logtime)
            out_datetime = log_datetime

            # Update attendance if this OUT is after IN and the latest one
            if out_datetime > in_datetime:
                if not attendance.last_logtime or out_datetime.time() > attendance.last_logtime:
                    attendance.last_logtime = log_time
                    attendance.direction = 'Manual' if is_manual else 'Machine'

                    self.attendance_calculator.calculate_attendance_details_autoshift(attendance, auto_shift)
                    attendance.save() # Save after calculating details
            elif out_datetime < in_datetime: # Handle cases where OUT time is earlier than IN time (next day OUT in night shift)
                if not attendance.last_logtime or out_datetime.time() > attendance.last_logtime:
                    attendance.last_logtime = log_time
                    attendance.direction = 'Manual' if is_manual else 'Machine'

                    in_datetime = datetime.combine(attendance.logdate, attendance.first_logtime) - timedelta(days=1) # Consider IN from previous day
                    self.attendance_calculator.calculate_attendance_details_autoshift(attendance, auto_shift)
                    attendance.save() # Save after calculating details

            return True

        except Exception as e:
            self.logger.error(f"Error in _handle_out_log_autoshift for employee {employee.employee_id}: {str(e)}")
            return False


    def _handle_in_log_fixedshift(self, employee: Employee, log: Logs, is_manual: bool = False) -> bool:
        """
        Handles processing of 'IN' logs for Fixed Shift employees.

        Updates or creates an Attendance record for fixed shift employees upon 'IN' log.

        Args:
            employee (Employee): The Employee object.
            log (Logs): The Logs object representing the 'IN' log.
            is_manual (bool, optional): Flag indicating if the log is manually entered. Defaults to False.

        Returns:
            bool: True if the log was processed successfully, False otherwise.
        """
        try:
            if timezone.is_aware(log.log_datetime):
                log_datetime = timezone.make_naive(log.log_datetime)
            else:
                log_datetime = log.log_datetime

            log_time = log_datetime.time()
            log_date = log_datetime.date()

            # Get the employee's fixed shift
            shift = self.shifts.get(employee.shift.id)
            if not shift:
                self.logger.error(f"Shift not found for employee {employee.employee_id}")
                return False

            shift_date = log_date # For fixed shift, date is usually log date

            try:
                with transaction.atomic():
                    existing_attendance = Attendance.objects.select_for_update().filter(
                        employeeid=employee,
                        logdate=shift_date
                    ).first()

                    if existing_attendance:
                        if existing_attendance.first_logtime is None:
                            attendance = existing_attendance
                            attendance.first_logtime = log_time
                            attendance.shift = shift.name
                            attendance.direction = 'Manual' if is_manual else 'Machine'
                            attendance.shift_status = 'MP'
                        else:
                            return True # Already has first logtime, nothing to update for IN log
                    else:
                        attendance = Attendance(
                            employeeid=employee,
                            logdate=shift_date,
                            first_logtime=log_time,
                            shift=shift.name,
                            direction='Manual' if is_manual else 'Machine',
                            shift_status='MP'
                        )

                    # Calculate shift start time for the current date
                    shift_start = datetime.combine(shift_date, shift.start_time)
                    shift_start_with_grace = shift_start + shift.grace_period_at_start_time

                    # Check for late entry
                    if log_datetime > shift_start_with_grace:
                        attendance.late_entry = log_datetime - shift_start

                    attendance.save()
                    return True

            except Exception as e:
                self.logger.error(f"Database error while processing IN log for employee {employee.employee_id}: {str(e)}")
                raise

        except Exception as e:
            self.logger.error(f"Error in _handle_in_log_fixedshift for employee {employee.employee_id}: {str(e)}")
            return False


    def _handle_out_log_fixedshift(self, employee: Employee, log: Logs, is_manual: bool = False) -> bool:
        """
        Handles processing of 'OUT' logs for Fixed Shift employees.

        Finds the corresponding 'IN' log, calculates attendance details, and updates or creates an Attendance record for fixed shift employees.

        Args:
            employee (Employee): The Employee object.
            log (Logs): The Logs object representing the 'OUT' log.
            is_manual (bool, optional): Flag indicating if the log is manually entered. Defaults to False.

        Returns:
            bool: True if the log was processed successfully, False otherwise.
        """
        try:
            # Convert to naive datetime if timezone-aware
            if timezone.is_aware(log.log_datetime):
                log_datetime = timezone.make_naive(log.log_datetime)
            else:
                log_datetime = log.log_datetime

            log_time = log_datetime.time()
            log_date = log_datetime.date()

            # Get the employee's fixed shift
            shift = self.shifts.get(employee.shift.id)
            if not shift:
                self.logger.error(f"Shift not found for employee {employee.employee_id}")
                return False

            # Determine the correct logdate and check for existing attendance
            if shift.is_night_shift():
                # For night shifts, the log might belong to the previous day's shift
                if log_time < shift.start_time:
                    # If log time is before shift start, it belongs to previous day
                    log_date = log_date - timedelta(days=1)

            # Check for existing attendance records
            existing_attendance = Attendance.objects.filter(
                employeeid=employee,
                logdate=log_date
            ).first()

            # Handle different scenarios
            if existing_attendance:
                # If an attendance record exists and has an IN time
                if existing_attendance.first_logtime:
                    # Update the OUT time if it's later or not set
                    if not existing_attendance.last_logtime or log_time > existing_attendance.last_logtime:
                        existing_attendance.last_logtime = log_time
                        existing_attendance.direction = 'Manual' if is_manual else 'Machine'

                        self.attendance_calculator.calculate_attendance_details_fixedshift(existing_attendance, shift)
                        existing_attendance.save() # Save after calculating details
                else:
                    # If no IN time, just update the OUT time
                    existing_attendance.last_logtime = log_time
                    existing_attendance.shift = shift.name
                    existing_attendance.direction = 'Manual' if is_manual else 'Machine'
                    existing_attendance.shift_status = 'MP'
                    existing_attendance.save()
            else:
                # Create a new attendance record with OUT time
                Attendance.objects.create(
                    employeeid=employee,
                    logdate=log_date,
                    last_logtime=log_time,
                    direction='Manual' if is_manual else 'Machine',
                    shift=shift.name,
                    shift_status='MP',
                    total_time=None, # set total_time to None for recalculation later
                    early_exit=None, # set early_exit to None for recalculation later
                    overtime=None, # set overtime to None for recalculation later
                )

            return True

        except Exception as e:
            self.logger.error(f"Error in _handle_out_log_fixedshift for employee {employee.employee_id}: {str(e)}", exc_info=True)
            return False


class AttendanceRecalculator:
    """
    Module responsible for recalculating attendance details for records that might have missed calculations,
    especially due to late 'IN' logs arriving after 'OUT' logs.
    """
    def __init__(self, shifts, auto_shifts, employees, attendance_calculator):
        """
        Initializes AttendanceRecalculator with shift configurations, employee data, and the attendance calculator module.

        Args:
            shifts (dict[int, Shift]): Dictionary of Shift objects, keyed by shift ID.
            auto_shifts (dict[str, AutoShift]): Dictionary of AutoShift objects, keyed by shift name.
            employees (dict[str, Employee]): Dictionary of Employee objects, keyed by employee ID.
            attendance_calculator (AttendanceCalculator): Instance of AttendanceCalculator for attendance detail calculations.
        """
        self.shifts = shifts
        self.auto_shifts = auto_shifts
        self.employees = employees
        self.attendance_calculator = attendance_calculator
        self.logger = logging.getLogger(__name__)

    @transaction.atomic
    def recalculate_attendance_on_late_in_log(self):
        """
        Recalculates attendance for records where 'first_logtime' was likely updated after 'last_logtime' was set.

        This addresses the scenario where 'In' logs arrive after 'Out' logs have been processed.
        It queries for Attendance records that have both 'first_logtime' and 'last_logtime' but are missing
        calculated fields like 'total_time'. It then recalculates these fields based on the employee's shift type.

        Edge Cases Handled:
            - Handles both AutoShift and Fixed Shift employees for recalculation.
            - Skips recalculation if attendance record already has 'total_time' calculated (idempotent operation).
            - Logs errors if shift information is missing for an attendance record.
        """
        print("Recalculating attendance for potential late IN logs...")
        attendances_to_recalculate = Attendance.objects.filter(
            last_logtime__isnull=False,
            first_logtime__isnull=False,
            total_time__isnull=True # Assuming total_time is None when calculations are missed initially
        )

        if not attendances_to_recalculate:
            print("No attendance records found for recalculation.")
            return

        print(f"Found {attendances_to_recalculate.count()} attendance records to recalculate.")

        for attendance in tqdm(attendances_to_recalculate, desc="Recalculating Attendance"):
            employee = attendance.employeeid
            if employee.shift: # Fixed Shift Employee
                shift = self.shifts.get(employee.shift.id)
                if shift:
                    self._recalculate_fixed_shift_attendance(attendance, shift, employee)
                else:
                    self.logger.error(f"Fixed Shift not found for attendance record ID: {attendance.id}, Employee: {employee.employee_id}")
            else: # Auto Shift Employee
                auto_shift_name = attendance.shift
                if auto_shift_name:
                    auto_shift = self.auto_shifts.get(auto_shift_name)
                    if auto_shift:
                        self._recalculate_auto_shift_attendance(attendance, auto_shift, employee)
                    else:
                        self.logger.error(f"AutoShift '{auto_shift_name}' not found for attendance record ID: {attendance.id}, Employee: {employee.employee_id}")
                else:
                    self.logger.warning(f"No shift information found for attendance record ID: {attendance.id}, Employee: {employee.employee_id}")


    def _recalculate_fixed_shift_attendance(self, attendance: Attendance, shift: Shift, employee: Employee):
        """
        Recalculates attendance details for fixed shift employees.

        Called by `recalculate_attendance_on_late_in_log` to specifically handle Fixed Shift attendance records.

        Args:
            attendance (Attendance): The Attendance record to recalculate.
            shift (Shift): The Shift configuration.
            employee (Employee): The Employee object.
        """
        try:
            self.attendance_calculator.calculate_attendance_details_fixedshift(attendance, shift)
            attendance.save() # Save after recalculating details
        except Exception as e:
            self.logger.error(f"Error recalculating fixed shift attendance for record ID: {attendance.id}, Employee: {employee.employee_id}: {e}")


    def _recalculate_auto_shift_attendance(self, attendance: Attendance, auto_shift: AutoShift, employee: Employee):
        """
        Recalculates attendance details for auto shift employees.

        Called by `recalculate_attendance_on_late_in_log` to specifically handle AutoShift attendance records.

        Args:
            attendance (Attendance): The Attendance record to recalculate.
            auto_shift (AutoShift): The AutoShift configuration.
            employee (Employee): The Employee object.
        """
        try:
            self.attendance_calculator.calculate_attendance_details_autoshift(attendance, auto_shift)
            attendance.save() # Save after recalculating details
        except Exception as e:
            self.logger.error(f"Error recalculating auto shift attendance for record ID: {attendance.id}, Employee: {employee.employee_id}: {e}")



class AttendanceProcessor:
    """
    Main class to orchestrate attendance processing.

    This class initializes and coordinates the different modules responsible for processing logs,
    calculating shifts, attendance details, and handling recalculations. It acts as the entry point
    for processing new attendance logs from the 'Logs' table.
    """
    def __init__(self):
        """
        Initializes AttendanceProcessor, setting up dependencies and configurations.

        This constructor fetches AutoShifts, Shifts, and Employees from the database and initializes
        the ShiftCalculator, AttendanceCalculator, LogProcessor, and AttendanceRecalculator modules.
        """
        self.logger = logging.getLogger(__name__)

        self.auto_shifts_list = list(AutoShift.objects.all())
        self.auto_shift_dict = {shift.name: shift for shift in self.auto_shifts_list}
        self.shifts_dict = {shift.id: shift for shift in Shift.objects.all()}
        self.employees_dict = {emp.employee_id: emp for emp in Employee.objects.all()}

        self.shift_calculator = ShiftCalculator(self.auto_shifts_list)
        self.attendance_calculator = AttendanceCalculator(self.shifts_dict, self.auto_shift_dict, self.employees_dict)
        self.log_processor = LogProcessor(self.auto_shift_dict, self.shifts_dict, self.employees_dict, self.shift_calculator, self.attendance_calculator)
        self.attendance_recalculator = AttendanceRecalculator(self.shifts_dict, self.auto_shift_dict, self.employees_dict, self.attendance_calculator)


    @transaction.atomic
    def process_new_logs(self) -> bool:
        """
        Processes new attendance logs from the Logs table.

        This is the main entry point for attendance processing. It fetches new logs since the last processed log ID,
        processes them in batches using the LogProcessor, updates the last processed log ID, and then triggers
        attendance recalculation to handle any late 'IN' logs.

        Returns:
            bool: True if log processing was successful, False otherwise.

        Edge Cases Handled:
            - Handles cases with no new logs gracefully.
            - Processes logs in batches to manage memory and transaction size.
            - Uses tqdm for progress indication during log processing.
            - Calls AttendanceRecalculator to address late 'IN' log scenario.
        """
        try:
            last_log_id_record = LastLogId.objects.select_for_update().first()
            if not last_log_id_record:
                last_log_id_record = LastLogId.objects.create(last_log_id=0)

            last_processed_id = last_log_id_record.last_log_id
            new_logs = Logs.objects.filter(id__gt=last_processed_id).order_by('log_datetime')
            print(f"Processing new logs {new_logs}")

            if not new_logs:
                return True

            # Process logs in batches
            batch_size = 10000
            processed_logs = []

            # Calculate total number of logs
            total_logs = new_logs.count()

            # Use tqdm to show progress
            with tqdm(total=total_logs, desc="Processing logs", unit="log") as pbar:
                for i in range(0, total_logs, batch_size):
                    batch = new_logs[i:i + batch_size]
                    for log in batch:
                        if self.log_processor.process_single_log(log): # Use LogProcessor to process single log
                            processed_logs.append(log.id)
                        pbar.update(1)  # Update progress bar for each log

            if processed_logs:
                last_log_id_record.last_log_id = max(processed_logs)
                last_log_id_record.save()

            self.attendance_recalculator.recalculate_attendance_on_late_in_log() # Recalculate after processing logs

            return True
        except Exception as e:
            self.logger.error(f"Error in process_new_logs: {str(e)}")
            return False

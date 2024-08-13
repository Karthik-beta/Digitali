from datetime import datetime, timedelta, time
from typing import Optional

from django.db import models
from django.utils import timezone

from config.models import Shift, AutoShift
from resource.models import Employee, Logs, Attendance

import logging

logger = logging.getLogger(__name__)

class AttendanceService:
    """
    Manages employee attendance logic, including:

      - Processing employee logs.
      - Determining attendance details (first/last log, late entries, early exits).
      - Creating or updating attendance records.
    """

    def __init__(self, employeeid: int, log_datetime: datetime, direction: str):
        """
        Initializes the AttendanceService with log data.

        Args:
            employeeid (int): The ID of the employee.
            log_datetime (datetime): The datetime of the log.
            direction (str): The direction of the log ('IN', 'OUT', 'INOUT').
        """
        self.employeeid = employeeid
        self.log_datetime = log_datetime
        self.direction = direction

        self.employee = self.get_employee(employeeid)
        self.shift = self.get_employee_shift(self.employee)
        # self.auto_shift = self.get_employee_auto_shift(self.employee) 
        self.auto_shift = None
    
    @staticmethod
    def get_employee(employeeid: str) -> Optional[Employee]:
        """
        Fetches an employee from the database.

        Args:
            employeeid (int): The ID of the employee.

        Returns:
            Optional[Employee]: The Employee object if found, else None.
        """
        try:
            return Employee.objects.get(employee_id=employeeid)
        except Employee.DoesNotExist:
            logger.error(f"Employee with ID: {employeeid} not found.")
            return None

    @staticmethod
    def get_employee_shift(employee: Optional[Employee]) -> Optional[Shift]:
        """
        Gets the assigned shift for an employee.

        Args:
            employee (Optional[Employee]): The Employee object.

        Returns:
            Optional[Shift]: The Shift object if assigned, else None.
        """
        if employee:
            return employee.shift
        return None

    @staticmethod
    def get_employee_auto_shift(employee: Optional[Employee]) -> Optional[AutoShift]:
        """
        Gets the assigned auto shift for an employee.

        Args:
            employee (Optional[Employee]): The Employee object.

        Returns:
            Optional[AutoShift]: The AutoShift object if assigned, else None.
        """
        if employee and employee.auto_shift:  # Check if auto_shift is enabled
            return AutoShift.objects.first()
        return None

    def get_first_log(self) -> Optional[Logs]:
        """
        Get the first log of the employee for the log date.

        Returns:
            Optional[Logs]: The first Logs object for the day, else None.
        """
        try:
            if self.direction in ['IN', 'INOUT']:
                # if self.shift.night_shift and self.direction == 'IN':
                #     # For night shifts, search for the log 6 hours greater than previous day's end time if not return None
                #     return Logs.objects.filter(
                #         employeeid=self.employeeid, 
                #         log_datetime__date=self.log_datetime.date(), 
                #         log_datetime__gte=self.log_datetime + timedelta(hours=6)
                #     ).order_by('log_datetime').first()
                # else: 
                #     return None

                return Logs.objects.filter(
                    employeeid=self.employeeid, 
                    log_datetime__date=self.log_datetime.date()
                ).order_by('log_datetime').first()
            
            # if self.shift.night_shift and self.direction == 'IN':
            # # For night shifts, search for the log 6 hours greater than previous day's end time if not return None
            #     return Logs.objects.filter(
            #         employeeid=self.employeeid, 
            #         log_datetime__date=self.log_datetime.date(), 
            #         log_datetime__gte=self.log_datetime + timedelta(hours=6)
            #     ).order_by('log_datetime').first()
            
            if self.auto_shift and self.direction == 'IN':
                if not self.auto_shift.night_shift:
                    log_date = self.log_datetime.date()
                    first_log = Logs.objects.filter(
                        employeeid=self.employeeid,
                        log_datetime__date=log_date,
                        direction__in=['IN']
                    ).order_by('log_datetime').first()

                    return self.find_log_within_tolerance(first_log, self.auto_shift.start_time, self.auto_shift.tolerance_start_time)
                elif self.auto_shift.night_shift and self.direction == 'IN':
                    log_date = self.log_datetime.date()
                    first_log = Logs.objects.filter(
                        employeeid=self.employeeid,
                        log_datetime__date=log_date,
                        direction__in=['IN']
                    ).order_by('log_datetime').first()

                    return self.find_log_within_tolerance(first_log, self.auto_shift.start_time, self.auto_shift.tolerance_start_time)
            
            # else:
            #     return None
            
            return None
        
            
        except Logs.DoesNotExist:
            logger.error(f"No logs found for employee ID: {self.employeeid} on {self.log_datetime.date()}.")
            return None

    def get_last_log(self) -> Optional[Logs]:
        """
        Get the last log of the employee, considering night shifts.

        For night shifts ending on the next day, the log date is adjusted to search across days.

        Returns:
            Optional[Logs]: The last Logs object, else None.
        """
        try:
            if self.direction in ['OUT', 'INOUT']:
                if self.shift:
                    # Calculate shift start and end, handling night shifts
                    shift_start_time = datetime.combine(self.log_datetime.date(), self.shift.start_time)
                    if self.shift.night_shift and self.direction == 'OUT':
                        shift_end_time = datetime.combine(self.log_datetime.date() + timedelta(days=1), self.shift.end_time)
                        # If night shift, search from shift start time until end time on the next day
                        logs = Logs.objects.filter(
                            employeeid=self.employeeid,
                            log_datetime__range=(shift_start_time, shift_end_time)
                        ).order_by('-log_datetime')
                        # If no logs found within the shift on the current day and next day
                        if not logs: 
                            # Search for logs only on the next day 
                            shift_start_time = datetime.combine(self.log_datetime.date() + timedelta(days=1), datetime.min.time())
                            shift_end_time = datetime.combine(self.log_datetime.date() + timedelta(days=1), datetime.max.time())
                            logs = Logs.objects.filter(
                                employeeid=self.employeeid,
                                log_datetime__range=(shift_start_time, shift_end_time)
                            ).order_by('-log_datetime')
                        return logs.first()
                    
                    else:
                        shift_end_time = datetime.combine(self.log_datetime.date(), self.shift.end_time)
                        
                    # Apply timezone 
                    tz = timezone.get_current_timezone()
                    shift_start_time = timezone.make_aware(shift_start_time, tz)
                    shift_end_time = timezone.make_aware(shift_end_time, tz)

                    return Logs.objects.filter(
                        employeeid=self.employeeid,
                        log_datetime__range=(shift_start_time, shift_end_time)
                    ).order_by('-log_datetime').first()
                
                elif self.auto_shift:
                        if not self.auto_shift.night_shift and self.direction == 'OUT':
                            log_date = self.log_datetime.date()
                            last_log = Logs.objects.filter(
                                employeeid=self.employeeid,
                                log_datetime__date=log_date
                            ).order_by('-log_datetime').first()
                            print("Last log from fun", last_log, "shift", self.auto_shift.end_time)

                            for auto_shift in AutoShift.objects.all():  # Iterate over all AutoShift objects
                                log_time = last_log.log_datetime.time()
                                end_time = auto_shift.end_time
                                tolerance_start = auto_shift.tolerance_start_time
                                tolerance_end = auto_shift.tolerance_end_time

                                # Calculate the tolerance window
                                start_window = (datetime.combine(last_log.log_datetime.date(), end_time) - tolerance_start).time()
                                end_window = (datetime.combine(last_log.log_datetime.date(), end_time) + tolerance_end).time()

                                # Check if the log time falls within the tolerance window of any AutoShift
                                if start_window <= log_time <= end_window:
                                    # Found the matching AutoShift
                                    self.auto_shift = auto_shift  # Assign the matching auto_shift to the instance
                                    break  # No need to continue checking other AutoShifts

                            # If no matching AutoShift was found, log a warning
                            if self.auto_shift is None:
                                logger.warning(f"No matching AutoShift found for employee {self.employeeid} with first log time {last_log.log_datetime}")
                            
                            return self.find_log_within_tolerance(last_log, self.auto_shift.end_time, self.auto_shift.tolerance_end_time)
                        elif self.auto_shift.night_shift and self.direction == 'OUT':
                            shift_start_time = datetime.combine(self.log_datetime.date(), self.auto_shift.start_time)
                            shift_end_time = datetime.combine(self.log_datetime.date() + timedelta(days=1), self.auto_shift.end_time)
                            logs = Logs.objects.filter(
                            employeeid=self.employeeid,
                            log_datetime__range=(shift_start_time, shift_end_time)
                            ).order_by('-log_datetime')

                            if not logs: 
                                # Search for logs only on the next day 
                                shift_start_time = datetime.combine(self.log_datetime.date() + timedelta(days=1), datetime.min.time())
                                shift_end_time = datetime.combine(self.log_datetime.date() + timedelta(days=1), datetime.max.time())
                                logs = Logs.objects.filter(
                                    employeeid=self.employeeid,
                                    log_datetime__range=(shift_start_time, shift_end_time)
                                ).order_by('-log_datetime')
                            return logs.first()
                            
                            log_date = self.log_datetime.date()
                            # last_log = Logs.objects.filter(
                            #     employeeid=self.employeeid,
                            #     log_datetime__date=log_date,
                            #     direction__in=['OUT']
                            # ).order_by('-log_datetime').first()

                            return self.find_log_within_tolerance(last_log, self.auto_shift.end_time, self.auto_shift.tolerance_end_time)
                else:
                    # logger.warning(f"Employee {self.employeeid} has no shift assigned.")
                    # return None
                    log_date = self.log_datetime.date()
                    last_log = Logs.objects.filter(
                        employeeid=self.employeeid,
                        log_datetime__date=log_date
                    ).order_by('-log_datetime').first()

                    for auto_shift in AutoShift.objects.all():  # Iterate over all AutoShift objects
                        log_time = last_log.log_datetime.time()
                        end_time = auto_shift.end_time
                        tolerance_start = auto_shift.tolerance_start_time
                        tolerance_end = auto_shift.tolerance_end_time

                        # Calculate the tolerance window
                        start_window = (datetime.combine(last_log.log_datetime.date(), end_time) - tolerance_start).time()
                        end_window = (datetime.combine(last_log.log_datetime.date(), end_time) + tolerance_end).time()

                        # Check if the log time falls within the tolerance window of any AutoShift
                        if start_window <= log_time <= end_window:
                            # Found the matching AutoShift
                            self.auto_shift = auto_shift  # Assign the matching auto_shift to the instance
                            break  # No need to continue checking other AutoShifts
                    
                    # If no matching AutoShift was found, log a warning
                    if self.auto_shift is None:
                        logger.warning(f"No matching AutoShift found for employee {self.employeeid} with first log time {last_log.log_datetime}")
                    
                    return self.find_log_within_tolerance(last_log, self.auto_shift.end_time, self.auto_shift.tolerance_end_time)
                
                print("Last log Shift", last_log, self.auto_shift)
            return None
        except Logs.DoesNotExist:
            logger.error(f"No logs found for employee ID: {self.employeeid} on {self.log_datetime.date()}.")
            return None
        
    def find_log_within_tolerance(self, log: Optional[Logs], target_time: time, tolerance: timedelta) -> Optional[Logs]:
        """Helper function to check if a log is within tolerance of a target time."""
        if log is None:
            return None 
        log_date = log.log_datetime.date()
        tolerance_min = (datetime.combine(log_date, target_time) - tolerance).time()
        tolerance_max = (datetime.combine(log_date, target_time) + tolerance).time()
        if tolerance_min <= log.log_datetime.time() <= tolerance_max:
            return log
        return None

    @staticmethod
    def calculate_shift_times(log_date: datetime, shift: Shift) -> tuple[datetime, datetime]:
        """
        Calculate the start and end times of the shift, including grace periods.

        Args:
            log_date (datetime): The date of the log.
            shift (Shift): The Shift object.

        Returns:
            tuple[datetime, datetime]: The shift start and end datetime objects.
        """
        tz = timezone.get_current_timezone()
        shift_start_time = timezone.make_aware(datetime.combine(log_date, shift.start_time), tz)
        shift_end_time = timezone.make_aware(
            datetime.combine(log_date + timedelta(days=1), shift.end_time) 
            if shift.night_shift and shift.end_time < shift.start_time 
            else datetime.combine(log_date, shift.end_time), 
            tz
        )
        # Factor in grace periods
        shift_start_time += shift.grace_period_at_start_time
        shift_end_time -= shift.grace_period_at_end_time
        return shift_start_time, shift_end_time

    def calculate_late_entry(self, first_log: Logs, shift: Shift) -> timedelta:
        """
        Calculate the late entry duration for the employee.

        Args:
            first_log (Logs): The first Logs object of the day.
            shift (Shift): The Shift object.

        Returns:
            timedelta: The late entry duration, or timedelta(0) if not late.
        """
        if first_log and shift:
            shift_start_time, _ = self.calculate_shift_times(first_log.log_datetime.date(), shift)
            if first_log.log_datetime > shift_start_time:
                return first_log.log_datetime - (shift_start_time - shift.grace_period_at_start_time)
        return timedelta(0)
    
    def calculate_auto_shift_late_entry(self, first_log: Logs, auto_shift: AutoShift) -> timedelta:
        """
        Calculate late entry for auto shifts considering the tolerance.

        Args:
            first_log (Logs): The first log of the day.
            auto_shift (AutoShift): The AutoShift object.

        Returns:
            timedelta: The late entry duration, or timedelta(0) if not late.
        """
        if first_log and auto_shift and not auto_shift.night_shift:
            log_time = first_log.log_datetime.time()
            tolerance_start = (datetime.combine(first_log.log_datetime.date(), auto_shift.start_time) + 
                               auto_shift.tolerance_start_time).time() 
            if log_time > auto_shift.start_time:
                return datetime.combine(first_log.log_datetime.date(), log_time) - \
                       datetime.combine(first_log.log_datetime.date(), auto_shift.start_time)
        elif first_log and auto_shift and auto_shift.night_shift:
            log_time = first_log.log_datetime.time()
            tolerance_start = (datetime.combine(first_log.log_datetime.date(), auto_shift.start_time) + 
                               auto_shift.tolerance_start_time).time()
            if log_time > auto_shift.start_time:
                return datetime.combine(first_log.log_datetime.date(), log_time) - \
                       datetime.combine(first_log.log_datetime.date(), auto_shift.start_time)
        return timedelta(0)
    
    def calculate_auto_shift_early_exit(self, last_log: Logs, auto_shift: AutoShift) -> timedelta:
        """
        Calculate early exit for auto shifts considering the tolerance.

        Args:
            last_log (Logs): The last log of the day.
            auto_shift (AutoShift): The AutoShift object.

        Returns:
            timedelta: The early exit duration, or timedelta(0) if not early.
        """
        if last_log and auto_shift:
            log_time = last_log.log_datetime.time()
            tolerance_end = (datetime.combine(last_log.log_datetime.date(), auto_shift.end_time) - 
                             auto_shift.tolerance_end_time).time()
            print("early exit", log_time)
            if log_time < auto_shift.end_time:
                return datetime.combine(last_log.log_datetime.date(), auto_shift.end_time) - \
                       datetime.combine(last_log.log_datetime.date(), log_time)
        return timedelta(0)

    def calculate_auto_shift_overtime(self, first_log: Logs, last_log: Logs, log_date: Logs, auto_shift: AutoShift) -> Optional[timedelta]:
        """
        Calculate overtime for auto shifts based on thresholds.

        Args:
            first_log (Logs): The first log of the day.
            last_log (Logs): The last log of the day.
            auto_shift (AutoShift): The AutoShift object.

        Returns:
            Optional[timedelta]: The overtime duration, or None if no overtime.
        """
        if first_log and last_log and log_date and auto_shift:
            # log_date = first_log.log_datetime.date()
            first_logtime = datetime.combine(log_date, first_log)
            last_logtime = datetime.combine(log_date, last_log)
            overtime_start = (datetime.combine(log_date, auto_shift.start_time) - 
                              auto_shift.overtime_threshold_before_start)
            overtime_end = (datetime.combine(log_date, auto_shift.end_time) + 
                            auto_shift.overtime_threshold_after_end)
            
            overtime_end_time = overtime_end.time()

            if first_logtime < overtime_start:
                overtime_before = overtime_start - first_logtime
            else:
                overtime_before = timedelta(0)

            if last_logtime > overtime_end:
                overtime_after = (last_logtime -
                                 datetime.combine(log_date, overtime_end_time))
            else: 
                overtime_after = timedelta(0)
            
            total_overtime = overtime_before + overtime_after
            return total_overtime if total_overtime > timedelta(0) else None 
        return None

    def calculate_early_exit(self, last_log: Logs, shift: Shift) -> timedelta:
        """
        Calculate the early exit duration for the employee.

        Args:
            last_log (Logs): The last Logs object of the day.
            shift (Shift): The Shift object.

        Returns:
            timedelta: The early exit duration, or timedelta(0) if not early.
        """
        if last_log and shift:
            _, shift_end_time = self.calculate_shift_times(last_log.log_datetime.date(), shift)
            if not shift.night_shift:            
                if last_log.log_datetime < shift_end_time:
                    return (shift_end_time + shift.grace_period_at_end_time) - last_log.log_datetime
            if shift.night_shift and shift.end_time < shift.start_time:
                if last_log.log_datetime < shift_end_time:
                    return (shift_end_time + shift.grace_period_at_end_time) - (last_log.log_datetime + timedelta(days=1))
        return timedelta(0)

    def calculate_total_time(self, first_log: Logs, last_log: Logs) -> timedelta:
        """
        Calculate the total time worked between the first and last log.

        Args:
            first_log (Logs): The first Logs object of the day.
            last_log (Logs): The last Logs object of the day.

        Returns:
            timedelta: The total time worked.
        """
        if first_log and last_log:
            return last_log.log_datetime - first_log.log_datetime
        return timedelta(0)
    
    def calculate_auto_shift_total_time(self, first_log: Logs, last_log: Logs, log_date: Logs) -> timedelta:
        """
        Calculate the total time worked between the first and last log for auto shifts.

        Args:
            first_log (Logs): The first Logs object of the day.
            last_log (Logs): The last Logs object of the day.

        Returns:
            timedelta: The total time worked.
        """
        if first_log and last_log:
            first_logtime = datetime.combine(log_date, first_log)
            last_logtime = datetime.combine(log_date, last_log)
            return last_logtime - first_logtime
        return timedelta(0)

    def calculate_overtime(self, first_log: Logs, last_log: Logs, shift: Shift) -> Optional[timedelta]:
        """
        Calculate the overtime worked based on shift thresholds.

        Args:
            first_log (Logs): The first Logs object of the day.
            last_log (Logs): The last Logs object of the day.
            shift (Shift): The Shift object.

        Returns:
            Optional[timedelta]: The overtime duration, or None if no overtime.
        """
        if first_log and last_log and shift:
            shift_start_time, shift_end_time = self.calculate_shift_times(first_log.log_datetime.date(), shift)
            overtime_start = shift_start_time - shift.overtime_threshold_before_start
            overtime_end = shift_end_time + shift.overtime_threshold_after_end

            if last_log.log_datetime > overtime_end:
                return last_log.log_datetime - overtime_end
            if first_log.log_datetime < overtime_start:
                return overtime_start - first_log.log_datetime
        return None  # Explicitly return None for no overtime
    
    def calculate_lunch_in():
        return None

    def calculate_lunch_out():
        return None

    def calculate_lunch_duration(lunch_in, lunch_out):
        return None

    def process_attendance(self) -> bool:
        """
        Processes a single log entry to update attendance records.

        This function now tracks the IN/OUT state of employees to correctly 
        associate OUT punches with previous IN punches, even across days for 
        night shifts.

        Returns:
            bool: True if the attendance record is successfully processed and saved, 
                  False otherwise.
        """

        if not self.employee:
            logger.error(f"Could not process attendance. Employee not found for ID: {self.employeeid}")
            return False

        # Get or create Attendance record for the log date
        attendance, created = Attendance.objects.get_or_create(
            employeeid=self.employee,
            logdate=self.log_datetime.date(),
            defaults={'direction': 'Machine'} 
        )

        # Get the first log for the day
        first_log = self.get_first_log()
        if first_log:
            attendance.first_logtime = first_log.log_datetime.time()
            if self.employee.auto_shift:
                for auto_shift in AutoShift.objects.all():  # Iterate over all AutoShift objects
                    log_time = first_log.log_datetime.time()
                    start_time = auto_shift.start_time
                    end_time = auto_shift.end_time
                    tolerance_start = auto_shift.tolerance_start_time
                    tolerance_end = auto_shift.tolerance_end_time

                    # Calculate the tolerance window
                    start_window = (datetime.combine(first_log.log_datetime.date(), start_time) - tolerance_start).time()
                    end_window = (datetime.combine(first_log.log_datetime.date(), start_time) + tolerance_end).time()

                    # Check if the log time falls within the tolerance window of any AutoShift
                    if start_window <= log_time <= end_window:
                        # Found the matching AutoShift
                        self.auto_shift = auto_shift  # Assign the matching auto_shift to the instance
                        break  # No need to continue checking other AutoShifts

                # If no matching AutoShift was found, log a warning
                if self.auto_shift is None:
                    logger.warning(f"No matching AutoShift found for employee {self.employeeid} with first log time {first_log.log_datetime}")

        last_log = self.get_last_log()
        if last_log:
            attendance.last_logtime = last_log.log_datetime.time()
            if self.employee.auto_shift:
                for auto_shift in AutoShift.objects.all():
                    log_time = last_log.log_datetime.time()
                    start_time = auto_shift.start_time
                    end_time = auto_shift.end_time
                    tolerance_start = auto_shift.tolerance_start_time
                    tolerance_end = auto_shift.tolerance_end_time

                    # Calculate the tolerance window
                    start_window = (datetime.combine(last_log.log_datetime.date(), end_time) - tolerance_start).time()
                    end_window = (datetime.combine(last_log.log_datetime.date(), end_time) + tolerance_end).time()

                    # Check if the log time falls within the tolerance window of any AutoShift
                    if start_window <= log_time <= end_window:
                        # Found the matching AutoShift
                        self.auto_shift = auto_shift
                        break
            elif self.auto_shift.night_shift:
                    # Check if there's an existing attendance for the previous day with last_logtime not set
                yesterday = self.log_datetime.date() - timedelta(days=1)
                try:
                    previous_attendance = Attendance.objects.get(employeeid=self.employee, logdate=yesterday)
                    if not previous_attendance.last_logtime: 
                        # This OUT punch is likely associated with yesterday's IN
                        previous_attendance.last_logtime = self.log_datetime.time()
                        previous_attendance.save(update_fields=['last_logtime'])
                        logger.info(f"Updated previous day's attendance for employee {self.employeeid} with OUT punch.")
                    else:
                        # This is a regular OUT punch for the current day
                        attendance.last_logtime = self.log_datetime.time() 
                except Attendance.DoesNotExist:
                    # No attendance record for the previous day, treat as a regular OUT punch
                    attendance.last_logtime = self.log_datetime.time()


                # If no matching AutoShift was found, log a warning
                # if self.auto_shift is None:
                #    logger.warning(f"No matching AutoShift found for employee {self.employeeid} with last log time {last_log.log_datetime}")
                #   return False
                # return False      

        # Logic for handling last_logtime based on IN/OUT and night shifts
        if self.direction in ['OUT']:
            if (self.shift and self.shift.night_shift) or (self.auto_shift and self.auto_shift.night_shift):
                # Check if there's an existing attendance for the previous day with last_logtime not set
                yesterday = self.log_datetime.date() - timedelta(days=1)
                try:
                    previous_attendance = Attendance.objects.get(employeeid=self.employee, logdate=yesterday)
                    if not previous_attendance.last_logtime: 
                        # This OUT punch is likely associated with yesterday's IN
                        previous_attendance.last_logtime = self.log_datetime.time()
                        previous_attendance.save(update_fields=['last_logtime'])
                        logger.info(f"Updated previous day's attendance for employee {self.employeeid} with OUT punch.")
                    else:
                        # This is a regular OUT punch for the current day
                        attendance.last_logtime = self.log_datetime.time() 
                except Attendance.DoesNotExist:
                    # No attendance record for the previous day, treat as a regular OUT punch
                    attendance.last_logtime = self.log_datetime.time()

        

        # Calculate and update attendance metrics
        if self.auto_shift:
            print("Auto shift", self.auto_shift)
            if first_log:
                attendance.late_entry = self.calculate_auto_shift_late_entry(first_log, self.auto_shift)
            if last_log:
                # attendance.last_logtime = last_log.log_datetime.time()
                print("Auto shift Log out", last_log.log_datetime.time())
                attendance.early_exit = self.calculate_auto_shift_early_exit(self.get_last_log(), self.auto_shift)
                print("First logtime", attendance.first_logtime, "Last logtime", attendance.last_logtime)
                attendance.total_time = self.calculate_auto_shift_total_time(attendance.first_logtime, attendance.last_logtime, attendance.logdate)
                attendance.overtime = self.calculate_auto_shift_overtime(attendance.first_logtime, attendance.last_logtime, attendance.logdate, self.auto_shift)
            
        elif self.shift:
            print("Shift Fixed", self.shift)
            attendance.late_entry = self.calculate_late_entry(first_log, self.shift)
            attendance.early_exit = self.calculate_early_exit(self.get_last_log(), self.shift)
            attendance.total_time = self.calculate_total_time(first_log, self.get_last_log())
            attendance.overtime = self.calculate_overtime(first_log, self.get_last_log(), self.shift)
            # attendance.lunch_in = self.calculate_lunch_in()
            # attendance.lunch_out = self.calculate_lunch_out()
            # attendance.lunch_duration = self.calculate_lunch_duration(attendance.lunch_in, attendance.lunch_out)
            attendance.lunch_in = None
            attendance.lunch_out = None
            attendance.lunch_duration = None


        # Handle cases with very short log time differences
        if attendance.last_logtime and attendance.first_logtime:
            time_difference = datetime.combine(attendance.logdate, attendance.last_logtime) - \
                              datetime.combine(attendance.logdate, attendance.first_logtime)
            if time_difference < timedelta(minutes=5):
                logger.warning(f"Time difference for {self.employeeid} is less than 5 minutes. Adjusting last_logtime.")
                attendance.last_logtime = None

            else:
                attendance.shift_status = 'P'

        # if attendance.last_logtime and attendance.first_logtime:
        #     attendance.shift_status = 'P'

        try:
            attendance.save()
            logger.info(f"Attendance processed for employee: {self.employeeid} at {self.log_datetime}")
            return True 
        except Exception as e:
            logger.error(f"Error saving attendance record for employee {self.employeeid}: {e}")
            return False 
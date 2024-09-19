from datetime import datetime, timedelta, time
from typing import Optional

from django.db import models
from django.utils import timezone

from config.models import Shift, AutoShift
from resource.models import Employee, Logs, Attendance

import logging

logger = logging.getLogger(__name__)

def process_attendance(employeeid: str, log_datetime: datetime, direction: str) -> bool:
    if not employeeid:
        return False
    
    try:
        employee = Employee.objects.get(employee_id=employeeid)
    except Employee.DoesNotExist:
        logger.error(f"Employee with ID: {employeeid} not found.")
        return False

    week_off = [6]

    if employee.shift is None:
        if direction == 'In Device':
            for auto_shift in AutoShift.objects.all():  # Iterate over all AutoShift objects
                log_time = log_datetime.time()
                start_time = auto_shift.start_time
                end_time = auto_shift.end_time
                tolerance_start = auto_shift.tolerance_start_time
                tolerance_end = auto_shift.tolerance_end_time
                grace_period_at_start_time = auto_shift.grace_period_at_start_time

                start_window = (datetime.combine(log_datetime.date(), start_time) - tolerance_start).time()
                end_window = (datetime.combine(log_datetime.date(), start_time) + tolerance_end).time()

                start_time_with_grace = (datetime.combine(log_datetime.date(), start_time) + grace_period_at_start_time).time()

                if start_window <= log_time <= end_window:
                    # Create an Attendance record if not existing
                    if log_datetime.weekday() not in week_off:
                        attendance, created = Attendance.objects.update_or_create(
                            employeeid=employee,
                            logdate=log_datetime.date(),
                            defaults={
                                'first_logtime': log_time,
                                'shift': auto_shift.name,
                                'direction': 'Machine',
                                'shift_status': 'MP'
                            }
                        )

                        if created:
                            if log_time > start_time_with_grace:
                                start_time_aware = timezone.make_aware(datetime.combine(log_datetime.date(), start_time))
                                attendance.late_entry = log_datetime - start_time_aware
                            attendance.save()
                            print(f"Attendance record created for employee {employeeid} on {log_datetime.date()}")
                            return True
                        else:
                            # Update fields if needed
                            if log_time > start_time_with_grace:
                                start_time_aware = timezone.make_aware(datetime.combine(log_datetime.date(), start_time))
                                attendance.late_entry = log_datetime - start_time_aware
                            attendance.first_logtime = log_time
                            attendance.shift = auto_shift.name
                            attendance.direction = 'Machine'
                            attendance.save()
                    else:
                        attendance, created = Attendance.objects.update_or_create(
                            employeeid=employee,
                            logdate=log_datetime.date(),
                            defaults={
                                'first_logtime': log_time,
                                'shift': auto_shift.name,
                                'direction': 'Machine',
                                'shift_status': 'WW'
                            }
                        )
                    

                    return True
                    
                    break  # Exit loop after creating attendance record

            # If no matching AutoShift was found, log a warning
            if auto_shift is None:
                logger.warning(f"No matching AutoShift found for employee {employeeid} with first log time {log_datetime}")
                pass
                

        elif direction == 'Out Device':   
            try:
                # Try to get the attendance record for the current date
                attendance = Attendance.objects.get(
                    employeeid=employee,
                    logdate=log_datetime.date(),
                    first_logtime__isnull=False
                )
            except Attendance.DoesNotExist:
                # If not found, check for the previous day (useful for night shifts)
                previous_day = log_datetime.date() - timedelta(days=1)
                try:
                    attendance = Attendance.objects.get(
                        employeeid=employee,
                        logdate=previous_day,
                        first_logtime__isnull=False
                    )
                    logger.info(f"Attendance record found for the previous day {previous_day} for employee {employee.employee_id}")
                except Attendance.DoesNotExist:
                    logger.warning(f"No IN log found for employee {employee.employee_id} on {log_datetime.date()}")
                    return False
            
            if attendance:
                shift = attendance.shift
                night_shift = AutoShift.objects.get(name=shift).night_shift if shift else False
                first_logtime = attendance.first_logtime

                if not night_shift:
                    log_time = log_datetime.time()
                    logdate = attendance.logdate
                    start_time = AutoShift.objects.get(name=shift).start_time
                    end_time = AutoShift.objects.get(name=shift).end_time
                    tolerance_start = AutoShift.objects.get(name=shift).tolerance_start_time
                    tolerance_end = AutoShift.objects.get(name=shift).tolerance_end_time
                    overtime_threshold_before_start = AutoShift.objects.get(name=shift).overtime_threshold_before_start
                    overtime_threshold_after_end = AutoShift.objects.get(name=shift).overtime_threshold_after_end
                    grace_period_at_end_time = AutoShift.objects.get(name=shift).grace_period_at_end_time
                    half_day_threshold = AutoShift.objects.get(name=shift).half_day_threshold

                    start_time_aware = timezone.make_aware(datetime.combine(logdate, start_time))
                    end_time_aware = timezone.make_aware(datetime.combine(logdate, end_time)) 

                    attendance.last_logtime = log_time
                    attendance.direction = 'Machine'
                    # attendance.shift_status = 'P'

                    end_time_with_grace = end_time_aware - grace_period_at_end_time
                    

                    attendance.total_time = log_datetime - timezone.make_aware(datetime.combine(logdate, first_logtime))

                    if attendance.logdate.weekday() not in week_off:

                        if attendance.total_time > half_day_threshold:
                            attendance.shift_status = 'P'
                        else: 
                            attendance.shift_status = 'HD'

                        if log_datetime < end_time_with_grace:
                            attendance.early_exit = end_time_aware - log_datetime

                        if timezone.make_aware(datetime.combine(attendance.logdate, attendance.first_logtime)) < (start_time_aware - overtime_threshold_before_start) or log_datetime > (end_time_aware + overtime_threshold_after_end):
                            start_overtime = timezone.make_aware(datetime.combine(attendance.logdate, start_time)) - timezone.make_aware(datetime.combine(attendance.logdate, attendance.first_logtime)) if timezone.make_aware(datetime.combine(attendance.logdate, attendance.first_logtime)) < (timezone.make_aware(datetime.combine(attendance.logdate, start_time)) - overtime_threshold_before_start) else timedelta(0)
                            end_overtime = log_datetime - timezone.make_aware(datetime.combine(attendance.logdate, end_time)) if log_datetime > (timezone.make_aware(datetime.combine(attendance.logdate, end_time)) + overtime_threshold_after_end) else timedelta(0)
                            total_overtime = start_overtime + end_overtime
                            if total_overtime > timedelta(0):
                                attendance.overtime = total_overtime

                    else:
                        attendance.shift_status = 'WW'
                        attendance.overtime = attendance.total_time

                    
                        # attendance.overtime = start_overtime + end_overtime
                
                else:
                    log_time = log_datetime.time()
                    logdate = log_datetime.date() - timedelta(days=1)
                    start_time = AutoShift.objects.get(name=shift).start_time
                    end_time = AutoShift.objects.get(name=shift).end_time
                    tolerance_start = AutoShift.objects.get(name=shift).tolerance_start_time
                    tolerance_end = AutoShift.objects.get(name=shift).tolerance_end_time
                    overtime_threshold_before_start = AutoShift.objects.get(name=shift).overtime_threshold_before_start
                    overtime_threshold_after_end = AutoShift.objects.get(name=shift).overtime_threshold_after_end
                    grace_period_at_end_time = AutoShift.objects.get(name=shift).grace_period_at_end_time
                    half_day_threshold = AutoShift.objects.get(name=shift).half_day_threshold

                    start_time_aware = timezone.make_aware(datetime.combine(log_datetime.date(), start_time)) 
                    end_time_aware = timezone.make_aware(datetime.combine(log_datetime.date(), end_time)) 

                    attendance.last_logtime = log_time
                    attendance.direction = 'Machine'
                    # attendance.shift_status = 'P'

                    end_time_with_grace = end_time_aware - grace_period_at_end_time
                    

                    attendance.total_time = timezone.make_aware(datetime.combine(attendance.logdate, attendance.last_logtime) + timedelta(days=1)) - timezone.make_aware(datetime.combine(attendance.logdate, attendance.first_logtime))

                    if attendance.logdate.weekday() not in week_off:

                        if attendance.total_time > half_day_threshold:
                            attendance.shift_status = 'P'
                        else:
                            attendance.shift_status = 'HD'

                        if log_datetime < end_time_with_grace:
                            attendance.early_exit = end_time_aware - log_datetime
                        
                        if timezone.make_aware(datetime.combine(attendance.logdate, attendance.first_logtime)) < (start_time_aware - overtime_threshold_before_start) or timezone.make_aware(datetime.combine(attendance.logdate, attendance.last_logtime)) > (end_time_aware + overtime_threshold_after_end):
                            start_overtime = timezone.make_aware(datetime.combine(attendance.logdate, start_time)) - timezone.make_aware(datetime.combine(attendance.logdate, attendance.first_logtime)) if timezone.make_aware(datetime.combine(attendance.logdate, attendance.first_logtime)) < (timezone.make_aware(datetime.combine(attendance.logdate, start_time)) - overtime_threshold_before_start) else timedelta(0)
                            end_overtime = timezone.make_aware(datetime.combine(attendance.logdate, attendance.last_logtime)) - timezone.make_aware(datetime.combine(attendance.logdate, end_time)) if timezone.make_aware(datetime.combine(attendance.logdate, attendance.last_logtime)) > (timezone.make_aware(datetime.combine(attendance.logdate, end_time)) + overtime_threshold_after_end) else timedelta(0)
                            total_overtime = start_overtime + end_overtime
                            if total_overtime > timedelta(0):
                                attendance.overtime = total_overtime

                    else:
                        attendance.shift_status = 'WW'
                        attendance.overtime = attendance.total_time

                    
                        # attendance.overtime = start_overtime + end_overtime

                try:
                    attendance.save()
                    # logger.info(f"Attendance processed for employee: {employeeid} at {log_datetime}")
                    return True 
                except Exception as e:
                    logger.error(f"Error saving attendance record for employee {employeeid}: {e}")
                    return False      


        
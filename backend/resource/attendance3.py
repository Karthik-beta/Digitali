from datetime import datetime, timedelta, date, time
from django.db.models import Q
from django.db import transaction
from typing import List, Dict, Tuple
import logging

from resource.models import Logs, Employee, ManDaysAttendance, LastLogIdMandays

logger = logging.getLogger(__name__)

class ManDaysAttendanceProcessor:
    def __init__(self):
        self.last_processed_id = self._get_last_processed_id()
        self.valid_employee_ids = self._get_valid_employee_ids()
        
    def _get_last_processed_id(self) -> int:
        last_log = LastLogIdMandays.objects.first()
        return last_log.last_log_id if last_log else 0
    
    def _get_valid_employee_ids(self) -> set:
        return set(Employee.objects.values_list('id', flat=True))
    
    def _get_new_logs(self) -> List:
        return (Logs.objects
                .filter(id__gt=self.last_processed_id)
                .order_by('log_datetime', 'id')
                .values('id', 'employeeid', 'log_datetime', 'direction'))

    def _process_day_logs(self, logs: List) -> List[Dict]:
        """Process logs for a single day in chronological order."""
        processed_logs = []
        slot_index = 1
        
        # Sort logs chronologically
        sorted_logs = sorted(logs, key=lambda x: x['log_datetime'])
        
        for log in sorted_logs:
            log_time = log['log_datetime'].time()
            
            if slot_index > 10:  # Limit to 10 pairs
                break
                
            if log['direction'] == 'In Device':
                processed_logs.append({
                    'slot': slot_index,
                    'duty_in': log_time,
                    'duty_out': None,
                    'total_time': None
                })
                slot_index += 1
            else:  # Out Device
                # Find the last incomplete entry
                for entry in reversed(processed_logs):
                    if entry['duty_out'] is None:
                        entry['duty_out'] = log_time
                        if entry['duty_in']:
                            # Calculate duration only if we have both in and out
                            in_dt = datetime.combine(date.today(), entry['duty_in'])
                            out_dt = datetime.combine(date.today(), log_time)
                            if out_dt < in_dt:  # Handle midnight crossing
                                out_dt += timedelta(days=1)
                            if out_dt > in_dt:
                                entry['total_time'] = out_dt - in_dt
                        break
                else:
                    # If no incomplete entry found, create new entry with only out time
                    processed_logs.append({
                        'slot': slot_index,
                        'duty_in': None,
                        'duty_out': log_time,
                        'total_time': None
                    })
                    slot_index += 1
                    
        return processed_logs

    def _group_logs_by_employee_and_date(self, logs: List) -> Dict:
        grouped_logs = {}
        for log in logs:
            emp_id = log['employeeid']
            
            if not self._is_valid_employee(emp_id):
                logger.warning(f"Skipping logs for invalid employee ID: {emp_id}")
                continue
                
            log_date = log['log_datetime'].date()
            
            if emp_id not in grouped_logs:
                grouped_logs[emp_id] = {}
            if log_date not in grouped_logs[emp_id]:
                grouped_logs[emp_id][log_date] = []
                
            grouped_logs[emp_id][log_date].append(log)
        
        return grouped_logs

    def _create_attendance_record(self, emp_id: str, log_date: date, 
                                processed_logs: List[Dict]) -> None:
        try:
            if not self._is_valid_employee(emp_id):
                logger.warning(f"Skipping attendance record for invalid employee ID: {emp_id}")
                return
                
            attendance_data = {
                'employeeid_id': emp_id,
                'logdate': log_date,
                'shift': '',
                'shift_status': ''
            }
            
            total_hours = timedelta()
            
            # Map processed logs to attendance record fields
            for log in processed_logs:
                slot = log['slot']
                if slot > 10:
                    break
                    
                if log['duty_in']:
                    attendance_data[f'duty_in_{slot}'] = log['duty_in']
                if log['duty_out']:
                    attendance_data[f'duty_out_{slot}'] = log['duty_out']
                if log['total_time']:
                    attendance_data[f'total_time_{slot}'] = log['total_time']
                    total_hours += log['total_time']
            
            attendance_data['total_hours_worked'] = total_hours
            
            # Create or update record
            ManDaysAttendance.objects.update_or_create(
                employeeid_id=emp_id,
                logdate=log_date,
                defaults=attendance_data
            )
            
        except Exception as e:
            logger.error(f"Error creating attendance record for employee {emp_id}: {str(e)}")

    def _is_valid_employee(self, emp_id: str) -> bool:
        try:
            emp_id = int(emp_id)
            return emp_id in self.valid_employee_ids
        except (ValueError, TypeError):
            return False

    @transaction.atomic
    def process_logs(self) -> None:
        try:
            new_logs = self._get_new_logs()
            if not new_logs:
                logger.info("No new logs to process")
                return
                
            grouped_logs = self._group_logs_by_employee_and_date(new_logs)
            
            for emp_id, date_logs in grouped_logs.items():
                for log_date, logs in date_logs.items():
                    processed_logs = self._process_day_logs(logs)
                    if processed_logs:
                        self._create_attendance_record(emp_id, log_date, processed_logs)
            
            if new_logs:
                self._update_last_processed_id(new_logs.last()['id'])
                
        except Exception as e:
            logger.error(f"Error processing logs: {str(e)}")
            raise

    def _update_last_processed_id(self, log_id: int) -> None:
        LastLogIdMandays.objects.update_or_create(
            defaults={'last_log_id': log_id}
        )


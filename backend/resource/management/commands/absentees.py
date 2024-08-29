from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import F, Q
from django.utils import timezone
from resource.models import Attendance, Employee

class Command(BaseCommand):
    help = "Creates new fields in Attendance model and marks absent employees for a given number of days starting from today"

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Number of days to process starting from today'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        num_days = options['days']
        today = timezone.now().date()
        
        for i in range(num_days):
            date = today - timezone.timedelta(days=i)
            employees = Employee.objects.all()
            for employee in employees:
                if not Attendance.objects.filter(employeeid=employee, logdate=date).exists():
                    Attendance.objects.create(
                        employeeid=employee,
                        logdate=date,
                        shift_status='A'
                    )
                    # self.stdout.write(self.style.SUCCESS(f"Marked {employee.employee_name} as absent for {date}"))
                else:
                    # self.stdout.write(self.style.SUCCESS(f"{employee.employee_name} already has an attendance entry for {date}"))
                    pass
        self.stdout.write(self.style.SUCCESS(f"Successfully marked absent employees for {num_days} days starting from {today}"))

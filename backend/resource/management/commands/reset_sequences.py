from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Reset database sequences'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT setval('employee_id_seq', 
                            (SELECT MAX(id) FROM employee), 
                            true);
            """)
            self.stdout.write(
                self.style.SUCCESS('Successfully reset employee sequence')
            )
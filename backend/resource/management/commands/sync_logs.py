from django.core.management.base import BaseCommand
import pyodbc
import psycopg2
import os
from django.conf import settings
from datetime import datetime

class Command(BaseCommand):
    help = 'Syncs logs from MSSQL to PostgreSQL database'

    def handle(self, *args, **kwargs):
        try:
            # Build MSSQL connection string from environment variables
            mssql_conn_str = (
                f"DRIVER={{{os.getenv('MSSQL_DRIVER', 'ODBC Driver 17 for SQL Server')}}};"
                f"SERVER={os.getenv('DATABASE_HOST')},{os.getenv('MSSQL_DATABASE_PORT', '1433')};;"
                f"DATABASE={os.getenv('MSSQL_DATABASE_NAME')};"
                f"UID={os.getenv('MSSQL_DATABASE_USER')};"
                f"PWD=={os.getenv('MSSQL_DATABASE_PASSWORD')};"
                f"TrustServerCertificate=yes;"
                f"Encrypt=no"
            )

            # Build PostgreSQL connection string from environment variables
            pg_conn_str = (
                f"dbname={os.getenv('DATABASE_NAME')} "
                f"user={os.getenv('DATABASE_USER')} "
                f"password={os.getenv('DATABASE_PASSWORD')} "
                f"host={os.getenv('DATABASE_HOST')} "
                f"port={os.getenv('DATABASE_PORT')}"
            )

            latest_id = self.fetch_latest_id_from_postgres(pg_conn_str)
            new_records = self.fetch_new_records_from_mssql(mssql_conn_str, latest_id)
            
            if new_records:
                self.insert_records_into_postgres(pg_conn_str, new_records)
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully inserted {len(new_records)} new records into PostgreSQL.')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('No new records to insert.')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error occurred: {str(e)}')
            )

    def fetch_latest_id_from_postgres(self, pg_conn_str):
        with psycopg2.connect(pg_conn_str) as pg_conn:
            with pg_conn.cursor() as cursor:
                cursor.execute('SELECT MAX(id) FROM public.logs')
                result = cursor.fetchone()
                return result[0] if result[0] is not None else 0

    def fetch_new_records_from_mssql(self, mssql_conn_str, latest_id):
        with pyodbc.connect(mssql_conn_str) as mssql_conn:
            query = '''
                SELECT [id], [employeeid], [direction], [shortname], [serialno], [log_datetime]
                FROM [biotime].[dbo].[logs]
                WHERE [id] > ?
            '''
            with mssql_conn.cursor() as cursor:
                cursor.execute(query, latest_id)
                return cursor.fetchall()

    def insert_records_into_postgres(self, pg_conn_str, records):
        with psycopg2.connect(pg_conn_str) as pg_conn:
            with pg_conn.cursor() as cursor:
                insert_query = '''
                INSERT INTO public.logs (id, employeeid, direction, shortname, serialno, log_datetime)
                VALUES (%s, %s, %s, %s, %s, %s)
                '''
                cursor.executemany(insert_query, records)
                pg_conn.commit()
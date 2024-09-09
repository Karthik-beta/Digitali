import pyodbc
import psycopg2
import schedule
import time
import os
import tempfile

# Database connection settings
mssql_conn_str = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER=AWYWE802669\\SQLEXPRESS;DATABASE=biotime;UID=Digitali;PWD=Digitali'
pg_conn_str = 'dbname=casa user=postgres password=password123 host=10.38.21.181 port=5432'

def clear_cache(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                os.rmdir(file_path)
        except Exception as e:
            print(f"Error clearing cache file {file_path}: {e}")
            # Optionally, wait a moment before retrying
            time.sleep(1)

clear_cache("C:\\Users\\vvrajgo\\AppData\\Local\\Temp")

def fetch_latest_id_from_postgres():
    with psycopg2.connect(pg_conn_str) as pg_conn:
        with pg_conn.cursor() as cursor:
            cursor.execute('SELECT MAX(id) FROM public.logs')
            result = cursor.fetchone()
            return result[0] if result[0] is not None else 0

def fetch_new_records_from_mssql(latest_id):
    with pyodbc.connect(mssql_conn_str) as mssql_conn:
        query = 'SELECT [id], [employeeid], [direction], [shortname], [serialno], [log_datetime] FROM [biotime].[dbo].[logs] WHERE [id] > ?'
        with mssql_conn.cursor() as cursor:
            cursor.execute(query, latest_id)
            return cursor.fetchall()

def insert_records_into_postgres(records):
    with psycopg2.connect(pg_conn_str) as pg_conn:
        with pg_conn.cursor() as cursor:
            insert_query = '''
            INSERT INTO public.logs (id, employeeid, direction, shortname, serialno, log_datetime)
            VALUES (%s, %s, %s, %s, %s, %s)
            '''
            cursor.executemany(insert_query, records)
            pg_conn.commit()

def job():
    clear_cache()
    
    latest_id = fetch_latest_id_from_postgres()
    new_records = fetch_new_records_from_mssql(latest_id)
    
    if new_records:
        insert_records_into_postgres(new_records)
        print(f'Inserted {len(new_records)} new records into PostgreSQL.')
    else:
        print('No new records to insert.')

# Schedule the job to run every 10 seconds
schedule.every(10).seconds.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)

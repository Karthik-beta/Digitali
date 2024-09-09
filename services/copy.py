import pyodbc
import requests
import time
import os
import schedule

# MSSQL connection details
MSSQL_SERVER = 'AWYWE802669\SQLEXPRESS'
MSSQL_DATABASE = 'biotime'
MSSQL_USER = 'Digitali'
MSSQL_PASSWORD = 'Digitali'

# API URL
API_URL = 'http://10.38.21.181:8000/'

# API endpoints
LAST_LOG_ID_URL = API_URL + 'last_log_id'
LOGS_URL = API_URL + 'logs'

# Function to get the last log ID from the API
def get_last_log_id():
    response = requests.get(LAST_LOG_ID_URL)
    if response.status_code == 200:
        data = response.json()
        return data.get('last_log_id', 0) or 0
    else:
        raise Exception("Failed to get last log ID from API")

# Function to query MSSQL database
def query_mssql(last_log_id):
    connection_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={MSSQL_SERVER};DATABASE={MSSQL_DATABASE};UID={MSSQL_USER};PWD={MSSQL_PASSWORD}'
    conn = pyodbc.connect(connection_str)
    cursor = conn.cursor()
    
    query = """
    SELECT [id], [employeeid], [direction], [shortname], [serialno], [log_datetime]
    FROM [dbo].[logs]
    WHERE [id] > ?
    """
    cursor.execute(query, (last_log_id,))
    rows = cursor.fetchall()
    conn.close()
    
    return rows

# Function to post a record to the API
def post_record(record):
    payload = {
        "employeeid": record.employeeid,
        "log_datetime": record.log_datetime.isoformat() if record.log_datetime else None,
        "direction": record.direction,
        "shortname": record.shortname,
        "serialno": record.serialno
    }
    response = requests.post(LOGS_URL, json=payload)
    if response.status_code != 201:
        print(f"Failed to post record: {response.text}")

# Function to perform the data transfer
def perform_data_transfer():
    try:
        # Step 1: Get the last log ID from the API
        last_log_id = get_last_log_id()
        
        # Step 2: Query MSSQL for records with ID greater than last_log_id
        records = query_mssql(last_log_id)
        
        # Step 3: Post each record to the API
        for record in records:
            post_record(record)
        
        # Clear cache
        os.system('ipconfig /flushdns')
    
    except Exception as e:
        print(f"An error occurred: {e}")

# Schedule the data transfer to run every 10 seconds
schedule.every(10).seconds.do(perform_data_transfer)

# Main loop to keep the script running
while True:
    schedule.run_pending()
    time.sleep(1)

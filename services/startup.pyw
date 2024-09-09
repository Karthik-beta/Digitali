import subprocess
import os

# Function to run a command in the background
def run_in_background(command, cwd=None):
    # Start process without a visible console window on Windows
    subprocess.Popen(command, cwd=cwd, shell=True, creationflags=subprocess.CREATE_NO_WINDOW)

# Paths to backend and frontend directories
backend_dir = r"C:\Getin\skf_mys\backend"
frontend_dir = r"C:\Getin\skf_mys\frontend\sakai-ng"

# Commands for backend deployment
backend_commands = [
    ["python", "manage.py", "runserver", "0.0.0.0:8000"],
    ["celery", "-A", "backend", "worker"],
    ["celery", "-A", "backend", "beat"]
]

# Command for frontend deployment
frontend_command = ["ng", "serve", "--host", "0.0.0.0", "--disable-host-check"]

# Run backend commands
for command in backend_commands:
    run_in_background(command, cwd=backend_dir)

# Run frontend command
run_in_background(frontend_command, cwd=frontend_dir)

print("Deployment started in the background.")

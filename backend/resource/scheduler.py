from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django_apscheduler.jobstores import DjangoJobStore, register_events, register_job
from django.core.management import call_command
from resource.tasks import scan_for_data
from apscheduler.jobstores.base import JobLookupError

def run_my_command():
    commands = ['absentees', 'task', 'mandays']
    
    for command in commands:
        try:
            call_command(command)
            print(f"Successfully executed command: {command}")
        except Exception as e:
            print(f"Error executing commands: {e}")

def start():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # Schedule the job with max_instances and misfire_grace_time
    try:
        scheduler.add_job(
            run_my_command,
            trigger=IntervalTrigger(minutes=1),
            id="my_job",
            replace_existing=True,
            max_instances=1,  # Prevent overlap
            misfire_grace_time=30  # Allow a grace period of 30 seconds
        )
    except JobLookupError:
        print("Job 'my_job' not found. Adding it again.")
        scheduler.add_job(
            run_my_command,
            trigger=IntervalTrigger(minutes=1),
            id="my_job",
            max_instances=1,
            misfire_grace_time=30
        )

    # Register the job and events
    register_events(scheduler)
    scheduler.start()
    print("Scheduler started.")


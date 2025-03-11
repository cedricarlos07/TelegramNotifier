import logging
from datetime import datetime, timedelta
from app import scheduler, db, app
from models import Course, ScheduledMessage, Log
from telegram_bot import init_telegram_bot
from excel_processor import excel_processor

logger = logging.getLogger(__name__)

def log_job_execution(scenario, success, message):
    """
    Log job execution to database.
    
    Args:
        scenario (str): The scenario name
        success (bool): Whether the job was successful
        message (str): The log message
    """
    level = "INFO" if success else "ERROR"
    log_entry = Log(level=level, scenario=scenario, message=message)
    db.session.add(log_entry)
    db.session.commit()
    
    if success:
        logger.info(message)
    else:
        logger.error(message)

def update_courses_job():
    """
    Job to update course schedules from Excel.
    Run weekly on Sunday at midnight.
    """
    logger.info("Running scheduled job: update_courses_job")
    
    try:
        # Update course schedules
        results = excel_processor.update_course_schedules()
        
        # Log the results
        message = (f"Course update job completed: {results['success']} successes, "
                  f"{results['errors']} errors out of {results['processed']} processed")
        log_job_execution("update_courses", True, message)
        
    except Exception as e:
        error_msg = f"Error in update_courses_job: {str(e)}"
        log_job_execution("update_courses", False, error_msg)

def create_zoom_links_job():
    """
    Job to create Zoom links for courses.
    Run weekly on Sunday after update_courses_job.
    """
    logger.info("Running scheduled job: create_zoom_links_job")
    
    try:
        # Create Zoom links
        results = excel_processor.create_zoom_links()
        
        # Log the results
        message = (f"Zoom link creation job completed: {results['created']} created, "
                  f"{results['errors']} errors out of {results['processed']} processed")
        log_job_execution("create_zoom", True, message)
        
    except Exception as e:
        error_msg = f"Error in create_zoom_links_job: {str(e)}"
        log_job_execution("create_zoom", False, error_msg)

def generate_messages_job():
    """
    Job to generate Telegram messages for courses.
    Run weekly on Sunday after create_zoom_links_job.
    """
    logger.info("Running scheduled job: generate_messages_job")
    
    try:
        # Get all courses for the next week
        today = datetime.now().date()
        next_week = today + timedelta(days=7)
        
        courses = Course.query.filter(
            Course.schedule_date >= today,
            Course.schedule_date < next_week
        ).all()
        
        message_count = 0
        error_count = 0
        
        # Clear existing scheduled messages for this period
        ScheduledMessage.query.filter(
            ScheduledMessage.scheduled_date >= today,
            ScheduledMessage.scheduled_date < next_week,
            ScheduledMessage.is_sent == False
        ).delete()
        
        # Generate messages for each course
        for course in courses:
            try:
                if not course.schedule_date or not course.telegram_group_id:
                    logger.warning(f"Skipping message generation for course {course.id}: Missing date or group ID")
                    continue
                
                # Generate message text
                bot = init_telegram_bot()
                message_text = bot.format_course_message(course)
                if not message_text:
                    continue
                
                # Create scheduled message
                scheduled_message = ScheduledMessage(
                    course_id=course.id,
                    message_text=message_text,
                    scheduled_date=course.schedule_date,
                    scheduled_time=datetime.strptime("08:00", "%H:%M").time(),  # 8 AM
                    telegram_group_id=course.telegram_group_id,
                    is_sent=False
                )
                
                db.session.add(scheduled_message)
                message_count += 1
                
            except Exception as e:
                logger.error(f"Error generating message for course {course.id}: {str(e)}")
                error_count += 1
        
        db.session.commit()
        
        # Log the results
        message = f"Message generation job completed: {message_count} messages created, {error_count} errors"
        log_job_execution("generate_messages", True, message)
        
    except Exception as e:
        error_msg = f"Error in generate_messages_job: {str(e)}"
        log_job_execution("generate_messages", False, error_msg)

def send_daily_messages_job():
    """
    Job to send daily messages to Telegram groups.
    Run daily at 8:00 AM.
    """
    logger.info("Running scheduled job: send_daily_messages_job")
    
    try:
        today = datetime.now().date()
        
        # Get all scheduled messages for today
        scheduled_messages = ScheduledMessage.query.filter(
            ScheduledMessage.scheduled_date == today,
            ScheduledMessage.is_sent == False
        ).all()
        
        message_count = len(scheduled_messages)
        success_count = 0
        error_count = 0
        
        # Send each message
        for message in scheduled_messages:
            try:
                # Send the message via Telegram
                bot = init_telegram_bot()
                if bot.send_message(message.telegram_group_id, message.message_text):
                    # Mark as sent
                    message.is_sent = True
                    message.sent_at = datetime.now()
                    success_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                logger.error(f"Error sending message {message.id}: {str(e)}")
                error_count += 1
        
        db.session.commit()
        
        # Log the results
        message = f"Daily message sending job completed: {success_count} sent, {error_count} errors out of {message_count}"
        log_job_execution("send_daily_messages", True, message)
        
    except Exception as e:
        error_msg = f"Error in send_daily_messages_job: {str(e)}"
        log_job_execution("send_daily_messages", False, error_msg)

def run_job(job_name):
    """
    Run a specific job by name.
    
    Args:
        job_name (str): Name of the job to run
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if job_name == "update_courses":
            update_courses_job()
        elif job_name == "create_zoom_links":
            create_zoom_links_job()
        elif job_name == "generate_messages":
            generate_messages_job()
        elif job_name == "send_daily_messages":
            send_daily_messages_job()
        else:
            return False
        return True
    except Exception as e:
        logger.error(f"Error running job {job_name}: {str(e)}")
        return False

def initialize_scheduler(app):
    """
    Initialize the scheduler with all jobs.
    
    Args:
        app (Flask): Flask application
    """
    # Update courses every Sunday at midnight
    scheduler.add_job(
        id='update_courses',
        func=update_courses_job,
        trigger='cron',
        day_of_week='sun',
        hour=0,
        minute=0
    )
    
    # Create Zoom links every Sunday at 00:05
    scheduler.add_job(
        id='create_zoom_links',
        func=create_zoom_links_job,
        trigger='cron',
        day_of_week='sun',
        hour=0,
        minute=5
    )
    
    # Generate messages every Sunday at 00:10
    scheduler.add_job(
        id='generate_messages',
        func=generate_messages_job,
        trigger='cron',
        day_of_week='sun',
        hour=0,
        minute=10
    )
    
    # Send daily messages every day at 8:00 AM
    scheduler.add_job(
        id='send_daily_messages',
        func=send_daily_messages_job,
        trigger='cron',
        hour=8,
        minute=0
    )
    
    logger.info("Scheduler initialized with all jobs")

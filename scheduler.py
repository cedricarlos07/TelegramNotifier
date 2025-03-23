import logging
from datetime import datetime, timedelta
from extensions import scheduler, db
from flask import current_app
from models import Course, ScheduledMessage, Log
from telegram_bot import init_telegram_bot
from excel_processor import excel_processor

logger = logging.getLogger(__name__)

def log_job_execution(db, scenario, success, message):
    """
    Log job execution to database.
    
    Args:
        db: Database instance
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
        log_job_execution(db, "update_courses", True, message)
        
    except Exception as e:
        error_msg = f"Error in update_courses_job: {str(e)}"
        log_job_execution(db, "update_courses", False, error_msg)

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
        log_job_execution(db, "create_zoom", True, message)
        
    except Exception as e:
        error_msg = f"Error in create_zoom_links_job: {str(e)}"
        log_job_execution(db, "create_zoom", False, error_msg)

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
        log_job_execution(db, "generate_messages", True, message)
        
    except Exception as e:
        error_msg = f"Error in generate_messages_job: {str(e)}"
        log_job_execution(db, "generate_messages", False, error_msg)

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
        log_job_execution(db, "send_daily_messages", True, message)
        
    except Exception as e:
        error_msg = f"Error in send_daily_messages_job: {str(e)}"
        log_job_execution(db, "send_daily_messages", False, error_msg)

def send_daily_notifications():
    """Send notifications for courses scheduled for today."""
    with current_app.app_context():
        try:
            today = datetime.now().date()
            courses = Course.query.filter(
                Course.schedule_date == today,
                Course.telegram_group_id.isnot(None)
            ).all()
            
            if courses:
                bot = init_telegram_bot()
                results = bot.send_daily_course_notifications(courses)
                logger.info(f"Daily notifications sent: {results['success']} successful, {results['failure']} failed")
            else:
                logger.info("No courses scheduled for today")
                
        except Exception as e:
            logger.error(f"Error sending daily notifications: {str(e)}")

def send_daily_rankings():
    """Send daily rankings to all active Telegram groups."""
    with current_app.app_context():
        try:
            today = datetime.now().date()
            courses = Course.query.filter(
                Course.schedule_date == today,
                Course.telegram_group_id.isnot(None)
            ).all()
            
            if courses:
                bot = init_telegram_bot()
                results = bot.send_daily_rankings(courses)
                logger.info(f"Daily rankings sent: {results['success']} successful, {results['failure']} failed")
            else:
                logger.info("No courses scheduled for today")
                
        except Exception as e:
            logger.error(f"Error sending daily rankings: {str(e)}")

def run_custom_python_code(scenario_name, python_code):
    """
    Execute custom Python code for a scenario.
    
    Args:
        scenario_name (str): Name of the scenario
        python_code (str): Custom Python code to execute
        
    Returns:
        tuple: (success, message)
    """
    try:
        # Create a local namespace to execute the code
        local_namespace = {
            'db': db,
            'app': current_app,
            'Course': Course,
            'ScheduledMessage': ScheduledMessage,
            'Log': Log,
            'logger': logger,
            'datetime': datetime,
            'timedelta': timedelta,
            'excel_processor': excel_processor,
            'init_telegram_bot': init_telegram_bot
        }
        
        # Execute the custom code
        exec(python_code, globals(), local_namespace)
        
        # Check if the code defined a run_scenario function
        if 'run_scenario' in local_namespace and callable(local_namespace['run_scenario']):
            # Call the run_scenario function from the custom code
            success, message = local_namespace['run_scenario']()
            return success, message
        else:
            return False, "Custom code must define a run_scenario() function that returns (success, message)"
    except Exception as e:
        error_msg = f"Error executing custom Python code: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def run_job(job_name):
    """
    Run a specific job by name.
    
    Args:
        job_name (str): Name of the job to run
        
    Returns:
        bool: True if successful, False otherwise
    """
    from models import Scenario
    
    try:
        # Check if this is a custom scenario with Python code
        scenario = Scenario.query.filter_by(name=job_name).first()
        
        if scenario and scenario.is_custom_code and scenario.python_code:
            # Run custom Python code
            success, message = run_custom_python_code(job_name, scenario.python_code)
            
            # Log the results
            log_level = "INFO" if success else "ERROR"
            log_entry = Log(
                level=log_level,
                scenario=job_name,
                message=message
            )
            db.session.add(log_entry)
            db.session.commit()
            
            return success
        
        # Otherwise, run the built-in function
        elif job_name == "update_courses":
            update_courses_job()
        elif job_name == "create_zoom_links":
            create_zoom_links_job()
        elif job_name == "generate_messages":
            generate_messages_job()
        elif job_name == "send_daily_messages":
            send_daily_messages_job()
        elif job_name == "send_daily_notifications":
            send_daily_notifications()
        elif job_name == "send_daily_rankings":
            send_daily_rankings()
        else:
            return False
        return True
    except Exception as e:
        logger.error(f"Error running job {job_name}: {str(e)}")
        return False

def initialize_scheduler(app):
    """Initialize the scheduler with the Flask app."""
    scheduler.init_app(app)
    scheduler.start()

def schedule_jobs():
    """Schedule all jobs."""
    # Schedule daily notifications at 8:00 AM
    scheduler.add_job(
        id='daily_notifications',
        func=send_daily_notifications,
        trigger='cron',
        hour=8,
        minute=0
    )
    
    # Schedule daily rankings at 8:30 AM
    scheduler.add_job(
        id='daily_rankings',
        func=send_daily_rankings,
        trigger='cron',
        hour=8,
        minute=30
    )
    
    logger.info("Scheduled jobs initialized")

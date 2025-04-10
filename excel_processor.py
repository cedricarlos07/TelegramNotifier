import logging
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
from config import Config
from app import db
from models import Course, Log
from zoom_api import zoom_api

logger = logging.getLogger(__name__)

class ExcelProcessor:
    """Class to handle Excel file processing for course schedules"""
    
    def __init__(self):
        """Initialize the Excel processor"""
        self.excel_path = Config.EXCEL_FILE_PATH
        self.sheet_name = Config.SHEET_NAME
        
    def _get_day_of_week_index(self, day_str):
        """
        Convert day string to day of week index (0-6, Monday is 0).
        
        Args:
            day_str (str): Day string (e.g., "Monday", "Tuesday")
            
        Returns:
            int: Day of week index (0-6)
        """
        days = {
            "monday": 0, "lundi": 0,
            "tuesday": 1, "mardi": 1,
            "wednesday": 2, "mercredi": 2,
            "thursday": 3, "jeudi": 3,
            "friday": 4, "vendredi": 4,
            "saturday": 5, "samedi": 5,
            "sunday": 6, "dimanche": 6
        }
        return days.get(day_str.lower(), -1)
    
    def _parse_time(self, time_str):
        """
        Parse time string to time object.
        
        Args:
            time_str (str): Time string (e.g., "09:00", "14:30", "20h 30 France")
            
        Returns:
            time: Time object
        """
        try:
            if pd.isna(time_str) or not time_str:
                return None
                
            time_str = str(time_str).strip()
            
            # Format spécifique de votre Excel: "20h 30 France" ou "11h 00 France"
            if "France" in time_str:
                # Supprimer la partie "France"
                time_str = time_str.replace("France", "").strip()
                
                # Convertir le format "20h 30" en "20:30"
                if "h" in time_str:
                    parts = time_str.split("h")
                    hours = parts[0].strip()
                    minutes = parts[1].strip() if len(parts) > 1 and parts[1].strip() else "00"
                    time_str = f"{hours}:{minutes}"
            
            # Try standard formats
            for fmt in ("%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M%p"):
                try:
                    return datetime.strptime(time_str, fmt).time()
                except ValueError:
                    continue
                    
            # If all formats fail, log and return None
            logger.warning(f"Could not parse time: {time_str}")
            return None
        except Exception as e:
            logger.error(f"Error parsing time {time_str}: {str(e)}")
            return None
    
    def load_excel_data(self):
        """
        Load course data from Excel file.
        
        Returns:
            DataFrame or None: Pandas DataFrame with course data or None on error
        """
        try:
            if not os.path.exists(self.excel_path):
                error_msg = f"Excel file not found at {self.excel_path}"
                logger.error(error_msg)
                log_entry = Log(level="ERROR", scenario="excel_load", message=error_msg)
                db.session.add(log_entry)
                db.session.commit()
                return None
                
            # Read the Excel file
            df = pd.read_excel(self.excel_path, sheet_name=self.sheet_name)
            
            # Check if dataframe is empty
            if df.empty:
                logger.warning(f"Excel sheet '{self.sheet_name}' is empty")
                return None
                
            logger.info(f"Successfully loaded {len(df)} rows from Excel")
            return df
            
        except Exception as e:
            error_msg = f"Error loading Excel file: {str(e)}"
            logger.error(error_msg)
            log_entry = Log(level="ERROR", scenario="excel_load", message=error_msg)
            db.session.add(log_entry)
            db.session.commit()
            return None
    
    def _get_next_occurrence(self, day_of_week):
        """
        Get the next occurrence of a day of week.
        
        Args:
            day_of_week (int): Day of week index (0-6, Monday is 0)
            
        Returns:
            date: Next occurrence date
        """
        today = datetime.now().date()
        days_ahead = day_of_week - today.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return today + timedelta(days=days_ahead)
        
    def update_course_schedules(self):
        """
        Update course schedules for the upcoming week.
        
        Returns:
            dict: Results dictionary with success and error counts
        """
        results = {"processed": 0, "success": 0, "errors": 0}
        
        try:
            # Load data from Excel
            df = self.load_excel_data()
            if df is None:
                return results
            
            # Debug column names
            logger.info(f"Excel columns: {df.columns.tolist()}")
                
            # Process the dataframe
            for index, row in df.iterrows():
                results["processed"] += 1
                try:
                    # Extract course details based on the Excel structure we observed
                    course_name = row.get('Salma Choufani - ABG - SS - 2:00pm')  # First column contains course name
                    teacher_name = row.get('Salma Choufani')  # Second column contains teacher name
                    day_str = row.get('DAY')  # Day column
                    start_time_str = row.get('TIME (France)')  # Using the French time column
                    end_time_str = None  # End time not provided, we'll calculate it later
                    telegram_group_id = row.get('TELEGRAM GROUP ID')  # Telegram group ID column
                    
                    # Skip rows with missing essential data
                    if pd.isna(course_name) or pd.isna(day_str) or pd.isna(start_time_str):
                        logger.warning(f"Skipping row {index}: Missing essential data")
                        continue
                    
                    # Convert to appropriate data types
                    day_of_week = self._get_day_of_week_index(day_str)
                    start_time = self._parse_time(start_time_str)
                    
                    # Assume classes are 1 hour if end time is not provided
                    if start_time and not end_time_str:
                        hour = start_time.hour
                        minute = start_time.minute
                        end_hour = hour + 1
                        end_time = time(end_hour % 24, minute)
                    else:
                        end_time = self._parse_time(end_time_str)
                    
                    if day_of_week == -1 or not start_time:
                        logger.warning(f"Skipping row {index}: Invalid day or time format: {day_str}, {start_time_str}")
                        continue
                    
                    # Calculate the next occurrence date
                    next_date = self._get_next_occurrence(day_of_week)
                    
                    # Use a safe string representation for course_name
                    if not isinstance(course_name, str):
                        course_name = str(course_name)
                    
                    # Use a safe string representation for teacher_name
                    if pd.isna(teacher_name) or not isinstance(teacher_name, str):
                        teacher_name = "Unknown Teacher"
                    
                    # Check if course already exists in database
                    existing_course = Course.query.filter_by(
                        course_name=course_name,
                        day_of_week=day_of_week,
                        start_time=start_time
                    ).first()
                    
                    # Make sure telegram_group_id is in the correct format
                    if pd.isna(telegram_group_id) or not telegram_group_id:
                        telegram_group_id = "-1001234567890"  # Default if not specified
                    else:
                        telegram_group_id = str(telegram_group_id).strip()
                    
                    logger.info(f"Processing course: {course_name}, teacher: {teacher_name}, day: {day_str}, " +
                               f"time: {start_time_str}, group: {telegram_group_id}")
                    
                    if existing_course:
                        # Update existing course
                        existing_course.teacher_name = teacher_name
                        existing_course.end_time = end_time
                        existing_course.schedule_date = next_date
                        existing_course.telegram_group_id = telegram_group_id
                        db.session.commit()
                        logger.info(f"Updated course: {course_name} on {next_date}")
                    else:
                        # Create new course
                        new_course = Course(
                            course_name=course_name,
                            teacher_name=teacher_name,
                            day_of_week=day_of_week,
                            start_time=start_time,
                            end_time=end_time,
                            schedule_date=next_date,
                            telegram_group_id=telegram_group_id
                        )
                        db.session.add(new_course)
                        db.session.commit()
                        logger.info(f"Added new course: {course_name} on {next_date}")
                    
                    results["success"] += 1
                    
                except Exception as e:
                    error_msg = f"Error processing row {index}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"] += 1
                    log_entry = Log(level="ERROR", scenario="update_courses", message=error_msg)
                    db.session.add(log_entry)
                    db.session.commit()
            
            # Log the results
            log_message = (f"Course schedule update completed: {results['success']} successes, "
                          f"{results['errors']} errors out of {results['processed']} processed")
            logger.info(log_message)
            log_entry = Log(level="INFO", scenario="update_courses", message=log_message)
            db.session.add(log_entry)
            db.session.commit()
            
            return results
            
        except Exception as e:
            error_msg = f"Error in update_course_schedules: {str(e)}"
            logger.error(error_msg)
            log_entry = Log(level="ERROR", scenario="update_courses", message=error_msg)
            db.session.add(log_entry)
            db.session.commit()
            return results
    
    def create_zoom_links(self):
        """
        Create Zoom links for courses that don't have them.
        
        Returns:
            dict: Results dictionary with success and error counts
        """
        results = {"processed": 0, "created": 0, "errors": 0, "skipped": 0}
        
        try:
            # Get all courses without Zoom links
            courses_without_zoom = Course.query.filter(
                (Course.zoom_link.is_(None)) | 
                (Course.zoom_link == '')
            ).all()
            
            results["processed"] = len(courses_without_zoom)
            
            for course in courses_without_zoom:
                try:
                    # Skip courses with no schedule date or times
                    if not course.schedule_date or not course.start_time or not course.end_time:
                        logger.warning(f"Skipping Zoom creation for course {course.id}: Missing date/time")
                        results["skipped"] += 1
                        continue
                    
                    # Create Zoom meeting
                    meeting_info = zoom_api.create_meeting(course)
                    
                    if meeting_info:
                        # Update course with Zoom details
                        course.zoom_link = meeting_info.get('join_url')
                        course.zoom_meeting_id = str(meeting_info.get('id'))
                        db.session.commit()
                        
                        logger.info(f"Created Zoom link for course {course.id}: {course.zoom_link}")
                        results["created"] += 1
                    else:
                        logger.error(f"Failed to create Zoom link for course {course.id}")
                        results["errors"] += 1
                        
                except Exception as e:
                    error_msg = f"Error creating Zoom link for course {course.id}: {str(e)}"
                    logger.error(error_msg)
                    results["errors"] += 1
                    log_entry = Log(level="ERROR", scenario="create_zoom", message=error_msg)
                    db.session.add(log_entry)
                    db.session.commit()
            
            # Log the results
            log_message = (f"Zoom link creation completed: {results['created']} created, "
                          f"{results['errors']} errors, {results['skipped']} skipped out of {results['processed']} processed")
            logger.info(log_message)
            log_entry = Log(level="INFO", scenario="create_zoom", message=log_message)
            db.session.add(log_entry)
            db.session.commit()
            
            return results
            
        except Exception as e:
            error_msg = f"Error in create_zoom_links: {str(e)}"
            logger.error(error_msg)
            log_entry = Log(level="ERROR", scenario="create_zoom", message=error_msg)
            db.session.add(log_entry)
            db.session.commit()
            return results
    
    def export_to_excel(self):
        """
        Export current course data to Excel.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get all courses
            courses = Course.query.all()
            
            # Convert to dataframe
            data = []
            for course in courses:
                data.append({
                    'Course Name': course.course_name,
                    'Teacher Name': course.teacher_name,
                    'Day': ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"][course.day_of_week],
                    'Start Time': course.start_time.strftime("%H:%M") if course.start_time else "",
                    'End Time': course.end_time.strftime("%H:%M") if course.end_time else "",
                    'Schedule Date': course.schedule_date.strftime("%Y-%m-%d") if course.schedule_date else "",
                    'Telegram Group ID': course.telegram_group_id,
                    'Zoom Link': course.zoom_link,
                    'Zoom Meeting ID': course.zoom_meeting_id
                })
            
            df = pd.DataFrame(data)
            
            # Save to Excel
            df.to_excel(self.excel_path, sheet_name=self.sheet_name, index=False)
            
            logger.info(f"Successfully exported {len(data)} courses to Excel")
            return True
            
        except Exception as e:
            error_msg = f"Error exporting to Excel: {str(e)}"
            logger.error(error_msg)
            log_entry = Log(level="ERROR", scenario="export_excel", message=error_msg)
            db.session.add(log_entry)
            db.session.commit()
            return False

# Create a global instance of the Excel processor
excel_processor = ExcelProcessor()

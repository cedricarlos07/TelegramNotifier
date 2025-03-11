import os
from datetime import time

# Telegram bot configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "7244520668:AAHhLLrMyNUvK1IWW9UJQ38nP7Kwh-N2UBE")

# Zoom API configuration
ZOOM_API_KEY = os.environ.get("ZOOM_API_KEY", "")
ZOOM_API_SECRET = os.environ.get("ZOOM_API_SECRET", "")
ZOOM_USER_ID = os.environ.get("ZOOM_USER_ID", "")

# Excel file configuration
EXCEL_FILE_PATH = os.environ.get("EXCEL_FILE_PATH", "course_schedule.xlsx")
SHEET_NAME = "Fix Schedule"

# Scheduler configuration
SCHEDULE_UPDATE_COURSES = {"day_of_week": "6", "hour": 0, "minute": 0}  # Sunday at midnight
SCHEDULE_CREATE_ZOOM = {"day_of_week": "6", "hour": 0, "minute": 5}  # Sunday at 00:05
SCHEDULE_GENERATE_MESSAGES = {"day_of_week": "6", "hour": 0, "minute": 10}  # Sunday at 00:10
SCHEDULE_SEND_DAILY_MESSAGES = {"hour": 8, "minute": 0}  # Daily at 8:00 AM

# Message template for Telegram
MESSAGE_TEMPLATE = """
📚 **COURS PROGRAMMÉ** 📚

📅 Date: {date}
⏰ Heure: {time}
👨‍🏫 Cours: {course_name}
🔗 Lien Zoom: {zoom_link}

Connectez-vous à l'heure, s'il vous plaît!
"""

import os
from datetime import time
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Telegram bot configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Zoom API configuration (OAuth)
ZOOM_ACCOUNT_ID = os.getenv("ZOOM_ACCOUNT_ID")
ZOOM_CLIENT_ID = os.getenv("ZOOM_CLIENT_ID")
ZOOM_CLIENT_SECRET = os.getenv("ZOOM_CLIENT_SECRET")
ZOOM_USER_ID = os.getenv("ZOOM_USER_ID", "me")  # "me" refers to the authenticated user

# Excel file configuration
EXCEL_FILE_PATH = os.environ.get("EXCEL_FILE_PATH", "attached_assets/Kodjo English - Classes Schedules (1).xlsx")
SHEET_NAME = "Fix Schedule"

# Scheduler configuration
SCHEDULE_UPDATE_COURSES = {"day_of_week": "6", "hour": 0, "minute": 0}  # Sunday at midnight
SCHEDULE_CREATE_ZOOM = {"day_of_week": "6", "hour": 0, "minute": 5}  # Sunday at 00:05
SCHEDULE_GENERATE_MESSAGES = {"day_of_week": "6", "hour": 0, "minute": 10}  # Sunday at 00:10
SCHEDULE_SEND_DAILY_MESSAGES = {"hour": 8, "minute": 0}  # Daily at 8:00 AM

# Message template for Telegram
MESSAGE_TEMPLATE = """
📚 *RAPPEL DE COURS AUJOURD'HUI* 📚

⚠️ Si vous prévoyez d'être en retard ou absent, merci d'informer le groupe à l'avance.

👨‍🏫 *COURS*: {course_name}
👤 *PROFESSEUR*: {teacher_name}

⏰ *HORAIRE*
• 🌍 {time} GMT
• 🇫🇷 {time} Heure de France

🔗 *ACCÈS AU COURS*
• Lien Zoom: {zoom_link}
• ID de réunion: {zoom_meeting_id}
• Code d'accès: 123456

📱 *INSTRUCTIONS DE CONNEXION*
1️⃣ Première utilisation? Téléchargez l'application ZOOM avant le cours
2️⃣ À l'heure du cours, cliquez sur le lien ci-dessus
3️⃣ Si demandé, entrez l'ID de réunion
4️⃣ Activez votre microphone
5️⃣ Renommez-vous avec votre prénom et nom de famille
6️⃣ Gardez votre caméra désactivée (cours audio uniquement)

📅 *DATE*: {date}

🎓 Nous vous attendons en classe!
"""

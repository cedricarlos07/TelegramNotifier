import os
from datetime import time
from dotenv import load_dotenv
import logging

# Charger les variables d'environnement
load_dotenv()

logger = logging.getLogger(__name__)

class Config:
    # Configuration de base
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    FLASK_ENV = os.environ.get('FLASK_ENV', 'production')
    FLASK_APP = os.environ.get('FLASK_APP', 'app.py')
    
    # Configuration de la base de données
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///telegram_notifier.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    
    # Configuration Telegram
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN n'est pas défini")
    
    # Configuration Zoom
    ZOOM_ACCOUNT_ID = os.environ.get('ZOOM_ACCOUNT_ID')
    ZOOM_CLIENT_ID = os.environ.get('ZOOM_CLIENT_ID')
    ZOOM_CLIENT_SECRET = os.environ.get('ZOOM_CLIENT_SECRET')
    ZOOM_USER_ID = os.environ.get('ZOOM_USER_ID', 'me')
    
    # Configuration des niveaux
    LEVELS = ['ABG', 'BBG', 'ZBG', 'IG', 'IAG']
    
    # Configuration des jours
    DAYS = {
        'MW': 'Monday-Wednesday',
        'TT': 'Tuesday-Thursday',
        'FS': 'Friday-Saturday',
        'SS': 'Sunday'
    }
    
    # Configuration des points
    POINTS_CONFIG = {
        'message': 1,  # Points par message
        'attendance': 5,  # Points par présence
        'bonus': 10  # Points bonus
    }
    
    # Configuration Excel
    EXCEL_FILE_PATH = os.environ.get('EXCEL_FILE_PATH', 'attached_assets/Kodjo English - Classes Schedules (1).xlsx')
    SHEET_NAME = os.environ.get('SHEET_NAME', "Fix Schedule")
    
    # Configuration du planificateur
    SCHEDULE_UPDATE_COURSES = {"day_of_week": "6", "hour": 0, "minute": 0}  # Dimanche à minuit
    SCHEDULE_CREATE_ZOOM = {"day_of_week": "6", "hour": 0, "minute": 5}  # Dimanche à 00:05
    SCHEDULE_GENERATE_MESSAGES = {"day_of_week": "6", "hour": 0, "minute": 10}  # Dimanche à 00:10
    SCHEDULE_SEND_DAILY_MESSAGES = {"hour": 8, "minute": 0}  # Quotidien à 8:00
    
    # Configuration de sécurité
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = 86400  # 24 heures en secondes
    
    # Template de message Telegram
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

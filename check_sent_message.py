from app import app, db
from models import Course
from telegram_bot import init_telegram_bot

with app.app_context():
    # Récupérer le dernier cours créé
    latest_course = Course.query.order_by(Course.id.desc()).first()
    if latest_course:
        print(f"Dernier cours: {latest_course.course_name}, Prof: {latest_course.teacher_name}")
        print(f"Jour: {latest_course.day_of_week}, Heure: {latest_course.start_time}")
        
        # Formater le message comme il aurait été envoyé
        bot = init_telegram_bot()
        message = bot.format_course_message(latest_course)
        
        print("\n--- MESSAGE FORMATÉ ---\n")
        print(message)
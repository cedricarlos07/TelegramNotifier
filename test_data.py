from app import app, db
from models import Course, Student, TelegramGroup, ZoomLink, User
from werkzeug.security import generate_password_hash
from datetime import datetime, time

def add_test_data():
    with app.app_context():
        # Créer un utilisateur admin si non existant
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@example.com',
                password=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)

        # Créer quelques cours
        courses_data = [
            {
                'name': 'Anglais Débutant',
                'code': 'ENG101',
                'professor': 'John Smith',
                'day_of_week': 1,
                'start_time': time(9, 0),
                'end_time': time(10, 30),
                'description': 'Cours d\'anglais pour débutants'
            },
            {
                'name': 'Anglais Intermédiaire',
                'code': 'ENG201',
                'professor': 'Sarah Johnson',
                'day_of_week': 2,
                'start_time': time(14, 0),
                'end_time': time(15, 30),
                'description': 'Cours d\'anglais niveau intermédiaire'
            },
            {
                'name': 'Anglais Avancé',
                'code': 'ENG301',
                'professor': 'Michael Brown',
                'day_of_week': 3,
                'start_time': time(16, 0),
                'end_time': time(17, 30),
                'description': 'Cours d\'anglais niveau avancé'
            }
        ]

        for course_data in courses_data:
            if not Course.query.filter_by(code=course_data['code']).first():
                course = Course(**course_data)
                db.session.add(course)

        # Créer quelques étudiants
        students_data = [
            {
                'telegram_id': '123456789',
                'username': 'alice_m',
                'first_name': 'Alice',
                'last_name': 'Martin',
                'email': 'alice@example.com'
            },
            {
                'telegram_id': '987654321',
                'username': 'bob_d',
                'first_name': 'Bob',
                'last_name': 'Dupont',
                'email': 'bob@example.com'
            },
            {
                'telegram_id': '456789123',
                'username': 'claire_b',
                'first_name': 'Claire',
                'last_name': 'Bernard',
                'email': 'claire@example.com'
            }
        ]

        for student_data in students_data:
            if not Student.query.filter_by(email=student_data['email']).first():
                student = Student(**student_data)
                db.session.add(student)

        # Créer quelques groupes Telegram
        groups_data = [
            {
                'group_name': 'Anglais Débutant - Groupe A',
                'group_id': '-1001234567890',
                'description': 'Groupe Telegram pour le cours d\'anglais débutant'
            },
            {
                'group_name': 'Anglais Intermédiaire - Groupe B',
                'group_id': '-1009876543210',
                'description': 'Groupe Telegram pour le cours d\'anglais intermédiaire'
            }
        ]

        for group_data in groups_data:
            if not TelegramGroup.query.filter_by(group_id=group_data['group_id']).first():
                group = TelegramGroup(**group_data)
                db.session.add(group)

        # Créer quelques liens Zoom
        zoom_links_data = [
            {
                'course_id': 1,  # Pour Anglais Débutant
                'meeting_id': '123456789',
                'password': 'abc123',
                'url': 'https://zoom.us/j/123456789'
            },
            {
                'course_id': 2,  # Pour Anglais Intermédiaire
                'meeting_id': '987654321',
                'password': 'xyz789',
                'url': 'https://zoom.us/j/987654321'
            }
        ]

        for link_data in zoom_links_data:
            if not ZoomLink.query.filter_by(meeting_id=link_data['meeting_id']).first():
                link = ZoomLink(**link_data)
                db.session.add(link)

        # Sauvegarder les changements
        db.session.commit()
        print("Données de test ajoutées avec succès !")

if __name__ == '__main__':
    add_test_data() 
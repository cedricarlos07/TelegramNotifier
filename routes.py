from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Course, TelegramGroup, Student, Point, RankingHistory
from datetime import datetime, timedelta
import pandas as pd
import logging
import random
from io import BytesIO
import os
from dotenv import load_dotenv
from functools import wraps

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Création du Blueprint
main = Blueprint('main', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Accès refusé. Vous devez être administrateur.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Routes d'authentification
@main.route('/login', methods=['GET', 'POST'])
    def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        logger.info(f"Tentative de connexion pour l'utilisateur: {username}")
        
        user = User.query.filter_by(username=username).first()
        
        if user:
            logger.info(f"Utilisateur trouvé: {username}")
            if user.check_password(password):
                logger.info(f"Mot de passe correct pour l'utilisateur: {username}")
                login_user(user)
                return redirect(url_for('main.dashboard'))
            else:
                logger.warning(f"Mot de passe incorrect pour l'utilisateur: {username}")
        else:
            logger.warning(f"Utilisateur non trouvé: {username}")
            
        flash('Nom d\'utilisateur ou mot de passe incorrect', 'error')
    return render_template('login.html')

@main.route('/logout')
    @login_required
    def logout():
        logout_user()
    return redirect(url_for('main.login'))

@main.route('/change-password', methods=['GET', 'POST'])
    @login_required
    def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        
        if check_password_hash(current_user.password, current_password):
            current_user.password = generate_password_hash(new_password)
            db.session.commit()
            flash('Mot de passe modifié avec succès', 'success')
            return redirect(url_for('main.dashboard'))
        flash('Mot de passe actuel incorrect', 'error')
    return render_template('change_password.html')

# Routes principales
@main.route('/')
@main.route('/admin')
    @login_required
def dashboard():
    return render_template('dashboard.html')

@main.route('/analytics')
    @login_required
def analytics():
    # Récupération des données pour les graphiques
    courses = Course.query.all()
    students = Student.query.all()
    groups = TelegramGroup.query.all()
    
    # Données pour le graphique de distribution des cours par jour
        days_of_week = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
    course_days_values = [0] * 7
    
    for course in courses:
        if course.day_of_week:
            day_index = course.day_of_week - 1
            if 0 <= day_index < 7:
                course_days_values[day_index] += 1
    
    # Données pour le graphique de distribution des étudiants par cours
    course_student_counts = []
    for course in courses:
        count = len(course.students)
        course_student_counts.append({
            'name': course.name,
            'count': count
        })
    
    return render_template('analytics.html',
                         courses=courses,
                         students=students,
                         groups=groups,
                         days_of_week=days_of_week,
            course_days_values=course_days_values,
                         course_student_counts=course_student_counts)

# Routes pour les cours
@main.route('/courses')
    @login_required
    def courses():
    courses = Course.query.all()
    return render_template('courses.html', courses=courses)

@main.route('/courses/add', methods=['POST'])
    @login_required
    def add_course():
    name = request.form.get('name')
    day_of_week = int(request.form.get('day_of_week'))
    start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
    end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()
    
    course = Course(
        name=name,
                day_of_week=day_of_week,
                start_time=start_time,
        end_time=end_time
            )

    db.session.add(course)
            db.session.commit()
    flash('Cours ajouté avec succès', 'success')
    return redirect(url_for('main.courses'))

@main.route('/courses/edit/<int:course_id>', methods=['POST'])
@login_required
    def edit_course(course_id):
            course = Course.query.get_or_404(course_id)
    course.name = request.form.get('name')
    course.day_of_week = int(request.form.get('day_of_week'))
    course.start_time = datetime.strptime(request.form.get('start_time'), '%H:%M').time()
    course.end_time = datetime.strptime(request.form.get('end_time'), '%H:%M').time()

            db.session.commit()
    flash('Cours modifié avec succès', 'success')
    return redirect(url_for('main.courses'))

@main.route('/courses/delete/<int:course_id>', methods=['POST'])
@login_required
    def delete_course(course_id):
            course = Course.query.get_or_404(course_id)
            db.session.delete(course)
            db.session.commit()
    flash('Cours supprimé avec succès', 'success')
    return redirect(url_for('main.courses'))

# Routes pour les groupes Telegram
@main.route('/telegram-groups')
@login_required
def telegram_groups():
    groups = TelegramGroup.query.all()
    return render_template('telegram_groups.html', groups=groups)

@main.route('/telegram-groups/add', methods=['POST'])
    @login_required
def add_telegram_group():
    name = request.form.get('name')
    chat_id = request.form.get('chat_id')
    
    group = TelegramGroup(name=name, chat_id=chat_id)
    db.session.add(group)
            db.session.commit()
    flash('Groupe ajouté avec succès', 'success')
    return redirect(url_for('main.telegram_groups'))

@main.route('/telegram-groups/<int:group_id>/edit', methods=['POST'])
    @login_required
def edit_telegram_group(group_id):
    group = TelegramGroup.query.get_or_404(group_id)
    group.name = request.form.get('name')
    group.chat_id = request.form.get('chat_id')

            db.session.commit()
    flash('Groupe modifié avec succès', 'success')
    return redirect(url_for('main.telegram_groups'))

@main.route('/telegram-groups/<int:group_id>/delete', methods=['POST'])
    @login_required
def delete_telegram_group(group_id):
    group = TelegramGroup.query.get_or_404(group_id)
    db.session.delete(group)
                db.session.commit()
    flash('Groupe supprimé avec succès', 'success')
    return redirect(url_for('main.telegram_groups'))

# Routes pour les étudiants
@main.route('/students')
    @login_required
def students():
    students = Student.query.all()
    courses = Course.query.all()
    return render_template('students.html', students=students, courses=courses)

@main.route('/students/assign-course', methods=['POST'])
    @login_required
def assign_student_to_course():
    student_id = request.form.get('student_id')
    course_id = request.form.get('course_id')
    
    student = Student.query.get_or_404(student_id)
    course = Course.query.get_or_404(course_id)
    
    student.courses.append(course)
            db.session.commit()
    flash('Étudiant assigné au cours avec succès', 'success')
    return redirect(url_for('main.students'))

@main.route('/students/remove-course', methods=['POST'])
    @login_required
def remove_student_from_course():
    student_id = request.form.get('student_id')
    course_id = request.form.get('course_id')
    
    student = Student.query.get_or_404(student_id)
    course = Course.query.get_or_404(course_id)
    
    student.courses.remove(course)
                db.session.commit()
    flash('Étudiant retiré du cours avec succès', 'success')
    return redirect(url_for('main.students'))

# Routes pour les classements
@main.route('/rankings')
    @login_required
def rankings():
    return render_template('rankings.html')

@main.route('/api/send-rankings', methods=['POST'])
    @login_required
def send_rankings():
    period_type = request.form.get('period_type', 'weekly')
    rankings = generate_rankings(period_type)
    message = format_rankings_message(rankings, period_type)
    
    # Envoi du message aux groupes Telegram
    groups = TelegramGroup.query.all()
    for group in groups:
        try:
            send_telegram_message(group.chat_id, message)
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du classement au groupe {group.name}: {str(e)}")
    
    return jsonify({'success': True})

@main.route('/admin-users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users)

@main.route('/api/users', methods=['POST'])
    @login_required
@admin_required
def create_user():
    data = request.form
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    is_admin = data.get('is_admin') == 'on'
    
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Ce nom d\'utilisateur existe déjà'}), 400
        
    if User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Cet email existe déjà'}), 400
    
    user = User(username=username, email=email, is_admin=is_admin)
    user.set_password(password)
    db.session.add(user)
                db.session.commit()
    
    return jsonify({'success': True})

@main.route('/api/users/<int:user_id>', methods=['GET'])
    @login_required
@admin_required
def get_user(user_id):
    user = User.query.get_or_404(user_id)
                return jsonify({
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'is_admin': user.is_admin
    })

@main.route('/api/users/<int:user_id>', methods=['PUT'])
    @login_required
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.form
    
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    is_admin = data.get('is_admin') == 'on'
    
    if username != user.username and User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': 'Ce nom d\'utilisateur existe déjà'}), 400
        
    if email != user.email and User.query.filter_by(email=email).first():
        return jsonify({'success': False, 'message': 'Cet email existe déjà'}), 400
    
    user.username = username
    user.email = email
    user.is_admin = is_admin
    
    if password:
        user.set_password(password)
    
            db.session.commit()
    return jsonify({'success': True})

@main.route('/api/users/<int:user_id>', methods=['DELETE'])
    @login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        return jsonify({'success': False, 'message': 'Vous ne pouvez pas supprimer votre propre compte'}), 400
    
    db.session.delete(user)
            db.session.commit()
    return jsonify({'success': True})

# Routes pour les erreurs
@main.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

@main.errorhandler(500)
    def server_error(e):
        return render_template('500.html'), 500
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user, logout_user, login_user
from models import Course, Student, RankingHistory, User, ZoomAttendance, TelegramMessage
from extensions import db, csrf
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/login', methods=['GET', 'POST'])
@csrf.exempt
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.courses'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.courses'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect', 'error')
            
    return render_template('login.html')

@bp.route('/courses')
@login_required
def courses():
    courses = Course.query.all()
    return render_template('courses.html', courses=courses)

@bp.route('/rankings')
@login_required
def rankings():
    rankings = RankingHistory.query.order_by(RankingHistory.date.desc()).all()
    return render_template('rankings.html', rankings=rankings)

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not check_password_hash(current_user.password, current_password):
            flash('Mot de passe actuel incorrect', 'error')
            return redirect(url_for('main.change_password'))
            
        if new_password != confirm_password:
            flash('Les nouveaux mots de passe ne correspondent pas', 'error')
            return redirect(url_for('main.change_password'))
            
        current_user.password = generate_password_hash(new_password)
        db.session.commit()
        
        flash('Mot de passe modifié avec succès', 'success')
        return redirect(url_for('main.courses'))
        
    return render_template('change_password.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté', 'success')
    return redirect(url_for('main.index'))

@bp.route('/zoom-links')
@login_required
def zoom_links():
    # Récupérer les liens Zoom pour aujourd'hui
    today = datetime.now().date()
    attendances = ZoomAttendance.query.filter(
        ZoomAttendance.date == today
    ).all()
    return render_template('zoom_links.html', attendances=attendances)

@bp.route('/analytics')
@login_required
def analytics():
    # Statistiques pour les 30 derniers jours
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # Nombre de messages envoyés
    messages_count = TelegramMessage.query.filter(
        TelegramMessage.timestamp.between(start_date, end_date)
    ).count()
    
    # Nombre de présences Zoom
    attendances_count = ZoomAttendance.query.filter(
        ZoomAttendance.join_time.between(start_date, end_date)
    ).count()
    
    return render_template('analytics.html',
                         messages_count=messages_count,
                         attendances_count=attendances_count)

@bp.route('/scenarios')
@login_required
def scenarios():
    return render_template('scenarios.html')

@bp.route('/bot-status')
@login_required
def bot_status():
    # Vérifier l'état du bot Telegram
    from telegram_bot import TelegramBot
    bot = TelegramBot()
    bot_info = bot.check_bot_status()
    return render_template('bot_status.html', bot_info=bot_info)

@bp.route('/logs')
@login_required
def logs():
    # Récupérer les derniers logs
    with open('app.log', 'r') as f:
        logs = f.readlines()[-100:]  # Dernières 100 lignes
    return render_template('logs.html', logs=logs)

@bp.route('/courses/add', methods=['POST'])
@login_required
@csrf.exempt
def add_course():
    try:
        name = request.form.get('name')
        code = request.form.get('code')
        professor = request.form.get('professor')
        schedule = request.form.get('schedule')
        
        if not all([name, code, professor, schedule]):
            return {'success': False, 'message': 'Tous les champs sont requis'}, 400
            
        course = Course(
            name=name,
            code=code,
            professor=professor,
            schedule=schedule
        )
        
        db.session.add(course)
        db.session.commit()
        
        return {'success': True, 'message': 'Cours ajouté avec succès'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': str(e)}, 500

@bp.route('/courses/<int:course_id>', methods=['DELETE'])
@login_required
@csrf.exempt
def delete_course(course_id):
    try:
        course = Course.query.get_or_404(course_id)
        db.session.delete(course)
        db.session.commit()
        return {'success': True, 'message': 'Cours supprimé avec succès'}
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': str(e)}, 500

@bp.route('/courses/<int:course_id>/students')
@login_required
@csrf.exempt
def get_course_students(course_id):
    try:
        course = Course.query.get_or_404(course_id)
        students = [{'id': s.id, 'name': s.name, 'email': s.email} for s in course.students]
        return {'success': True, 'students': students}
    except Exception as e:
        return {'success': False, 'message': str(e)}, 500

@bp.route('/courses/<int:course_id>/students/<int:student_id>', methods=['DELETE'])
@login_required
@csrf.exempt
def remove_student_from_course(course_id, student_id):
    try:
        course = Course.query.get_or_404(course_id)
        student = Student.query.get_or_404(student_id)
        
        if student in course.students:
            course.students.remove(student)
            db.session.commit()
            return {'success': True, 'message': 'Étudiant retiré du cours avec succès'}
        else:
            return {'success': False, 'message': 'L\'étudiant n\'est pas inscrit à ce cours'}, 400
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': str(e)}, 500 
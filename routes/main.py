from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user, logout_user
from models import Course, Student, RankingHistory, User, ZoomAttendance, TelegramMessage
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

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
        TelegramMessage.created_at.between(start_date, end_date)
    ).count()
    
    # Nombre de présences Zoom
    attendances_count = ZoomAttendance.query.filter(
        ZoomAttendance.date.between(start_date, end_date)
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
    from telegram_bot import bot
    bot_info = bot.get_me()
    return render_template('bot_status.html', bot_info=bot_info)

@bp.route('/logs')
@login_required
def logs():
    # Récupérer les derniers logs
    with open('app.log', 'r') as f:
        logs = f.readlines()[-100:]  # Dernières 100 lignes
    return render_template('logs.html', logs=logs) 
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user, logout_user
from models import Course, Student, RankingHistory, User
from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

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
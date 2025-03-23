from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import User, Course, Student, RankingHistory
from extensions import db

bp = Blueprint('admin', __name__, url_prefix='/admin')

@bp.before_request
def require_admin():
    if not current_user.is_authenticated or not current_user.is_admin:
        flash('You need to be an admin to access this page.')
        return redirect(url_for('main.index'))

@bp.route('/')
def index():
    return render_template('admin/index.html')

@bp.route('/users')
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@bp.route('/courses')
def courses():
    courses = Course.query.all()
    return render_template('admin/courses.html', courses=courses) 
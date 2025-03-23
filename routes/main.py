from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from models import Course, Student, RankingHistory
from extensions import db

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
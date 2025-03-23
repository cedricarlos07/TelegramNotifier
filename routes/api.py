from flask import Blueprint, jsonify, request
from flask_login import login_required
from models import Course, Student, RankingHistory
from extensions import db

bp = Blueprint('api', __name__, url_prefix='/api')

@bp.route('/courses')
@login_required
def get_courses():
    courses = Course.query.all()
    return jsonify([{
        'id': course.id,
        'name': course.name,
        'teacher': course.teacher_name,
        'schedule_date': course.schedule_date.isoformat(),
        'telegram_group_id': course.telegram_group_id
    } for course in courses])

@bp.route('/rankings')
@login_required
def get_rankings():
    rankings = RankingHistory.query.order_by(RankingHistory.date.desc()).all()
    return jsonify([{
        'id': ranking.id,
        'student_name': ranking.student_name,
        'points': ranking.points,
        'date': ranking.date.isoformat()
    } for ranking in rankings]) 
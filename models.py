from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db

class AppSettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    simulation_mode = db.Column(db.Boolean, default=False)
    test_group_id = db.Column(db.String(100), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<AppSettings simulation_mode={self.simulation_mode}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'simulation_mode': self.simulation_mode,
            'test_group_id': self.test_group_id,
            'updated_at': self.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        }

class TelegramMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_group_id = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.String(100), nullable=False)
    user_name = db.Column(db.String(100), nullable=True)
    message_content = db.Column(db.Text, nullable=True)
    message_id = db.Column(db.String(100), nullable=False)
    points = db.Column(db.Integer, default=1)  # Base points per message
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<TelegramMessage from {self.user_name} in group {self.telegram_group_id}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'telegram_group_id': self.telegram_group_id,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'message_content': self.message_content,
            'message_id': self.message_id,
            'points': self.points,
            'timestamp': self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }

class ZoomAttendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    user_id = db.Column(db.String(100), nullable=False)
    user_name = db.Column(db.String(100), nullable=True)
    join_time = db.Column(db.DateTime, nullable=False)
    leave_time = db.Column(db.DateTime, nullable=True)
    duration = db.Column(db.Integer, default=0)  # Duration in minutes
    points = db.Column(db.Integer, default=10)  # Base points per attendance
    
    course = db.relationship('Course', backref=db.backref('attendances', lazy=True))
    
    def __repr__(self):
        return f"<ZoomAttendance {self.user_name} for course_id {self.course_id}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'join_time': self.join_time.strftime("%Y-%m-%d %H:%M:%S") if self.join_time else None,
            'leave_time': self.leave_time.strftime("%Y-%m-%d %H:%M:%S") if self.leave_time else None,
            'duration': self.duration,
            'points': self.points
        }

class UserRanking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    telegram_group_id = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.String(100), nullable=False)
    user_name = db.Column(db.String(100), nullable=True)
    message_points = db.Column(db.Integer, default=0)
    attendance_points = db.Column(db.Integer, default=0)
    total_points = db.Column(db.Integer, default=0)
    rank = db.Column(db.Integer, nullable=True)
    last_message_date = db.Column(db.DateTime, nullable=True)
    last_attendance_date = db.Column(db.DateTime, nullable=True)
    period_start = db.Column(db.DateTime, nullable=False)  # Start of ranking period (day/week/month)
    period_end = db.Column(db.DateTime, nullable=False)  # End of ranking period
    period_type = db.Column(db.String(10), nullable=False)  # 'daily', 'weekly' or 'monthly'
    
    def __repr__(self):
        return f"<UserRanking {self.user_name} in group {self.telegram_group_id} ({self.period_type})>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'telegram_group_id': self.telegram_group_id,
            'user_id': self.user_id,
            'user_name': self.user_name,
            'message_points': self.message_points,
            'attendance_points': self.attendance_points,
            'total_points': self.total_points,
            'rank': self.rank,
            'last_message_date': self.last_message_date.strftime("%Y-%m-%d %H:%M:%S") if self.last_message_date else None,
            'last_attendance_date': self.last_attendance_date.strftime("%Y-%m-%d %H:%M:%S") if self.last_attendance_date else None,
            'period_start': self.period_start.strftime("%Y-%m-%d") if self.period_start else None,
            'period_end': self.period_end.strftime("%Y-%m-%d") if self.period_end else None,
            'period_type': self.period_type
        }

class Course(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_name = db.Column(db.String(100), nullable=False)
    teacher_name = db.Column(db.String(100), nullable=False)
    telegram_group_id = db.Column(db.String(100), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0-6, Monday is 0
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    schedule_date = db.Column(db.Date, nullable=True)  # The next occurrence date
    zoom_link = db.Column(db.String(255), nullable=True)
    zoom_meeting_id = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Course {self.course_name} on {self.day_of_week} at {self.start_time}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'course_name': self.course_name,
            'teacher_name': self.teacher_name,
            'telegram_group_id': self.telegram_group_id,
            'day_of_week': self.day_of_week,
            'start_time': self.start_time.strftime("%H:%M") if self.start_time else None,
            'end_time': self.end_time.strftime("%H:%M") if self.end_time else None,
            'schedule_date': self.schedule_date.strftime("%Y-%m-%d") if self.schedule_date else None,
            'zoom_link': self.zoom_link,
            'zoom_meeting_id': self.zoom_meeting_id
        }

class ScheduledMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    message_text = db.Column(db.Text, nullable=False)
    scheduled_date = db.Column(db.Date, nullable=False)
    scheduled_time = db.Column(db.Time, nullable=False)
    telegram_group_id = db.Column(db.String(100), nullable=False)
    is_sent = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    course = db.relationship('Course', backref=db.backref('scheduled_messages', lazy=True))
    
    def __repr__(self):
        return f"<ScheduledMessage for course_id {self.course_id} on {self.scheduled_date}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'course_id': self.course_id,
            'message_text': self.message_text,
            'scheduled_date': self.scheduled_date.strftime("%Y-%m-%d") if self.scheduled_date else None,
            'scheduled_time': self.scheduled_time.strftime("%H:%M") if self.scheduled_time else None,
            'telegram_group_id': self.telegram_group_id,
            'is_sent': self.is_sent,
            'sent_at': self.sent_at.strftime("%Y-%m-%d %H:%M:%S") if self.sent_at else None
        }

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f"<User {self.username}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            'last_login': self.last_login.strftime("%Y-%m-%d %H:%M:%S") if self.last_login else None
        }

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    level = db.Column(db.String(20), nullable=False)  # INFO, WARNING, ERROR
    scenario = db.Column(db.String(100), nullable=True)  # Which scenario the log is related to
    message = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Log {self.level}: {self.message[:50]}...>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'level': self.level,
            'scenario': self.scenario,
            'message': self.message,
            'timestamp': self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }

class Scenario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    display_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    schedule = db.Column(db.String(100), nullable=False)
    actions = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), nullable=False, default="fa-calendar-alt")
    color = db.Column(db.String(50), nullable=False, default="primary")
    python_code = db.Column(db.Text, nullable=True)
    is_custom_code = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Scenario {self.name}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'schedule': self.schedule,
            'actions': self.actions,
            'icon': self.icon,
            'color': self.color,
            'python_code': self.python_code,
            'is_custom_code': self.is_custom_code,
            'created_at': self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            'updated_at': self.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        }

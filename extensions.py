from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_apscheduler import APScheduler

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
scheduler = APScheduler() 
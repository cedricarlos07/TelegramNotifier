import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_apscheduler import APScheduler

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the base class
db = SQLAlchemy(model_class=Base)

# Initialize the scheduler
scheduler = APScheduler()

# Create the Flask application
app = Flask(__name__)

# Configure the application
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///courses.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions with the app
db.init_app(app)
scheduler.init_app(app)

# Create database tables within the application context
with app.app_context():
    # Import models to ensure they're registered with SQLAlchemy
    from models import Course, ScheduledMessage, Log
    
    # Create all database tables
    db.create_all()
    
    logger.info("Database tables created successfully")

# Register all routes for the application
from routes import register_routes
register_routes(app)

# Initialize the scheduler with all the tasks
from scheduler import initialize_scheduler
initialize_scheduler(app)

# Start the scheduler
scheduler.start()

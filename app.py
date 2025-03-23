import os
import logging
from flask import Flask
from flask_apscheduler import APScheduler
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from datetime import datetime, timedelta
from dotenv import load_dotenv
from models import db, User, TelegramGroup, Course, Student, RankingHistory
from routes import main
from config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO if os.environ.get('FLASK_ENV') == 'production' else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize extensions
scheduler = APScheduler()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app(config_class=Config):
    # Create the Flask application
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_class)
    
    # Configure database URL for Render
    if os.environ.get('RENDER'):
        database_url = os.environ.get('DATABASE_URL')
        if database_url and database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    
    # Initialize extensions with the app
    db.init_app(app)
    scheduler.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    app.register_blueprint(main)
    
    # Initialize scheduler
    from scheduler import initialize_scheduler
    initialize_scheduler(app)
    
    # Initialize database
    with app.app_context():
        db.create_all()
        # Create admin user if not exists
        if not User.query.first():
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password(os.environ.get('ADMIN_PASSWORD', 'admin123'))
            db.session.add(admin)
            db.session.commit()
            logger.info("Admin user created successfully")
    
    # Start scheduler only in production
    if os.environ.get('FLASK_ENV') == 'production':
        scheduler.start()
    
    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

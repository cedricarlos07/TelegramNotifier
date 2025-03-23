import os
import logging
from flask import Flask, jsonify
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from datetime import datetime, timedelta
from dotenv import load_dotenv
from models import db, User, TelegramGroup, Course, Student, RankingHistory
from config import Config
from extensions import login_manager, csrf, scheduler
from flask_migrate import Migrate
from logging.handlers import RotatingFileHandler
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(
    level=logging.INFO if os.environ.get('FLASK_ENV') == 'production' else logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    scheduler.init_app(app)
    
    # Initialize rate limiter if available
    try:
        from flask_limiter import Limiter
        from flask_limiter.util import get_remote_address
        limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=["200 per day", "50 per hour"]
        )
    except ImportError:
        logger.warning("Flask-Limiter not installed. Rate limiting is disabled.")
    
    # Initialize migrations
    migrate = Migrate(app, db)
    
    # Configure login manager
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        try:
            return User.query.get(int(user_id))
        except SQLAlchemyError as e:
            logger.error(f"Database error while loading user: {str(e)}")
            return None
    
    # Register blueprints
    from routes import init_app as init_routes
    init_routes(app)
    
    # Health check route
    @app.route('/health')
    def health_check():
        try:
            # Vérifier la connexion à la base de données
            db.session.execute('SELECT 1')
            return jsonify({
                'status': 'healthy',
                'database': 'connected',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        except SQLAlchemyError as e:
            logger.error(f"Health check failed: {str(e)}")
            return jsonify({
                'status': 'unhealthy',
                'database': 'disconnected',
                'error': str(e)
            }), 500
    
    # Global error handlers
    @app.errorhandler(HTTPException)
    def handle_exception(e):
        response = {
            "code": e.code,
            "name": e.name,
            "description": e.description,
        }
        return jsonify(response), e.code
    
    @app.errorhandler(SQLAlchemyError)
    def handle_database_error(e):
        logger.error(f"Database error: {str(e)}")
        return jsonify({
            "code": 500,
            "name": "Database Error",
            "description": "Une erreur de base de données s'est produite."
        }), 500
    
    @app.errorhandler(Exception)
    def handle_generic_exception(e):
        logger.error(f"Unhandled exception: {str(e)}")
        return jsonify({
            "code": 500,
            "name": "Internal Server Error",
            "description": "Une erreur inattendue s'est produite."
        }), 500
    
    # Initialize database
    with app.app_context():
        try:
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
        except SQLAlchemyError as e:
            logger.error(f"Database initialization error: {str(e)}")
            raise
    
    # Initialize scheduler only in production
    if os.environ.get('FLASK_ENV') == 'production':
        try:
            from scheduler import initialize_scheduler, schedule_jobs
            initialize_scheduler(app)
            schedule_jobs()
        except Exception as e:
            logger.error(f"Scheduler initialization error: {str(e)}")
    
    # Configure logging
    if not app.debug and not app.testing:
        if os.environ.get('RENDER'):
            # Sur Render, utiliser les logs système
            app.logger.setLevel(logging.INFO)
            app.logger.info('Application startup')
        else:
            # En local, utiliser les fichiers de log
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
            file_handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
            ))
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.setLevel(logging.INFO)
            app.logger.info('Application startup')
    
    return app

# Create the application instance
app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

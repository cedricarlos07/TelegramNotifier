import os
import logging
from flask import Flask
from flask_apscheduler import APScheduler
from flask_login import LoginManager
from datetime import datetime, timedelta
from dotenv import load_dotenv
from models import db, User, TelegramGroup, Course, Student, RankingHistory
from routes import main

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the scheduler
scheduler = APScheduler()

# Initialize the login manager
login_manager = LoginManager()

# Create the Flask application
app = Flask(__name__)

# Load environment variables
load_dotenv()

# Configure the application
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key")

# Configure SQLAlchemy
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///telegram_notifier.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions with the app
db.init_app(app)
scheduler.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'main.login'
login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
login_manager.login_message_category = 'warning'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Création des tables dans la base de données
def create_tables():
    try:
        logger.info("Début de l'initialisation de la base de données...")
        
        # Supprimer toutes les tables existantes
        logger.info("Suppression des tables existantes...")
        db.drop_all()
        
        # Créer toutes les tables
        logger.info("Création des nouvelles tables...")
        db.create_all()
        
        # Créer l'utilisateur admin s'il n'existe pas
        logger.info("Vérification de l'existence de l'utilisateur admin...")
        admin = User.query.filter_by(username='admin').first()
        
        if not admin:
            logger.info("Création de l'utilisateur admin...")
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            logger.info("Utilisateur admin créé avec succès!")
        else:
            logger.info("L'utilisateur admin existe déjà.")
            
        # Vérifier que l'utilisateur admin a bien été créé
        admin = User.query.filter_by(username='admin').first()
        if admin:
            logger.info(f"Utilisateur admin trouvé dans la base de données: {admin.username}")
        else:
            logger.error("L'utilisateur admin n'a pas été créé correctement!")
            
        logger.info("Base de données initialisée avec succès!")
        
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données : {str(e)}")
        raise e

# Register the blueprint
app.register_blueprint(main)

# Initialize the scheduler with all the tasks
from scheduler import initialize_scheduler
initialize_scheduler(app)

# Start the scheduler
scheduler.start()

# Initialiser la base de données au démarrage de l'application
with app.app_context():
    create_tables()

if __name__ == '__main__':
    app.run(debug=True)

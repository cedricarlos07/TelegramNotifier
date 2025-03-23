import os
from app import app, db, create_tables
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

def init_database():
    with app.app_context():
        # Supprimer toutes les tables existantes
        db.drop_all()
        # Créer toutes les tables
        db.create_all()
        # Créer l'utilisateur admin
        create_tables()
        print("Base de données initialisée avec succès !")

if __name__ == '__main__':
    init_database() 
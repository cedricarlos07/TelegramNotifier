#!/usr/bin/env python3
"""
Script pour mettre à jour le modèle Scenario avec les colonnes pour le code Python personnalisé.
"""

import os
import sys
from app import app, db
from datetime import datetime

def add_columns_to_scenario():
    """Ajouter les colonnes python_code et is_custom_code à la table scenario."""
    try:
        # Se connecter à la base de données
        with app.app_context():
            # Vérifier si les colonnes existent déjà
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('scenario')]
            
            changes_made = False
            
            # Ajouter les colonnes si elles n'existent pas
            if 'python_code' not in columns:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE scenario ADD COLUMN python_code TEXT'))
                    conn.commit()
                print("Colonne 'python_code' ajoutée avec succès")
                changes_made = True
                
            if 'is_custom_code' not in columns:
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE scenario ADD COLUMN is_custom_code BOOLEAN DEFAULT FALSE'))
                    conn.commit()
                print("Colonne 'is_custom_code' ajoutée avec succès")
                changes_made = True
            
            if not changes_made:
                print("Aucune modification nécessaire, les colonnes existent déjà")
            
            return True
    except Exception as e:
        print(f"Erreur lors de la mise à jour de la table: {str(e)}")
        return False

if __name__ == '__main__':
    print("Mise à jour du modèle Scenario...")
    success = add_columns_to_scenario()
    if success:
        print("Mise à jour terminée avec succès")
    else:
        print("Échec de la mise à jour")
        sys.exit(1)
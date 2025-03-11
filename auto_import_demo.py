import os
import sys
import random
from datetime import datetime, timedelta, time
import pandas as pd

# Ajouter le répertoire courant au chemin d'importation
sys.path.append('.')

from app import app, db
from models import Course, Log, AppSettings
from telegram_bot import init_telegram_bot
from config import EXCEL_FILE_PATH, SHEET_NAME
from excel_processor import excel_processor


def create_demo_course_from_excel():
    """
    Créer un cours de démonstration à partir du fichier Excel et envoyer une notification.
    Cette fonction est automatisée pour ne nécessiter aucune intervention manuelle.
    """
    print("Démarrage de l'importation automatisée des cours de démonstration...")
    
    with app.app_context():
        try:
            # Vérifier et configurer le mode simulation
            bot = init_telegram_bot()
            # Activer automatiquement le mode simulation
            test_group_id = "-1002486921694"  # ID du groupe test
            bot.toggle_simulation_mode(enabled=True, test_group_id=test_group_id)
            print(f"Mode simulation activé avec ID de groupe: {test_group_id}")
            
            # Charger le fichier Excel
            print(f"Chargement du fichier Excel: {EXCEL_FILE_PATH}, feuille: {SHEET_NAME}")
            try:
                df = pd.read_excel(EXCEL_FILE_PATH, sheet_name=SHEET_NAME)
                print(f"Excel chargé avec succès: {len(df)} lignes")
                print(f"Colonnes disponibles: {df.columns.tolist()}")
            except Exception as e:
                print(f"Erreur lors du chargement du fichier Excel: {str(e)}")
                return
                
            # Supprimer les anciens cours de démo
            old_courses = Course.query.filter_by(telegram_group_id=test_group_id).all()
            for old_course in old_courses:
                db.session.delete(old_course)
            db.session.commit()
            print(f"{len(old_courses)} cours de démonstration précédents supprimés")
            
            # Traiter une ligne du fichier Excel pour créer un cours
            success_count = 0
            row = df.iloc[0]  # Prendre la première ligne
            
            try:
                # Extraire les données du cours
                course_name = row.get('Salma Choufani - ABG - SS - 2:00pm')
                teacher_name = row.get('Salma Choufani')
                day_str = row.get('DAY')
                start_time_str = row.get('TIME (France)')
                
                print(f"Données extraites: cours={course_name}, prof={teacher_name}, jour={day_str}, heure={start_time_str}")
                
                # Convertir les types de données
                day_of_week = excel_processor._get_day_of_week_index(day_str)
                start_time = excel_processor._parse_time(start_time_str)
                
                # Calculer l'heure de fin (1 heure plus tard)
                if start_time:
                    hour = start_time.hour
                    minute = start_time.minute
                    end_hour = hour + 1
                    end_time = time(end_hour % 24, minute)
                else:
                    print(f"Format d'heure invalide: {start_time_str}")
                    # Valeur par défaut
                    start_time = time(20, 30)
                    end_time = time(21, 30)
                
                # Utiliser des valeurs par défaut si nécessaire
                if day_of_week == -1:
                    day_of_week = 0  # Lundi par défaut
                
                # Calculer la prochaine date d'occurrence
                next_date = excel_processor._get_next_occurrence(day_of_week)
                
                # Vérifier le nom du cours
                if not isinstance(course_name, str) or pd.isna(course_name):
                    course_name = "Cours d'anglais - Niveau intermédiaire"
                
                # Vérifier le nom de l'enseignant
                if not isinstance(teacher_name, str) or pd.isna(teacher_name):
                    teacher_name = "Prof. John Smith"
                
                # Générer un lien Zoom fictif
                zoom_link = f"https://zoom.us/j/{random.randint(10000000000, 99999999999)}"
                zoom_meeting_id = str(random.randint(100000000, 999999999))
                
                # Créer le cours
                new_course = Course(
                    course_name=course_name,
                    teacher_name=teacher_name,
                    telegram_group_id=test_group_id,
                    day_of_week=day_of_week,
                    start_time=start_time,
                    end_time=end_time,
                    schedule_date=next_date,
                    zoom_link=zoom_link,
                    zoom_meeting_id=zoom_meeting_id
                )
                
                db.session.add(new_course)
                db.session.commit()
                success_count += 1
                print(f"Cours créé: {course_name}, ID: {new_course.id}")
                
                # Envoyer une notification pour ce cours
                print("Envoi de la notification...")
                msg = bot.format_course_message(new_course)
                if msg and bot.send_message(test_group_id, msg, is_simulation=True):
                    print("Notification envoyée avec succès!")
                else:
                    print("Échec de l'envoi de la notification")
                
            except Exception as e:
                print(f"Erreur lors de la création du cours: {str(e)}")
            
            # Journaliser l'action
            log_entry = Log(
                level="INFO",
                scenario="auto_demo_import",
                message=f"Import Excel automatisé: {success_count} cours créé"
            )
            db.session.add(log_entry)
            db.session.commit()
            
            if success_count > 0:
                print(f"{success_count} cours importé avec succès!")
            else:
                print("Aucun cours n'a pu être importé.")
            
        except Exception as e:
            print(f"Erreur globale: {str(e)}")


if __name__ == "__main__":
    create_demo_course_from_excel()
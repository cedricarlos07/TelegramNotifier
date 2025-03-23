import os
from app import app, db
from models import User, Course, TelegramGroup, Student, ZoomLink
from werkzeug.security import generate_password_hash
import pandas as pd
from datetime import datetime, time
import logging
import numpy as np
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_time(time_str):
    """Parse time string in format '19h 30 GMT' or '20h 30 France'"""
    if pd.isna(time_str):
        return None
    match = re.search(r'(\d{1,2})h\s*(\d{2})', time_str)
    if match:
        hour = int(match.group(1))
        minute = int(match.group(2))
        return time(hour, minute)
    return None

def extract_level_from_topic(topic):
    """Extract level (ABG, BBG, etc.) from topic"""
    match = re.search(r'(ABG|BBG|ZBG|IAG|IG)', topic)
    return match.group(1) if match else 'Unknown'

def extract_session_type(topic):
    """Extract session type (TT, SS, FS) from topic"""
    match = re.search(r'(TT|SS|FS)', topic)
    return match.group(1) if match else 'Unknown'

def init_db():
    with app.app_context():
        # Suppression des tables existantes
        db.drop_all()
        
        # Création des nouvelles tables
        db.create_all()
        
        # Création de l'utilisateur admin
        admin = User(
            username='admin',
            email='admin@example.com',
            password=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        
        try:
            # Lecture du fichier Excel
            excel_file = 'attached_assets/Kodjo English - Classes Schedules (1).xlsx'
            df = pd.read_excel(excel_file)
            logger.info(f"Fichier Excel lu avec succès")
            
            # Nettoyage des noms de colonnes
            df.columns = df.columns.str.strip()
            
            # Traitement des données
            for index, row in df.iterrows():
                try:
                    # Extraction des informations du cours
                    topic = str(row['Topic']).strip()
                    coach = str(row['Coach']).strip()
                    start_date_time = pd.to_datetime(row['Start Date & Time'])
                    zoom_link = str(row['Zoom Link']).strip()
                    zoom_id = str(row['ZOOM ID']).strip()
                    time_gmt = str(row['TIME (GMT)']).strip()
                    time_france = str(row['TIME (France)']).strip()
                    
                    # Extraction des informations supplémentaires
                    level = extract_level_from_topic(topic)
                    session_type = extract_session_type(topic)
                    
                    # Création du code unique pour le cours
                    code = f"{level}-{session_type}-{index+100}"
                    
                    # Parsing des heures
                    start_time = parse_time(time_gmt)
                    if not start_time:
                        start_time = time(14, 0)  # Valeur par défaut
                    
                    end_time = time(start_time.hour + 1, start_time.minute)
                    
                    # Détermination du jour de la semaine
                    day_of_week = start_date_time.weekday() + 1  # 1 = Lundi, 7 = Dimanche
                    
                    # Création du cours
                    course = Course(
                        name=topic,
                        code=code,
                        professor=coach,
                        day_of_week=day_of_week,
                        start_time=start_time,
                        end_time=end_time,
                        description=f"Cours d'anglais niveau {level} - {session_type}"
                    )
                    db.session.add(course)
                    db.session.flush()  # Pour obtenir l'ID du cours
                    logger.info(f"Cours ajouté : {topic}")
                    
                    # Création du lien Zoom
                    zoom_link_obj = ZoomLink(
                        course_id=course.id,
                        meeting_id=zoom_id,
                        url=zoom_link,
                        password="123456"  # Mot de passe par défaut
                    )
                    db.session.add(zoom_link_obj)
                    logger.info(f"Lien Zoom ajouté pour le cours : {topic}")
                    
                    # Création du groupe Telegram (si nécessaire)
                    group = TelegramGroup(
                        group_id=f"-100{zoom_id}",  # ID temporaire basé sur l'ID Zoom
                        group_name=f"Groupe {level} - {session_type}",
                        description=f"Groupe Telegram pour le cours {topic}"
                    )
                    db.session.add(group)
                    logger.info(f"Groupe Telegram ajouté : {group.group_name}")
                    
                    # Commit après chaque cours pour éviter de perdre toutes les données en cas d'erreur
                    db.session.commit()
                
                except Exception as e:
                    logger.error(f"Erreur lors du traitement de la ligne {index} : {str(e)}")
                    db.session.rollback()
                    continue
            
            logger.info("Base de données initialisée avec succès")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la base de données : {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    init_db() 
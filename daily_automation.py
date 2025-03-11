#!/usr/bin/env python3
"""
Script d'automatisation quotidienne pour importer les cours depuis Excel
et envoyer les notifications Telegram.

Ce script peut être exécuté automatiquement via un cron job:
0 8 * * * python /chemin/vers/daily_automation.py
"""

import os
import sys
import logging
from datetime import datetime, date, timedelta

# Ajouter le répertoire courant au chemin d'importation
sys.path.append('.')

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("automation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("daily_automation")

# Importer les modules nécessaires
try:
    from app import app, db
    from models import Course, Log
    from excel_processor import excel_processor
    from telegram_bot import init_telegram_bot
    logger.info("Modules importés avec succès")
except Exception as e:
    logger.error(f"Erreur lors de l'importation des modules: {str(e)}")
    sys.exit(1)

def update_courses_from_excel():
    """Mettre à jour les cours depuis le fichier Excel."""
    try:
        results = excel_processor.update_course_schedules()
        logger.info(f"Mise à jour des cours depuis Excel: {results}")
        return results
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des cours: {str(e)}")
        return {"success": 0, "errors": 1}

def create_zoom_links_for_courses():
    """Créer des liens Zoom pour les cours qui n'en ont pas."""
    try:
        results = excel_processor.create_zoom_links()
        logger.info(f"Création des liens Zoom: {results}")
        return results
    except Exception as e:
        logger.error(f"Erreur lors de la création des liens Zoom: {str(e)}")
        return {"created": 0, "errors": 1}

def send_notifications_for_today():
    """Envoyer les notifications pour les cours d'aujourd'hui."""
    try:
        with app.app_context():
            # Initialiser le bot Telegram
            bot = init_telegram_bot()
            
            # Récupérer les cours d'aujourd'hui
            today = date.today()
            today_courses = Course.query.filter_by(schedule_date=today).all()
            
            logger.info(f"Cours programmés aujourd'hui: {len(today_courses)}")
            
            # Envoyer les notifications
            if today_courses:
                results = bot.send_daily_course_notifications(today_courses)
                logger.info(f"Notifications envoyées: {results}")
                
                # Log de l'action
                log_entry = Log(
                    level="INFO",
                    scenario="daily_automation",
                    message=f"Notifications automatiques: {results['success']} succès, {results['failure']} échecs"
                )
                db.session.add(log_entry)
                db.session.commit()
                
                return results
            else:
                logger.info("Aucun cours programmé aujourd'hui")
                return {"success": 0, "failure": 0}
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi des notifications: {str(e)}")
        return {"success": 0, "failure": 1}

def run_automation():
    """Exécuter toutes les étapes de l'automatisation quotidienne."""
    logger.info("Démarrage de l'automatisation quotidienne")
    
    with app.app_context():
        try:
            # 1. Mettre à jour les cours depuis Excel
            update_results = update_courses_from_excel()
            
            # 2. Créer des liens Zoom
            zoom_results = create_zoom_links_for_courses()
            
            # 3. Envoyer les notifications pour les cours d'aujourd'hui
            notification_results = send_notifications_for_today()
            
            # Résumé des actions
            summary = {
                "update_courses": update_results,
                "create_zoom": zoom_results,
                "send_notifications": notification_results
            }
            
            logger.info(f"Automatisation terminée: {summary}")
            
            # Log de l'action complète
            log_entry = Log(
                level="INFO",
                scenario="daily_automation",
                message=f"Automatisation quotidienne terminée avec succès"
            )
            db.session.add(log_entry)
            db.session.commit()
            
            return summary
            
        except Exception as e:
            error_msg = f"Erreur lors de l'automatisation quotidienne: {str(e)}"
            logger.error(error_msg)
            
            # Log de l'erreur
            with app.app_context():
                log_entry = Log(
                    level="ERROR",
                    scenario="daily_automation",
                    message=error_msg
                )
                db.session.add(log_entry)
                db.session.commit()
            
            return {"error": str(e)}

if __name__ == "__main__":
    run_automation()
import os
from datetime import datetime
import sqlite3
from telegram import Bot
import asyncio
import logging
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv(override=True)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Récupérer le token du bot depuis les variables d'environnement
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
logger.info(f"Token chargé: {TELEGRAM_BOT_TOKEN[:10]}...")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Le token du bot Telegram n'est pas configuré dans le fichier .env")

async def get_group_members(bot, group_id):
    """Récupère la liste des membres d'un groupe Telegram."""
    try:
        members = []
        logger.info(f"Tentative de connexion au groupe {group_id}")
        
        # Récupérer les informations du chat
        chat = await bot.get_chat(group_id)
        logger.info(f"Chat récupéré: {chat.title}")
        
        # Récupérer les administrateurs
        admins = await chat.get_administrators()
        logger.info(f"Nombre d'administrateurs trouvés: {len(admins)}")
        
        for admin in admins:
            if not admin.user.is_bot:
                members.append({
                    'telegram_id': str(admin.user.id),
                    'username': admin.user.username or '',
                    'first_name': admin.user.first_name or '',
                    'last_name': admin.user.last_name or ''
                })
        
        # Pour les groupes publics, récupérer les membres
        if chat.type in ['supergroup', 'channel']:
            logger.info(f"Récupération des membres pour le groupe public {chat.title}")
            async for member in chat.get_members():
                if not member.user.is_bot and not any(m['telegram_id'] == str(member.user.id) for m in members):
                    members.append({
                        'telegram_id': str(member.user.id),
                        'username': member.user.username or '',
                        'first_name': member.user.first_name or '',
                        'last_name': member.user.last_name or ''
                    })
        
        return members
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des membres du groupe {group_id}: {str(e)}")
        return []

async def sync_telegram_students():
    """Synchronise les étudiants depuis les groupes Telegram vers la base de données."""
    try:
        # Connexion à la base de données
        db_path = os.path.join('instance', 'telegram_notifier.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Récupérer tous les groupes Telegram
        cursor.execute("SELECT group_id, group_name FROM telegram_groups")
        telegram_groups = cursor.fetchall()

        if not telegram_groups:
            logger.warning("Aucun groupe Telegram trouvé dans la base de données")
            return

        # Initialiser le bot Telegram
        bot = Bot(token=TELEGRAM_BOT_TOKEN)
        
        total_students = 0
        for group_id, group_name in telegram_groups:
            logger.info(f"Traitement du groupe : {group_name}")
            
            # Récupérer les membres du groupe
            members = await get_group_members(bot, group_id)
            
            for member in members:
                # Vérifier si l'étudiant existe déjà
                cursor.execute("""
                    SELECT id FROM students 
                    WHERE telegram_id = ?
                """, (member['telegram_id'],))
                
                existing_student = cursor.fetchone()
                
                if not existing_student:
                    # Ajouter le nouvel étudiant
                    cursor.execute("""
                        INSERT INTO students (
                            telegram_id, username, first_name, last_name, created_at
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        member['telegram_id'],
                        member['username'],
                        member['first_name'],
                        member['last_name'],
                        datetime.now()
                    ))
                    
                    student_id = cursor.lastrowid
                    logger.info(f"Nouvel étudiant ajouté : {member['first_name']} {member['last_name']}")
                    total_students += 1
                    
                    # Trouver les cours associés au groupe
                    cursor.execute("""
                        SELECT c.id 
                        FROM courses c
                        JOIN course_telegram_groups ctg ON c.id = ctg.course_id
                        JOIN telegram_groups tg ON ctg.group_id = tg.id
                        WHERE tg.group_id = ?
                    """, (group_id,))
                    
                    courses = cursor.fetchall()
                    for course_id in courses:
                        # Lier l'étudiant aux cours du groupe
                        cursor.execute("""
                            INSERT INTO student_courses (student_id, course_id)
                            VALUES (?, ?)
                        """, (student_id, course_id[0]))
                else:
                    # Mettre à jour les informations de l'étudiant existant
                    cursor.execute("""
                        UPDATE students 
                        SET username = ?,
                            first_name = ?,
                            last_name = ?
                        WHERE telegram_id = ?
                    """, (
                        member['username'],
                        member['first_name'],
                        member['last_name'],
                        member['telegram_id']
                    ))

        # Valider les changements
        conn.commit()
        logger.info(f"Synchronisation terminée. {total_students} nouveaux étudiants ajoutés.")

    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation : {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
        await bot.close()

def main():
    """Point d'entrée principal."""
    try:
        asyncio.run(sync_telegram_students())
    except KeyboardInterrupt:
        logger.info("Synchronisation interrompue par l'utilisateur")
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution : {str(e)}")

if __name__ == '__main__':
    main() 
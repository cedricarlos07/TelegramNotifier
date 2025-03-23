import sqlite3
import logging
from typing import Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_telegram_group_ids(group_mappings: Dict[str, str]):
    """
    Met à jour les IDs des groupes Telegram dans la base de données.
    
    Args:
        group_mappings (dict): Dictionnaire avec les anciens IDs comme clés et les nouveaux IDs comme valeurs
        Exemple: {
            "-100123456789": "-1001234567890",  # ancien_id: nouveau_id
            "-100987654321": "-1001987654321"
        }
    """
    try:
        # Connexion à la base de données
        db_path = 'instance/telegram_notifier.db'
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Afficher les groupes actuels
        logger.info("Groupes actuels dans la base de données :")
        cursor.execute("SELECT id, group_id, group_name FROM telegram_groups")
        current_groups = cursor.fetchall()
        for group in current_groups:
            logger.info(f"ID: {group[0]}, Group ID: {group[1]}, Nom: {group[2]}")

        # Mettre à jour les IDs des groupes
        for old_id, new_id in group_mappings.items():
            cursor.execute("""
                UPDATE telegram_groups 
                SET group_id = ? 
                WHERE group_id = ?
            """, (new_id, old_id))
            logger.info(f"Mise à jour du groupe {old_id} vers {new_id}")

        # Afficher les groupes mis à jour
        logger.info("\nGroupes après mise à jour :")
        cursor.execute("SELECT id, group_id, group_name FROM telegram_groups")
        updated_groups = cursor.fetchall()
        for group in updated_groups:
            logger.info(f"ID: {group[0]}, Group ID: {group[1]}, Nom: {group[2]}")

        # Valider les changements
        conn.commit()
        logger.info("Mise à jour terminée avec succès")

    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour : {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    # Exemple d'utilisation :
    # Remplacez ces valeurs par les vrais IDs que vous avez obtenus
    group_mappings = {
        # Format : "ancien_id": "nouveau_id"
        "-100123456789": "-1001234567890",  # Exemple
    }
    
    # Vérification des mappings
    if not group_mappings:
        logger.error("Veuillez ajouter les mappings des IDs de groupe avant d'exécuter le script")
    else:
        update_telegram_group_ids(group_mappings) 
from models import db, TelegramGroup, Course, CourseTelegramGroup
from datetime import datetime

def get_telegram_groups():
    """
    Récupère tous les groupes Telegram avec leurs cours associés.
    """
    return TelegramGroup.query.all()

def get_telegram_group(group_id):
    """
    Récupère un groupe Telegram spécifique avec ses cours associés.
    """
    return TelegramGroup.query.get(group_id)

def add_telegram_group(group_id, group_name, description, course_ids=None):
    """
    Ajoute un nouveau groupe Telegram avec ses associations de cours.
    """
    try:
        group = TelegramGroup(
            group_id=str(group_id),
            group_name=group_name,
            description=description
        )
        db.session.add(group)
        db.session.flush()

        if course_ids:
            for course_id in course_ids:
                course = Course.query.get(int(course_id))
                if course:
                    association = CourseTelegramGroup(
                        course_id=course.id,
                        group_id=group.id
                    )
                    db.session.add(association)

        db.session.commit()
        return True, "Groupe Telegram ajouté avec succès"
    except Exception as e:
        db.session.rollback()
        return False, f"Erreur lors de l'ajout du groupe : {str(e)}"

def update_telegram_group(group_id, group_name, description, course_ids=None):
    """
    Met à jour un groupe Telegram et ses associations de cours.
    """
    try:
        group = TelegramGroup.query.get(group_id)
        if not group:
            return False, "Groupe non trouvé"

        group.group_name = group_name
        group.description = description
        group.updated_at = datetime.utcnow()

        # Mise à jour des associations de cours
        if course_ids is not None:
            # Supprimer les anciennes associations
            CourseTelegramGroup.query.filter_by(group_id=group.id).delete()
            
            # Ajouter les nouvelles associations
            for course_id in course_ids:
                course = Course.query.get(int(course_id))
                if course:
                    association = CourseTelegramGroup(
                        course_id=course.id,
                        group_id=group.id
                    )
                    db.session.add(association)

        db.session.commit()
        return True, "Groupe Telegram mis à jour avec succès"
    except Exception as e:
        db.session.rollback()
        return False, f"Erreur lors de la mise à jour du groupe : {str(e)}"

def delete_telegram_group(group_id):
    """
    Supprime un groupe Telegram et ses associations.
    """
    try:
        group = TelegramGroup.query.get(group_id)
        if not group:
            return False, "Groupe non trouvé"

        # Supprimer les associations
        CourseTelegramGroup.query.filter_by(group_id=group.id).delete()
        # Supprimer le groupe
        db.session.delete(group)
        db.session.commit()
        return True, "Groupe Telegram supprimé avec succès"
    except Exception as e:
        db.session.rollback()
        return False, f"Erreur lors de la suppression du groupe : {str(e)}" 
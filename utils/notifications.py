def send_course_notification(course, message):
    """
    Envoie une notification de cours aux groupes Telegram associés.
    """
    try:
        # Récupérer les groupes Telegram associés au cours
        telegram_groups = course.telegram_groups.all()
        
        for group in telegram_groups:
            # Envoyer le message au groupe
            send_telegram_message(group.group_id, message)
            
        return True, "Notifications envoyées avec succès"
    except Exception as e:
        return False, f"Erreur lors de l'envoi des notifications : {str(e)}"

def send_telegram_message(group_id, message):
    """
    Envoie un message à un groupe Telegram spécifique.
    """
    try:
        bot = telegram.Bot(token=app.config['TELEGRAM_BOT_TOKEN'])
        bot.send_message(
            chat_id=group_id,
            text=message,
            parse_mode='HTML'
        )
        return True
    except Exception as e:
        print(f"Erreur lors de l'envoi du message au groupe {group_id}: {str(e)}")
        return False 
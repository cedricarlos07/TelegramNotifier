import logging
import telegram
from telegram import Bot
from telegram.error import TelegramError
from datetime import datetime, timedelta
import asyncio
from config import TELEGRAM_BOT_TOKEN, MESSAGE_TEMPLATE
from app import db, app
from models import Log, AppSettings, TelegramMessage, UserRanking

logger = logging.getLogger(__name__)

class TelegramBot:
    """
    Telegram Bot class for handling all interactions with the Telegram API
    """
    def __init__(self):
        """Initialize the Telegram bot with the token."""
        self.bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
        self._init_app_settings()
        logger.info("Telegram bot initialized")
        
    def _run_sync(self, coroutine):
        """
        Run a coroutine synchronously
        
        Args:
            coroutine: The coroutine to run
            
        Returns:
            The result of the coroutine
        """
        try:
            # Essayer d'obtenir la boucle d'événements existante
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # Si aucune boucle d'événements n'est définie, en créer une nouvelle
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        # Utilisons un modèle plus sûr qui ne ferme pas la boucle
        if loop.is_running():
            # Si la boucle est déjà en cours d'exécution, utiliser run_coroutine_threadsafe
            future = asyncio.run_coroutine_threadsafe(coroutine, loop)
            return future.result()
        else:
            # Sinon, utiliser run_until_complete
            return loop.run_until_complete(coroutine)
    
    def _init_app_settings(self):
        """Initialize application settings if they don't exist."""
        settings = AppSettings.query.first()
        if not settings:
            settings = AppSettings(simulation_mode=False)
            db.session.add(settings)
            db.session.commit()
            logger.info("Application settings initialized")
    
    def is_simulation_mode(self):
        """Check if simulation mode is active."""
        settings = AppSettings.query.first()
        return settings.simulation_mode if settings else False
    
    def get_test_group_id(self):
        """Get the test group ID for simulation mode."""
        settings = AppSettings.query.first()
        return settings.test_group_id if settings else None
    
    def toggle_simulation_mode(self, enabled=True, test_group_id=None):
        """Toggle simulation mode on or off."""
        settings = AppSettings.query.first()
        if not settings:
            settings = AppSettings(simulation_mode=enabled, test_group_id=test_group_id)
            db.session.add(settings)
        else:
            settings.simulation_mode = enabled
            if test_group_id:
                settings.test_group_id = test_group_id
        
        try:
            db.session.commit()
            logger.info(f"Simulation mode {'enabled' if enabled else 'disabled'}")
            return settings.simulation_mode
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error toggling simulation mode: {str(e)}")
            return False
        
    def check_bot_status(self):
        """
        Vérifie l'état du bot et renvoie des informations détaillées.
        
        Returns:
            dict: Informations sur l'état du bot
        """
        status = {
            "success": False,
            "bot_id": None,
            "bot_username": None,
            "bot_first_name": None,
            "token_valid": False,
            "error": None
        }
        
        try:
            # Exécute get_me de manière synchrone
            bot_info = self._run_sync(self.bot.get_me())
            
            status["success"] = True
            status["bot_id"] = bot_info.id
            status["bot_username"] = bot_info.username
            status["bot_first_name"] = bot_info.first_name
            status["token_valid"] = True
            logger.info(f"Bot status check: ID={bot_info.id}, Username=@{bot_info.username}")
        except Exception as e:
            status["error"] = str(e)
            status["token_valid"] = False
            logger.error(f"Bot status check failed: {str(e)}")
        
        return status

    def send_message(self, chat_id, message, is_simulation=False):
        """
        Send a message to a specific Telegram chat.
        
        Args:
            chat_id (str): The Telegram chat ID
            message (str): The message to send
            is_simulation (bool): Whether this is a simulation message
            
        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Attempt to send message to chat_id: {chat_id}, simulation: {is_simulation}")
        
        # Vérifier l'état du bot avant d'envoyer un message
        bot_status = self.check_bot_status()
        if not bot_status["success"]:
            error_msg = f"Bot is not properly configured: {bot_status['error']}"
            logger.error(error_msg)
            log_entry = Log(level="ERROR", scenario="telegram_message", message=error_msg)
            db.session.add(log_entry)
            db.session.commit()
            return False
            
        # Check if simulation mode is active
        if self.is_simulation_mode() and not is_simulation:
            test_group_id = self.get_test_group_id()
            logger.info(f"Simulation mode active, redirecting to test group ID: {test_group_id}")
            if test_group_id:
                # Modify the message to indicate it's a simulation
                simulation_message = f"[SIMULATION]\n\n{message}"
                return self.send_message(test_group_id, simulation_message, is_simulation=True)
            else:
                logger.warning("Simulation mode is active but no test group ID is set")
                return False
        
        try:
            logger.info(f"Sending Telegram message to chat_id: {chat_id}")
            logger.info(f"Message content: {message[:100]}...")
            
            # Vérifions si le chat_id est un nombre ou une chaîne
            if chat_id and chat_id.strip():
                # Pour les cas où le chat_id pourrait contenir des caractères non numériques
                try:
                    # Tentons de convertir en entier, car Telegram préfère les ID numériques
                    if chat_id.startswith('-'):
                        # C'est un ID de groupe (négatif)
                        numeric_chat_id = int(chat_id)
                    else:
                        # C'est un ID d'utilisateur ou de chat privé
                        numeric_chat_id = int(chat_id)
                    
                    logger.info(f"Using numeric chat_id: {numeric_chat_id}")
                    actual_chat_id = numeric_chat_id
                except ValueError:
                    # Si ce n'est pas un nombre, utilisez-le tel quel (par exemple, @username)
                    logger.info(f"Using string chat_id: {chat_id}")
                    actual_chat_id = chat_id
            else:
                logger.error(f"Invalid chat_id: '{chat_id}'")
                return False
            
            # Ajouter une vérification des permissions du bot dans le groupe
            try:
                # Essayer d'obtenir des informations sur le chat pour vérifier les permissions
                chat_info = self._run_sync(self.bot.get_chat(actual_chat_id))
                logger.info(f"Chat info: ID={chat_info.id}, Type={chat_info.type}, Title={getattr(chat_info, 'title', 'N/A')}")
                
                # Si c'est un groupe, vérifier si le bot est administrateur
                if hasattr(chat_info, 'all_members_are_administrators'):
                    logger.info(f"All members are admins: {chat_info.all_members_are_administrators}")
                
                # Vérifier les permissions du bot si disponible
                try:
                    member = self._run_sync(self.bot.get_chat_member(actual_chat_id, bot_status["bot_id"]))
                    logger.info(f"Bot's status in the chat: {member.status}")
                    if member.status not in ['administrator', 'creator']:
                        logger.warning(f"Bot is not an admin in the group (status: {member.status}). Some features may not work.")
                except Exception as perm_e:
                    logger.warning(f"Could not check bot permissions: {str(perm_e)}")
                    
            except Exception as chat_e:
                logger.warning(f"Could not get chat info: {str(chat_e)}")
            
            # Envoyer le message
            response = self._run_sync(self.bot.send_message(
                chat_id=actual_chat_id,
                text=message,
                parse_mode='Markdown'
            ))
            
            logger.info(f"Message sent successfully to chat {chat_id}, response: {response}")
            # Log the success to the database
            log_entry = Log(level="INFO", scenario="telegram_message", message=f"Message sent to chat {chat_id}")
            db.session.add(log_entry)
            db.session.commit()
            return True
        except Exception as e:
            error_msg = f"Failed to send message to chat {chat_id}: {str(e)}"
            logger.error(error_msg)
            # Log the error to the database
            log_entry = Log(level="ERROR", scenario="telegram_message", message=error_msg)
            db.session.add(log_entry)
            db.session.commit()
            return False
    
    def record_message(self, user_id, user_name, chat_id, message_id, message_content=None):
        """
        Record a message for points calculation.
        
        Args:
            user_id (str): The Telegram user ID
            user_name (str): The Telegram username
            chat_id (str): The Telegram chat ID
            message_id (str): The Telegram message ID
            message_content (str): The content of the message (optional)
            
        Returns:
            TelegramMessage: The created message record
        """
        # Create a new message record
        message = TelegramMessage(
            telegram_group_id=chat_id,
            user_id=user_id,
            user_name=user_name,
            message_id=message_id,
            message_content=message_content
        )
        db.session.add(message)
        
        # Update user rankings
        self._update_user_rankings(user_id, user_name, chat_id, message_points=message.points)
        
        db.session.commit()
        logger.debug(f"Recorded message from {user_name} in group {chat_id}")
        return message
    
    def _update_user_rankings(self, user_id, user_name, chat_id, message_points=0, attendance_points=0):
        """
        Update user rankings with new points.
        
        Args:
            user_id (str): The Telegram user ID
            user_name (str): The Telegram username
            chat_id (str): The Telegram chat ID
            message_points (int): Points for messages
            attendance_points (int): Points for attendance
            
        Returns:
            tuple: (daily_ranking, weekly_ranking, monthly_ranking) The updated ranking records
        """
        now = datetime.utcnow()
        
        # Calculate current day period (00:00 to 23:59:59)
        start_of_day = datetime(now.year, now.month, now.day, 0, 0, 0)
        end_of_day = start_of_day + timedelta(days=1) - timedelta(seconds=1)
        
        # Calculate current week period (Monday to Sunday)
        start_of_week = now - timedelta(days=now.weekday())
        start_of_week = datetime(start_of_week.year, start_of_week.month, start_of_week.day, 0, 0, 0)
        end_of_week = start_of_week + timedelta(days=7) - timedelta(seconds=1)
        
        # Calculate current month period
        start_of_month = datetime(now.year, now.month, 1, 0, 0, 0)
        if now.month == 12:
            end_of_month = datetime(now.year + 1, 1, 1, 0, 0, 0) - timedelta(seconds=1)
        else:
            end_of_month = datetime(now.year, now.month + 1, 1, 0, 0, 0) - timedelta(seconds=1)
        
        # Update daily ranking
        daily_ranking = UserRanking.query.filter_by(
            user_id=user_id,
            telegram_group_id=chat_id,
            period_start=start_of_day,
            period_end=end_of_day,
            period_type='daily'
        ).first()
        
        if not daily_ranking:
            daily_ranking = UserRanking(
                user_id=user_id,
                user_name=user_name,
                telegram_group_id=chat_id,
                period_start=start_of_day,
                period_end=end_of_day,
                period_type='daily'
            )
            db.session.add(daily_ranking)
        
        if message_points > 0:
            daily_ranking.message_points += message_points
            daily_ranking.last_message_date = now
        
        if attendance_points > 0:
            daily_ranking.attendance_points += attendance_points
            daily_ranking.last_attendance_date = now
        
        daily_ranking.total_points = daily_ranking.message_points + daily_ranking.attendance_points
        
        # Update weekly ranking
        weekly_ranking = UserRanking.query.filter_by(
            user_id=user_id,
            telegram_group_id=chat_id,
            period_start=start_of_week,
            period_end=end_of_week,
            period_type='weekly'
        ).first()
        
        if not weekly_ranking:
            weekly_ranking = UserRanking(
                user_id=user_id,
                user_name=user_name,
                telegram_group_id=chat_id,
                period_start=start_of_week,
                period_end=end_of_week,
                period_type='weekly'
            )
            db.session.add(weekly_ranking)
        
        if message_points > 0:
            weekly_ranking.message_points += message_points
            weekly_ranking.last_message_date = now
        
        if attendance_points > 0:
            weekly_ranking.attendance_points += attendance_points
            weekly_ranking.last_attendance_date = now
        
        weekly_ranking.total_points = weekly_ranking.message_points + weekly_ranking.attendance_points
        
        # Update monthly ranking
        monthly_ranking = UserRanking.query.filter_by(
            user_id=user_id,
            telegram_group_id=chat_id,
            period_start=start_of_month,
            period_end=end_of_month,
            period_type='monthly'
        ).first()
        
        if not monthly_ranking:
            monthly_ranking = UserRanking(
                user_id=user_id,
                user_name=user_name,
                telegram_group_id=chat_id,
                period_start=start_of_month,
                period_end=end_of_month,
                period_type='monthly'
            )
            db.session.add(monthly_ranking)
        
        if message_points > 0:
            monthly_ranking.message_points += message_points
            monthly_ranking.last_message_date = now
        
        if attendance_points > 0:
            monthly_ranking.attendance_points += attendance_points
            monthly_ranking.last_attendance_date = now
        
        monthly_ranking.total_points = monthly_ranking.message_points + monthly_ranking.attendance_points
        
        db.session.commit()
        
        # Calculate ranks later in a separate operation to avoid doing it for each message
        
        return (daily_ranking, weekly_ranking, monthly_ranking)

    def format_course_message(self, course):
        """
        Format a course into a Telegram message.
        
        Args:
            course (Course): The course object from the database
            
        Returns:
            str: Formatted message for Telegram
        """
        if not course.schedule_date or not course.start_time:
            logger.warning(f"Course {course.id} has no scheduled date or time")
            return None
            
        date_str = course.schedule_date.strftime("%d/%m/%Y")
        time_str = course.start_time.strftime("%H:%M") 
        
        # Format the message using the template
        formatted_message = MESSAGE_TEMPLATE.format(
            date=date_str,
            time=time_str,
            course_name=course.course_name,
            teacher_name=course.teacher_name,
            zoom_link=course.zoom_link or "Lien non disponible",
            zoom_meeting_id=course.zoom_meeting_id or "ID non disponible"
        )
        
        return formatted_message

    def send_daily_course_notifications(self, courses):
        """
        Send notifications for all courses scheduled on a specific day.
        
        Args:
            courses (list): List of Course objects to send notifications for
            
        Returns:
            dict: Results with success and failure counts
        """
        results = {"success": 0, "failure": 0}
        
        for course in courses:
            # Format the message for this course
            message = self.format_course_message(course)
            if not message:
                continue
                
            # Send the message to the appropriate Telegram group
            if self.send_message(course.telegram_group_id, message):
                results["success"] += 1
            else:
                results["failure"] += 1
                
        # Log the results
        log_message = f"Sent {results['success']} course notifications, {results['failure']} failures"
        log_entry = Log(level="INFO", scenario="daily_notifications", message=log_message)
        db.session.add(log_entry)
        db.session.commit()
        
        logger.info(log_message)
        return results
    
    def record_zoom_attendance(self, course_id, user_id, user_name, join_time, leave_time=None, duration=0):
        """
        Record Zoom attendance for points calculation.
        
        Args:
            course_id (int): The course ID
            user_id (str): The user ID
            user_name (str): The username
            join_time (datetime): When the user joined
            leave_time (datetime): When the user left (optional)
            duration (int): Duration in minutes (optional)
            
        Returns:
            ZoomAttendance: The created attendance record
        """
        from models import ZoomAttendance, Course
        
        # Get the course to find the telegram_group_id
        course = Course.query.get(course_id)
        if not course:
            logger.error(f"Course with ID {course_id} not found")
            return None
        
        # Create a new attendance record
        attendance = ZoomAttendance(
            course_id=course_id,
            user_id=user_id,
            user_name=user_name,
            join_time=join_time,
            leave_time=leave_time,
            duration=duration
        )
        db.session.add(attendance)
        
        # Update user rankings
        self._update_user_rankings(
            user_id=user_id,
            user_name=user_name,
            chat_id=course.telegram_group_id,
            attendance_points=attendance.points
        )
        
        db.session.commit()
        logger.debug(f"Recorded Zoom attendance for {user_name} in course {course_id}")
        return attendance
        
    def calculate_rankings(self, period_type='weekly', telegram_group_id=None):
        """
        Calculate rankings for users in a period.
        
        Args:
            period_type (str): 'daily', 'weekly' or 'monthly'
            telegram_group_id (str): Optional group ID to filter by
            
        Returns:
            list: Sorted list of rankings
        """
        now = datetime.utcnow()
        
        # Calculate period dates
        if period_type == 'daily':
            # Daily period (current day)
            start_of_period = datetime(now.year, now.month, now.day, 0, 0, 0)
            end_of_period = start_of_period + timedelta(days=1) - timedelta(seconds=1)
        elif period_type == 'weekly':
            # Weekly period (Monday to Sunday)
            start_of_period = now - timedelta(days=now.weekday())
            start_of_period = datetime(start_of_period.year, start_of_period.month, start_of_period.day, 0, 0, 0)
            end_of_period = start_of_period + timedelta(days=7) - timedelta(seconds=1)
        else:  # monthly
            # Monthly period
            start_of_period = datetime(now.year, now.month, 1, 0, 0, 0)
            if now.month == 12:
                end_of_period = datetime(now.year + 1, 1, 1, 0, 0, 0) - timedelta(seconds=1)
            else:
                end_of_period = datetime(now.year, now.month + 1, 1, 0, 0, 0) - timedelta(seconds=1)
        
        # Query for rankings in this period
        query = UserRanking.query.filter_by(
            period_type=period_type,
            period_start=start_of_period,
            period_end=end_of_period
        )
        
        if telegram_group_id:
            query = query.filter_by(telegram_group_id=telegram_group_id)
        
        # Get all users and sort by total points
        rankings = query.all()
        rankings.sort(key=lambda r: r.total_points, reverse=True)
        
        # Update the rank field
        for i, ranking in enumerate(rankings):
            ranking.rank = i + 1
        
        db.session.commit()
        
        return rankings
        
    def get_top_users(self, telegram_group_id, period_type='weekly', limit=5):
        """
        Get the top users for a specific group and period.
        
        Args:
            telegram_group_id (str): The Telegram group ID
            period_type (str): 'daily', 'weekly' or 'monthly'
            limit (int): Number of top users to return
            
        Returns:
            list: List of top user rankings
        """
        rankings = self.calculate_rankings(period_type, telegram_group_id)
        return rankings[:limit]
        
    def send_ranking_message(self, telegram_group_id, period_type='weekly'):
        """
        Send a ranking message to a Telegram group.
        
        Args:
            telegram_group_id (str): The Telegram group ID
            period_type (str): 'daily', 'weekly' or 'monthly'
            
        Returns:
            bool: Success status
        """
        top_users = self.get_top_users(telegram_group_id, period_type)
        
        if not top_users:
            message = f"*Classement {period_type}*\n\nAucun participant pour le moment. Soyez le premier !"
        else:
            # Détermination du texte selon la période
            if period_type == 'daily':
                period_text = "du jour"
            elif period_type == 'weekly':
                period_text = "de la semaine"
            else:  # monthly
                period_text = "du mois"
                
            message = f"*🏆 MEILLEURS PARTICIPANTS {period_text.upper()} 🏆*\n\n"
            
            for i, user in enumerate(top_users):
                medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
                message += f"{medal} *{user.user_name}* - {user.total_points} points\n"
                message += f"  • Messages: {user.message_points} pts\n"
                message += f"  • Présences: {user.attendance_points} pts\n\n"
            
            message += "Continuez à participer pour monter dans le classement ! 💪"
        
        return self.send_message(telegram_group_id, message)

    def send_daily_rankings(self, courses=None):
        """
        Envoie les classements quotidiens à tous les groupes Telegram actifs.
        
        Args:
            courses (list): Liste optionnelle de cours pour filtrer les groupes
            
        Returns:
            dict: Résultats avec les compteurs de succès et d'échec
        """
        results = {"success": 0, "failure": 0}
        processed_groups = set()
        
        # Si des cours sont fournis, envoyer les classements seulement aux groupes de ces cours
        if courses:
            for course in courses:
                group_id = course.telegram_group_id
                if group_id and group_id not in processed_groups:
                    # Envoyer le classement quotidien
                    if self.send_ranking_message(group_id, 'daily'):
                        results["success"] += 1
                    else:
                        results["failure"] += 1
                    
                    processed_groups.add(group_id)
        else:
            # Sinon, envoyer à tous les groupes uniques dans la base de données
            from models import Course
            
            unique_groups = db.session.query(Course.telegram_group_id).distinct().all()
            for (group_id,) in unique_groups:
                if group_id and group_id not in processed_groups:
                    # Envoyer le classement quotidien
                    if self.send_ranking_message(group_id, 'daily'):
                        results["success"] += 1
                    else:
                        results["failure"] += 1
                    
                    processed_groups.add(group_id)
        
        # Journal des résultats
        log_message = f"Envoi de {results['success']} classements quotidiens, {results['failure']} échecs"
        log_entry = Log(level="INFO", scenario="daily_rankings", message=log_message)
        db.session.add(log_entry)
        db.session.commit()
        
        logger.info(log_message)
        return results

# Initialize bot later to avoid app context issues
telegram_bot = None

def init_telegram_bot():
    global telegram_bot
    if telegram_bot is None:
        with app.app_context():
            telegram_bot = TelegramBot()
    return telegram_bot

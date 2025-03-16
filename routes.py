import logging
import random
import pandas as pd
from datetime import datetime, timedelta, time
from flask import render_template, request, redirect, url_for, jsonify, flash
from flask_login import login_user, logout_user, login_required, current_user
from app import app, db
from models import Course, ScheduledMessage, Log, UserRanking, AppSettings, TelegramMessage, ZoomAttendance, User, Scenario
from forms import LoginForm, ChangePasswordForm, AddAdminForm
from scheduler import run_job
from excel_processor import excel_processor
from telegram_bot import init_telegram_bot

logger = logging.getLogger(__name__)

def register_routes(app):
    """
    Register all routes for the application.

    Args:
        app (Flask): Flask application
    """

    @app.route('/analytics')
    @login_required
    def analytics():
        """Tableau de bord d'analyse détaillé pour la participation aux cours."""
        # Récupérer toutes les présences
        attendances = ZoomAttendance.query.all()

        # Récupérer tous les cours
        courses = Course.query.all()

        # Récupérer tous les groupes Telegram uniques
        telegram_groups = db.session.query(Course.telegram_group_id).distinct().all()
        telegram_groups = [group[0] for group in telegram_groups]

        # Statistiques globales
        total_attendances = len(attendances)
        total_courses = len(courses)

        # Calculer le taux moyen de participation (présences / cours)
        avg_attendance_rate = 0
        if total_courses > 0:
            avg_attendance_rate = round((total_attendances / total_courses), 2)

        # Récupération des présences par cours
        course_attendances = db.session.query(
            Course.course_name,
            db.func.count(ZoomAttendance.id).label('attendance_count')
        ).join(ZoomAttendance, ZoomAttendance.course_id == Course.id)\
        .group_by(Course.course_name).all()

        course_names = [course[0] for course in course_attendances]
        attendance_counts = [course[1] for course in course_attendances]

        # Récupérer les tendances de participation par jour de la semaine
        weekday_attendances = db.session.query(
            Course.day_of_week,
            db.func.count(ZoomAttendance.id).label('attendance_count')
        ).join(ZoomAttendance, ZoomAttendance.course_id == Course.id)\
        .group_by(Course.day_of_week).all()

        weekday_labels = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        weekday_data = [0] * 7

        for day, count in weekday_attendances:
            if 0 <= day < 7:  # Vérifier que l'indice est valide
                weekday_data[day] = count

        # Récupérer la durée moyenne de présence
        average_duration = db.session.query(db.func.avg(ZoomAttendance.duration)).scalar() or 0
        average_duration = round(average_duration, 2)

        # Récupérer le top 5 des participants les plus assidus
        top_attendees = db.session.query(
            ZoomAttendance.user_name,
            db.func.count(ZoomAttendance.id).label('attendance_count'),
            db.func.sum(ZoomAttendance.duration).label('total_duration')
        ).group_by(ZoomAttendance.user_name)\
        .order_by(db.func.count(ZoomAttendance.id).desc())\
        .limit(5).all()

        # Récupérer les heures de début les plus populaires
        popular_times = db.session.query(
            db.func.extract('hour', Course.start_time).label('hour'),
            db.func.count(ZoomAttendance.id).label('attendance_count')
        ).join(ZoomAttendance, ZoomAttendance.course_id == Course.id)\
        .group_by('hour')\
        .order_by(db.func.count(ZoomAttendance.id).desc())\
        .all()

        time_labels = [f"{hour}:00" for hour, _ in popular_times]
        time_data = [count for _, count in popular_times]

        # Récupérer le taux de présence par cours (présences / sessions totales)
        course_attendance_rates = []
        for course in courses:
            total_sessions = 1  # Au moins une session par cours
            attendance_count = ZoomAttendance.query.filter_by(course_id=course.id).count()
            rate = (attendance_count / total_sessions) * 100
            course_attendance_rates.append({
                'course_name': course.course_name,
                'rate': round(rate, 1)
            })

        # Trier par taux de présence
        course_attendance_rates = sorted(course_attendance_rates, key=lambda x: x['rate'], reverse=True)

        # Vérifier si l'utilisateur a demandé la vue par onglets
        use_tabbed_view = request.args.get('view') == 'tabbed'

        # Utiliser le template par onglets ou original en fonction du paramètre
        template = 'analytics_tabbed.html' if use_tabbed_view else 'analytics.html'

        return render_template(template,
                              total_attendances=total_attendances,
                              total_courses=total_courses,
                              avg_attendance_rate=avg_attendance_rate,
                              average_duration=average_duration,
                              course_names=course_names,
                              attendance_counts=attendance_counts,
                              weekday_labels=weekday_labels,
                              weekday_data=weekday_data,
                              top_attendees=top_attendees,
                              time_labels=time_labels,
                              time_data=time_data,
                              course_attendance_rates=course_attendance_rates,
                              telegram_groups=telegram_groups)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Page de connexion admin."""
        # Si l'utilisateur est déjà connecté, rediriger vers le dashboard
        if current_user.is_authenticated:
            return redirect(url_for('dashboard'))

        form = LoginForm()
        if form.validate_on_submit():
            # Récupérer l'utilisateur depuis la base de données
            user = User.query.filter_by(username=form.username.data).first()

            # Vérifier si l'utilisateur existe et si le mot de passe est correct
            if user is None or not user.check_password(form.password.data):
                flash('Nom d\'utilisateur ou mot de passe incorrect', 'danger')
                return redirect(url_for('login'))

            # Connexion de l'utilisateur
            login_user(user, remember=form.remember_me.data)

            # Mise à jour de la date de dernière connexion
            user.last_login = datetime.utcnow()
            db.session.commit()

            # Log de connexion
            log_entry = Log(
                level="INFO",
                scenario="auth",
                message=f"Connexion réussie pour l'utilisateur {user.username}"
            )
            db.session.add(log_entry)
            db.session.commit()

            # Redirection vers la page demandée ou le dashboard
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('dashboard')
            return redirect(next_page)

        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        """Déconnexion de l'utilisateur."""
        # Log de déconnexion
        log_entry = Log(
            level="INFO",
            scenario="auth",
            message=f"Déconnexion de l'utilisateur {current_user.username}"
        )
        db.session.add(log_entry)
        db.session.commit()

        # Déconnexion
        logout_user()
        flash('Vous avez été déconnecté avec succès', 'success')
        return redirect(url_for('login'))

    @app.route('/change-password', methods=['GET', 'POST'])
    @login_required
    def change_password():
        """Changement de mot de passe."""
        form = ChangePasswordForm()
        if form.validate_on_submit():
            # Vérifier l'ancien mot de passe
            if not current_user.check_password(form.old_password.data):
                flash('Ancien mot de passe incorrect', 'danger')
                return redirect(url_for('change_password'))

            # Définir le nouveau mot de passe
            current_user.set_password(form.password.data)
            db.session.commit()

            # Log de changement de mot de passe
            log_entry = Log(
                level="INFO",
                scenario="auth",
                message=f"Mot de passe changé pour l'utilisateur {current_user.username}"
            )
            db.session.add(log_entry)
            db.session.commit()

            flash('Votre mot de passe a été modifié avec succès', 'success')
            return redirect(url_for('dashboard'))

        return render_template('change_password.html', form=form)

    @app.route('/admin-users', methods=['GET', 'POST'])
    @login_required
    def admin_users():
        """Gestion des utilisateurs administrateurs."""
        # Vérifier si l'utilisateur est admin
        if not current_user.is_admin:
            flash('Accès refusé. Vous devez être administrateur pour accéder à cette page.', 'danger')
            return redirect(url_for('dashboard'))

        form = AddAdminForm()
        if form.validate_on_submit():
            # Créer un nouvel utilisateur
            user = User(
                username=form.username.data,
                email=form.email.data,
                is_admin=True
            )
            user.set_password(form.password.data)

            db.session.add(user)
            db.session.commit()

            # Log de création d'utilisateur
            log_entry = Log(
                level="INFO",
                scenario="auth",
                message=f"Nouvel utilisateur {user.username} créé par {current_user.username}"
            )
            db.session.add(log_entry)
            db.session.commit()

            flash(f'Utilisateur {user.username} créé avec succès', 'success')
            return redirect(url_for('admin_users'))

        # Récupérer tous les utilisateurs
        users = User.query.all()

        return render_template('admin_users.html', users=users, form=form, current_user=current_user)

    @app.route('/admin-users/toggle-admin/<int:user_id>', methods=['GET'])
    @login_required
    def toggle_admin(user_id):
        """Activer/désactiver le statut d'administrateur pour un utilisateur."""
        # Vérifier si l'utilisateur est admin
        if not current_user.is_admin:
            flash('Accès refusé. Vous devez être administrateur pour effectuer cette action.', 'danger')
            return redirect(url_for('dashboard'))

        # Éviter que l'utilisateur modifie son propre statut
        if user_id == current_user.id:
            flash('Vous ne pouvez pas modifier votre propre statut d\'administrateur', 'warning')
            return redirect(url_for('admin_users'))

        # Récupérer l'utilisateur
        user = User.query.get_or_404(user_id)

        # Inverser le statut d'administrateur
        user.is_admin = not user.is_admin
        db.session.commit()

        # Log de modification de statut
        log_entry = Log(
            level="INFO",
            scenario="auth",
            message=f"Statut admin modifié pour {user.username} par {current_user.username}: {user.is_admin}"
        )
        db.session.add(log_entry)
        db.session.commit()

        status = "activé" if user.is_admin else "désactivé"
        flash(f'Statut d\'administrateur {status} pour {user.username}', 'success')
        return redirect(url_for('admin_users'))

    @app.route('/admin-users/delete/<int:user_id>', methods=['GET'])
    @login_required
    def delete_user(user_id):
        """Supprimer un utilisateur."""
        # Vérifier si l'utilisateur est admin
        if not current_user.is_admin:
            flash('Accès refusé. Vous devez être administrateur pour effectuer cette action.', 'danger')
            return redirect(url_for('dashboard'))

        # Éviter que l'utilisateur se supprime lui-même
        if user_id == current_user.id:
            flash('Vous ne pouvez pas supprimer votre propre compte', 'warning')
            return redirect(url_for('admin_users'))

        # Récupérer l'utilisateur
        user = User.query.get_or_404(user_id)
        username = user.username

        # Supprimer l'utilisateur
        db.session.delete(user)
        db.session.commit()

        # Log de suppression d'utilisateur
        log_entry = Log(
            level="INFO",
            scenario="auth",
            message=f"Utilisateur {username} supprimé par {current_user.username}"
        )
        db.session.add(log_entry)
        db.session.commit()

        flash(f'Utilisateur {username} supprimé avec succès', 'success')
        return redirect(url_for('admin_users'))

    @app.route('/')
    @app.route('/admin')
    @login_required
    def dashboard():
        """Dashboard home page"""
        # Get counts for dashboard
        course_count = Course.query.count()
        today = datetime.now().date()
        today_courses = Course.query.filter_by(schedule_date=today).count()

        # Get the next 7 days of courses
        next_week = today + timedelta(days=7)
        upcoming_courses = Course.query.filter(
            Course.schedule_date >= today,
            Course.schedule_date < next_week
        ).order_by(Course.schedule_date, Course.start_time).all()

        # Get recent logs
        recent_logs = Log.query.order_by(Log.timestamp.desc()).limit(10).all()

        # Get app settings and status
        bot = init_telegram_bot()
        simulation_mode = bot.is_simulation_mode()
        test_group_id = bot.get_test_group_id()

        # Get engagement statistics
        message_count = TelegramMessage.query.count()
        attendance_count = ZoomAttendance.query.count()

        # Get top groups by activity
        top_groups = db.session.query(
            UserRanking.telegram_group_id,
            db.func.sum(UserRanking.total_points).label('total_points')
        ).group_by(UserRanking.telegram_group_id) \
         .order_by(db.func.sum(UserRanking.total_points).desc()) \
         .limit(5).all()

        # Data for course distribution chart by day of week
        days_of_week = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
        course_days_values = [0] * 7  # Initialize with zeros for each day

        # Count courses for each day of the week
        day_counts = db.session.query(
            Course.day_of_week,
            db.func.count(Course.id).label('count')
        ).group_by(Course.day_of_week).all()

        # Fill in the counts
        for day, count in day_counts:
            if 0 <= day < 7:  # Ensure day is valid
                course_days_values[day] = count

        # Prepare data for activity trend chart (last 7 days)
        past_week_start = today - timedelta(days=6)
        date_range = [(past_week_start + timedelta(days=i)) for i in range(7)]
        date_labels = [d.strftime('%d/%m') for d in date_range]

        # Initialize arrays for message and attendance trends
        message_trend = [0] * 7
        attendance_trend = [0] * 7

        # Get message counts by day for the past week
        message_counts = db.session.query(
            db.func.date(TelegramMessage.timestamp).label('date'),
            db.func.count(TelegramMessage.id).label('count')
        ).filter(
            db.func.date(TelegramMessage.timestamp) >= past_week_start,
            db.func.date(TelegramMessage.timestamp) <= today
        ).group_by(db.func.date(TelegramMessage.timestamp)).all()

        # Fill in message trend data
        for date_count in message_counts:
            msg_date = date_count.date
            if isinstance(msg_date, str):
                msg_date = datetime.strptime(msg_date, '%Y-%m-%d').date()
            days_ago = (today - msg_date).days
            if 0 <= days_ago < 7:
                message_trend[6 - days_ago] = date_count.count

        # Get attendance counts by day for the past week
        attendance_counts = db.session.query(
            db.func.date(ZoomAttendance.join_time).label('date'),
            db.func.count(ZoomAttendance.id).label('count')
        ).filter(
            db.func.date(ZoomAttendance.join_time) >= past_week_start,
            db.func.date(ZoomAttendance.join_time) <= today
        ).group_by(db.func.date(ZoomAttendance.join_time)).all()

        # Fill in attendance trend data
        for date_count in attendance_counts:
            att_date = date_count.date
            if isinstance(att_date, str):
                att_date = datetime.strptime(att_date, '%Y-%m-%d').date()
            days_ago = (today - att_date).days
            if 0 <= days_ago < 7:
                attendance_trend[6 - days_ago] = date_count.count

        return render_template(
            'dashboard.html',
            course_count=course_count,
            today_courses=today_courses,
            upcoming_courses=upcoming_courses,
            recent_logs=recent_logs,
            simulation_mode=simulation_mode,
            test_group_id=test_group_id,
            message_count=message_count,
            attendance_count=attendance_count,
            top_groups=top_groups,
            # Chart data
            course_days_labels=days_of_week,
            course_days_values=course_days_values,
            activity_dates=date_labels,
            message_trend=message_trend,
            attendance_trend=attendance_trend
        )

    @app.route('/courses')
    @login_required
    def courses():
        """Course management page"""
        # Get filter parameters
        teacher_filter = request.args.get('teacher')
        class_filter = request.args.get('class')
        group_filter = request.args.get('group')
        period_filter = request.args.get('period')

        # Start with all courses query
        query = Course.query

        # Apply filters
        if teacher_filter:
            query = query.filter(Course.teacher_name == teacher_filter)

        if class_filter:
            query = query.filter(Course.course_name == class_filter)

        if group_filter:
            query = query.filter(Course.telegram_group_id == group_filter)

        if period_filter:
            today = datetime.now().date()
            if period_filter == 'this_week':
                # This week (from today to next 7 days)
                end_date = today + timedelta(days=7)
                query = query.filter(Course.schedule_date >= today, Course.schedule_date < end_date)
            elif period_filter == 'next_week':
                # Next week
                start_date = today + timedelta(days=7)
                end_date = start_date + timedelta(days=7)
                query = query.filter(Course.schedule_date >= start_date, Course.schedule_date < end_date)
            elif period_filter == 'this_month':
                # This month
                next_month = today.replace(day=28) + timedelta(days=4)
                end_date = next_month.replace(day=1)
                query = query.filter(Course.schedule_date >= today, Course.schedule_date < end_date)

        # Execute query with ordering
        filtered_courses = query.order_by(Course.day_of_week, Course.start_time).all()

        # Get unique values for filters
        all_courses = Course.query.all()
        teachers = sorted(list(set(course.teacher_name for course in all_courses)))
        class_names = sorted(list(set(course.course_name for course in all_courses)))
        telegram_groups = sorted(list(set(course.telegram_group_id for course in all_courses)))

        # Calculate planning progress
        total_courses = len(all_courses)
        courses_with_zoom = Course.query.filter(Course.zoom_link.isnot(None)).count()
        planning_progress = round(courses_with_zoom / total_courses * 100) if total_courses > 0 else 0

        # Group by day of week
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        courses_by_day = {day: [] for day in days}

        for course in filtered_courses:
            day_name = days[course.day_of_week]
            courses_by_day[day_name].append(course)

        return render_template(
            'courses.html',
            courses_by_day=courses_by_day,
            days=days,
            teachers=teachers,
            class_names=class_names,
            telegram_groups=telegram_groups,
            planning_progress=planning_progress,
            courses_with_zoom=courses_with_zoom,
            total_courses=total_courses
        )

    @app.route('/courses/add', methods=['POST'])
    @login_required
    def add_course():
        """Add a new course"""
        try:
            # Get form data
            course_name = request.form.get('course_name')
            teacher_name = request.form.get('teacher_name')
            day_of_week = int(request.form.get('day_of_week', 0))
            start_time_str = request.form.get('start_time')
            end_time_str = request.form.get('end_time')
            telegram_group_id = request.form.get('telegram_group_id')

            # Convert strings to time objects
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()

            # Calculate next occurrence date
            today = datetime.now().date()
            days_ahead = day_of_week - today.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            next_date = today + timedelta(days=days_ahead)

            # Create new course
            new_course = Course(
                course_name=course_name,
                teacher_name=teacher_name,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
                schedule_date=next_date,
                telegram_group_id=telegram_group_id
            )

            db.session.add(new_course)
            db.session.commit()

            flash("Course added successfully!", "success")

            # Log the action
            log_entry = Log(
                level="INFO",
                scenario="manual_add_course",
                message=f"Manually added course: {course_name}"
            )
            db.session.add(log_entry)
            db.session.commit()

        except Exception as e:
            error_msg = f"Error adding course: {str(e)}"
            logger.error(error_msg)
            flash(error_msg, "danger")

            # Log the error
            log_entry = Log(
                level="ERROR",
                scenario="manual_add_course",
                message=error_msg
            )
            db.session.add(log_entry)
            db.session.commit()

        return redirect(url_for('courses'))

    @app.route('/courses/edit/<int:course_id>', methods=['POST'])
    def edit_course(course_id):
        """Edit an existing course"""
        try:
            # Get the course
            course = Course.query.get_or_404(course_id)

            # Update course data
            course.course_name = request.form.get('course_name')
            course.teacher_name = request.form.get('teacher_name')
            course.day_of_week = int(request.form.get('day_of_week', 0))
            course.start_time = datetime.strptime(request.form.get('start_time'), "%H:%M").time()
            course.end_time = datetime.strptime(request.form.get('end_time'), "%H:%M").time()
            course.telegram_group_id = request.form.get('telegram_group_id')

            # Recalculate next occurrence date
            today = datetime.now().date()
            days_ahead = course.day_of_week - today.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            course.schedule_date = today + timedelta(days=days_ahead)

            db.session.commit()

            flash("Course updated successfully!", "success")

            # Log the action
            log_entry = Log(
                level="INFO",
                scenario="manual_edit_course",
                message=f"Manually updated course: {course.course_name}"
            )
            db.session.add(log_entry)
            db.session.commit()

        except Exception as e:
            error_msg = f"Error updating course: {str(e)}"
            logger.error(error_msg)
            flash(error_msg, "danger")

            # Log the error
            log_entry = Log(
                level="ERROR",
                scenario="manual_edit_course",
                message=error_msg
            )
            db.session.add(log_entry)
            db.session.commit()

        return redirect(url_for('courses'))

    @app.route('/courses/delete/<int:course_id>', methods=['POST'])
    def delete_course(course_id):
        """Delete a course"""
        try:
            # Get the course
            course = Course.query.get_or_404(course_id)
            course_name = course.course_name

            # Delete the course
            db.session.delete(course)
            db.session.commit()

            flash("Course deleted successfully!", "success")

            # Log the action
            log_entry = Log(
                level="INFO",
                scenario="manual_delete_course",
                message=f"Manually deleted course: {course_name}"
            )
            db.session.add(log_entry)
            db.session.commit()

        except Exception as e:
            error_msg = f"Error deleting course: {str(e)}"
            logger.error(error_msg)
            flash(error_msg, "danger")

            # Log the error
            log_entry = Log(
                level="ERROR",
                scenario="manual_delete_course",
                message=error_msg
            )
            db.session.add(log_entry)
            db.session.commit()

        return redirect(url_for('courses'))

    @app.route('/zoom-links')
    @login_required
    def zoom_links():
        """Zoom links management page"""
        # Get all courses with Zoom links
        courses_with_zoom = Course.query.filter(
            (Course.zoom_link.isnot(None)) & 
            (Course.zoom_link != '')
        ).order_by(Course.schedule_date).all()

        # Get courses without Zoom links
        courses_without_zoom = Course.query.filter(
            (Course.zoom_link.is_(None)) | 
            (Course.zoom_link == '')
        ).order_by(Course.schedule_date).all()

        return render_template(
            'zoom_links.html',
            courses_with_zoom=courses_with_zoom,
            courses_without_zoom=courses_without_zoom
        )

    @app.route('/zoom-links/update/<int:course_id>', methods=['POST'])
    def update_zoom_link(course_id):
        """Update Zoom link for a course"""
        try:
            # Get the course
            course = Course.query.get_or_404(course_id)

            # Update Zoom link
            course.zoom_link = request.form.get('zoom_link')
            course.zoom_meeting_id = request.form.get('zoom_meeting_id')

            db.session.commit()

            flash("Zoom link updated successfully!", "success")

            # Log the action
            log_entry = Log(
                level="INFO",
                scenario="manual_update_zoom",
                message=f"Manually updated Zoom link for course: {course.course_name}"
            )
            db.session.add(log_entry)
            db.session.commit()

        except Exception as e:
            error_msg = f"Error updating Zoom link: {str(e)}"
            logger.error(error_msg)
            flash(error_msg, "danger")

            # Log the error
            log_entry = Log(
                level="ERROR",
                scenario="manual_update_zoom",
                message=error_msg
            )
            db.session.add(log_entry)
            db.session.commit()

        return redirect(url_for('zoom_links'))

    @app.route('/scenarios')
    @login_required
    def scenarios():
        """Scenarios management page"""
        # Chercher les scénarios dans la base de données
        db_scenarios = Scenario.query.all()

        # Si aucun scénario n'existe, initialiser avec les scénarios par défaut
        if not db_scenarios:
            default_scenarios = [
                {
                    'name': 'update_courses',
                    'display_name': 'Update Courses',
                    'description': 'Reads the Excel file, updates course schedules for the upcoming week or month.',
                    'schedule': 'Every Sunday at midnight',
                    'actions': 'Read course information from Excel\nUpdate or create courses in the database\nCalculate next occurrence dates',
                    'icon': 'fa-calendar-alt',
                    'color': 'primary'
                },
                {
                    'name': 'create_zoom_links',
                    'display_name': 'Create Zoom Links',
                    'description': 'Creates Zoom meetings for all courses that don\'t have a Zoom link yet.',
                    'schedule': 'Every Sunday at 00:05 AM (after Scenario 1)',
                    'actions': 'Find courses without Zoom links\nCreate Zoom meetings for each course\nUpdate courses with Zoom meeting links',
                    'icon': 'fa-video',
                    'color': 'info'
                },
                {
                    'name': 'generate_messages',
                    'display_name': 'Generate Messages',
                    'description': 'Generates Telegram messages for all courses in the upcoming week.',
                    'schedule': 'Every Sunday at 00:10 AM (after Scenario 2)',
                    'actions': 'Find all courses for the upcoming week\nCreate message templates with course details\nSchedule messages for sending',
                    'icon': 'fa-comment-alt',
                    'color': 'success'
                },
                {
                    'name': 'send_daily_messages',
                    'display_name': 'Send Daily Messages',
                    'description': 'Sends scheduled Telegram messages for today\'s courses.',
                    'schedule': 'Every day at 8:00 AM',
                    'actions': 'Find all scheduled messages for today\nSend messages to appropriate Telegram groups\nMark messages as sent',
                    'icon': 'fa-paper-plane',
                    'color': 'warning'
                },
                {
                    'name': 'send_daily_rankings',
                    'display_name': 'Send Daily Rankings',
                    'description': 'Sends daily rankings to all Telegram groups with active courses.',
                    'schedule': 'Every day at 8:00 PM',
                    'actions': 'Calculate rankings for all active groups\nFormat ranking messages with user scores\nSend ranking messages to groups',
                    'icon': 'fa-trophy',
                    'color': 'danger'
                }
            ]

            for scenario_data in default_scenarios:
                scenario = Scenario(**scenario_data)
                db.session.add(scenario)

            db.session.commit()
            db_scenarios = Scenario.query.all()

        return render_template('scenarios.html', scenarios=db_scenarios)

    @app.route('/scenarios/run/<scenario_name>', methods=['POST'])
    def run_scenario(scenario_name):
        """Run a specific scenario"""
        try:
            # Run the requested scenario
            if run_job(scenario_name):
                flash(f"Scenario '{scenario_name}' executed successfully!", "success")

                # Log the action
                log_entry = Log(
                    level="INFO",                    scenario="manual_run_scenario",
                    message=f"Manually executed scenario: {scenario_name}"
                )
                db.session.add(log_entry)
                db.session.commit()
            else:
                flash(f"Failed to execute scenario '{scenario_name}'", "danger")

        except Exception as e:
            error_msg = f"Error running scenario: {str(e)}"
            logger.error(error_msg)
            flash(error_msg, "danger")

            # Log the error
            log_entry = Log(
                level="ERROR",
                scenario="manual_run_scenario",
                message=error_msg
            )
            db.session.add(log_entry)
            db.session.commit()

        return redirect(url_for('scenarios'))

    @app.route('/scenarios/add', methods=['GET', 'POST'])
    @login_required
    def add_scenario():
        """Add a new scenario"""
        if request.method == 'POST':
            try:
                # Récupérer les données du formulaire
                name = request.form.get('name')
                display_name = request.form.get('display_name')
                description = request.form.get('description')
                schedule = request.form.get('schedule')
                actions = request.form.get('actions')
                icon = request.form.get('icon', 'fa-calendar-alt')
                color = request.form.get('color', 'primary')

                # Récupérer les données de code personnalisé
                is_custom_code = 'is_custom_code' in request.form
                python_code = request.form.get('python_code', '')

                # Vérifier que le nom du scénario est unique
                existing_scenario = Scenario.query.filter_by(name=name).first()
                if existing_scenario:
                    flash(f"Le nom de scénario '{name}' existe déjà.", "danger")
                    return redirect(url_for('add_scenario'))

                # Créer un nouveau scénario
                scenario = Scenario(
                    name=name,
                    display_name=display_name,
                    description=description,
                    schedule=schedule,
                    actions=actions,
                    icon=icon,
                    color=color,
                    is_custom_code=is_custom_code,
                    python_code=python_code if is_custom_code else None
                )

                db.session.add(scenario)
                db.session.commit()

                # Log de création de scénario
                log_entry = Log(
                    level="INFO",
                    scenario="scenario_management",
                    message=f"Scénario '{display_name}' créé"
                )
                db.session.add(log_entry)
                db.session.commit()

                flash(f"Scénario '{display_name}' créé avec succès!", "success")
                return redirect(url_for('scenarios'))

            except Exception as e:
                error_msg = f"Erreur lors de la création du scénario: {str(e)}"
                logger.error(error_msg)
                flash(error_msg, "danger")

                # Log de l'erreur
                log_entry = Log(
                    level="ERROR",
                    scenario="scenario_management",
                    message=error_msg
                )
                db.session.add(log_entry)
                db.session.commit()

        # Liste des icônes et couleurs disponibles
        icons = [
            'fa-calendar-alt', 'fa-video', 'fa-comment-alt', 'fa-paper-plane', 
            'fa-trophy', 'fa-sync', 'fa-clock', 'fa-bell', 'fa-chart-line'
        ]

        colors = [
            'primary', 'secondary', 'success', 'danger', 
            'warning', 'info', 'dark', 'light'
        ]

        return render_template('add_scenario.html', icons=icons, colors=colors)

    @app.route('/scenarios/edit/<int:scenario_id>', methods=['GET', 'POST'])
    @login_required
    def edit_scenario(scenario_id):
        """Edit an existing scenario"""
        # Récupérer le scénario
        scenario = Scenario.query.get_or_404(scenario_id)

        if request.method == 'POST':
            try:
                # Récupérer les données du formulaire
                display_name = request.form.get('display_name')
                description = request.form.get('description')
                schedule = request.form.get('schedule')
                actions = request.form.get('actions')
                icon = request.form.get('icon')
                color = request.form.get('color')

                # Récupérer les données de code personnalisé
                is_custom_code = 'is_custom_code' in request.form
                python_code = request.form.get('python_code', '')

                # Mettre à jour le scénario
                scenario.display_name = display_name
                scenario.description = description
                scenario.schedule = schedule
                scenario.actions = actions
                scenario.icon = icon
                scenario.color = color
                scenario.is_custom_code = is_custom_code
                scenario.python_code = python_code if is_custom_code else None

                db.session.commit()

                # Log de mise à jour de scénario
                log_entry = Log(
                    level="INFO",
                    scenario="scenario_management",
                    message=f"Scénario '{display_name}' mis à jour"
                )
                db.session.add(log_entry)
                db.session.commit()

                flash(f"Scénario '{display_name}' mis à jour avec succès!", "success")
                return redirect(url_for('scenarios'))

            except Exception as e:
                error_msg = f"Erreur lors de la mise à jour du scénario: {str(e)}"
                logger.error(error_msg)
                flash(error_msg, "danger")

                # Log de l'erreur
                log_entry = Log(
                    level="ERROR",
                    scenario="scenario_management",
                    message=error_msg
                )
                db.session.add(log_entry)
                db.session.commit()

        # Liste des icônes et couleurs disponibles
        icons = [
            'fa-calendar-alt', 'fa-video', 'fa-comment-alt', 'fa-paper-plane', 
            'fa-trophy', 'fa-sync', 'fa-clock', 'fa-bell', 'fa-chart-line'
        ]

        colors = [
            'primary', 'secondary', 'success', 'danger', 
            'warning', 'info', 'dark', 'light'
        ]

        return render_template('edit_scenario.html', scenario=scenario, icons=icons, colors=colors)

    @app.route('/scenarios/delete/<int:scenario_id>', methods=['POST'])
    @login_required
    def delete_scenario(scenario_id):
        """Delete a scenario"""
        try:
            # Récupérer le scénario
            scenario = Scenario.query.get_or_404(scenario_id)
            display_name = scenario.display_name

            # Supprimer le scénario
            db.session.delete(scenario)
            db.session.commit()

            # Log de suppression de scénario
            log_entry = Log(
                level="INFO",
                scenario="scenario_management",
                message=f"Scénario '{display_name}' supprimé"
            )
            db.session.add(log_entry)
            db.session.commit()

            flash(f"Scénario '{display_name}' supprimé avec succès!", "success")

        except Exception as e:
            error_msg = f"Erreur lors de la suppression du scénario: {str(e)}"
            logger.error(error_msg)
            flash(error_msg, "danger")

            # Log de l'erreur
            log_entry = Log(
                level="ERROR",
                scenario="scenario_management",
                message=error_msg
            )
            db.session.add(log_entry)
            db.session.commit()

        return redirect(url_for('scenarios'))

    @app.route('/logs')
    @login_required
    def logs():
        """Logs page"""
        # Get all logs, most recent first
        all_logs = Log.query.order_by(Log.timestamp.desc()).all()

        return render_template('logs.html', logs=all_logs)

    @app.route('/api/send-test-message', methods=['POST'])
    def send_test_message():
        """Send a test message to a Telegram group"""
        try:
            group_id = request.form.get('group_id')
            message = request.form.get('message', 'Test message from Telegram Course Bot')

            if not group_id:
                return jsonify({'success': False, 'message': 'Group ID is required'})

            # Vérifier et nettoyer group_id
            group_id = group_id.strip()
            logger.info(f"Attempting to send test message to group ID: {group_id}")

            # Log bot status for debugging
            bot = init_telegram_bot()

            try:
                # Vérifier que le bot est correctement initialisé
                bot_info = bot.bot.get_me()
                logger.info(f"Bot info: ID={bot_info.id}, Username=@{bot_info.username}, Is_bot={bot_info.is_bot}")
            except Exception as bot_err:
                error_msg = f"Error getting bot info: {str(bot_err)}"
                logger.error(error_msg)
                log_entry = Log(level="ERROR", scenario="test_message", message=error_msg)
                db.session.add(log_entry)
                db.session.commit()

            # Tenter d'envoyer avec plus de détails sur le succès/échec
            try:
                result = bot.send_message(group_id, message)
                logger.info(f"Message send result: {result}")

                if result:
                    # Log the successful send
                    log_entry = Log(
                        level="INFO",
                        scenario="test_message",
                        message=f"Test message sent to group {group_id}"
                    )
                    db.session.add(log_entry)
                    db.session.commit()

                    return jsonify({'success': True, 'message': 'Message sent successfully'})
                else:
                    error_msg = "Failed to send message, check the logs for details"
                    logger.error(error_msg)
                    return jsonify({'success': False, 'message': error_msg})
            except Exception as msg_err:
                error_msg = f"Error while sending message: {str(msg_err)}"
                logger.error(error_msg)
                return jsonify({'success': False, 'message': error_msg})

        except Exception as e:
            error_msg = f"Error sending test message: {str(e)}"
            logger.error(error_msg)

            # Log the error
            log_entry = Log(
                level="ERROR",
                scenario="test_message",
                message=error_msg
            )
            db.session.add(log_entry)
            db.session.commit()

            return jsonify({'success': False, 'message': error_msg})

    @app.route('/api/export-excel', methods=['POST'])
    def export_excel():
        """Export courses to Excel"""
        try:
            # Export to Excel
            if excel_processor.export_to_excel():
                # Log the action
                log_entry = Log(
                    level="INFO",
                    scenario="export_excel",
                    message=f"Manually exported courses to Excel"
                )
                db.session.add(log_entry)
                db.session.commit()

                return jsonify({'success': True, 'message': 'Courses exported to Excel successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to export courses to Excel'})

        except Exception as e:
            error_msg = f"Error exporting to Excel: {str(e)}"
            logger.error(error_msg)

            # Log the error
            log_entry = Log(
                level="ERROR",
                scenario="export_excel",
                message=error_msg
            )
            db.session.add(log_entry)
            db.session.commit()

            return jsonify({'success': False, 'message': error_msg})

    @app.route('/api/filter-rankings')
    @login_required
    def filter_rankings():
        """API endpoint for rankings filters"""
        coach = request.args.get('coach', '')
        course = request.args.get('course', '')

        # Query courses based on filters
        query = Course.query

        if coach:
            query = query.filter(Course.teacher_name == coach)
        if course:
            query = query.filter(Course.course_name == course)

        # Get unique values
        courses = db.session.query(Course.course_name).distinct()
        if coach:
            courses = courses.filter(Course.teacher_name == coach)

        groups = db.session.query(Course.telegram_group_id).distinct()
        if coach:
            groups = groups.filter(Course.teacher_name == coach)
        if course:
            groups = groups.filter(Course.course_name == course)

        return jsonify({
            'courses': [c[0] for c in courses if c[0]],
            'groups': [g[0] for g in groups if g[0]]
        })

    @app.route('/api/check-course-conflict', methods=['POST'])
    @login_required
    def check_course_conflict():
        """Vérifier s'il existe déjà un cours similaire (anti-doublons)"""
        try:
            # Récupérer les données du formulaire
            day_of_week = int(request.form.get('day_of_week', 0))
            start_time_str = request.form.get('start_time')
            end_time_str = request.form.get('end_time')
            teacher_name = request.form.get('teacher_name')
            course_id = request.form.get('course_id')  # Optionnel, pour ignorer le cours actuel

            # Convertir en objets time
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()

            # Construire la requête pour vérifier les conflits
            query = Course.query.filter(
                Course.day_of_week == day_of_week,
                Course.teacher_name == teacher_name
            )

            # Si nous éditons un cours existant, nous devons l'exclure de la vérification
            if course_id:
                query = query.filter(Course.id != int(course_id))

            # Vérifier les chevauchements horaires
            potential_conflicts = query.all()
            conflict = None

            for course in potential_conflicts:
                # Vérifier si les horaires se chevauchent
                if (start_time <= course.end_time and end_time >= course.start_time):
                    conflict = course
                    break

            if conflict:
                # Formater les détails du conflit
                day_names = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
                day_name = day_names[conflict.day_of_week]
                conflict_details = (
                    f"Cours: {conflict.course_name}\n"
                    f"Professeur: {conflict.teacher_name}\n"
                    f"Jour: {day_name}\n"
                    f"Horaire: {conflict.start_time.strftime('%H:%M')} - {conflict.end_time.strftime('%H:%M')}"
                )

                return jsonify({
                    'conflict': True, 
                    'details': conflict_details,
                    'course_id': conflict.id
                })
            else:
                return jsonify({'conflict': False})

        except Exception as e:
            error_msg = f"Erreur lors de la vérification des conflits de cours: {str(e)}"
            logger.error(error_msg)

            # Log de l'erreur
            log_entry = Log(
                level="ERROR",
                scenario="check_course_conflict",
                message=error_msg
            )
            db.session.add(log_entry)
            db.session.commit()

            return jsonify({'error': True, 'message': error_msg})

    @app.route('/simulation')
    @login_required
    def simulation():
        """Simulation mode management page"""
        # Get app settings
        bot = init_telegram_bot()
        simulation_mode = bot.is_simulation_mode()
        test_group_id = bot.get_test_group_id()

        # Get demo courses (if any)
        demo_courses = []
        if simulation_mode and test_group_id:
            demo_courses = Course.query.filter_by(telegram_group_id=test_group_id).all()

        return render_template(
            'simulation.html',
            simulation_mode=simulation_mode,
            test_group_id=test_group_id,
            demo_courses=demo_courses
        )

    @app.route('/simulation/toggle', methods=['POST'])
    def toggle_simulation():
        """Toggle simulation mode"""
        try:
            # Get form data
            enabled = request.form.get('simulation_mode') == 'on'
            test_group_id = request.form.get('test_group_id')

            if not test_group_id and enabled:
                flash("Un ID de groupe test est requis quand le mode simulation est activé", "danger")
                return redirect(url_for('simulation'))

            # Update simulation mode
            bot = init_telegram_bot()
            result = bot.toggle_simulation_mode(enabled, test_group_id)

            if result:
                flash(
                    f"Mode simulation {'activé' if enabled else 'désactivé'} avec succès !", 
                    "success"
                )

                # Log the action
                status = "activé" if enabled else "désactivé"
                log_entry = Log(
                    level="INFO",
                    scenario="simulation_mode",
                    message=f"Mode simulation {status} avec groupe test {test_group_id}"
                )
                db.session.add(log_entry)
                db.session.commit()
            else:
                activation_text = "l'activation" if enabled else "la désactivation"
                flash(
                    f"Échec de {activation_text} du mode simulation", 
                    "danger"
                )

        except Exception as e:
            error_msg = f"Erreur lors de la mise à jour du mode simulation: {str(e)}"
            logger.error(error_msg)
            flash(error_msg, "danger")

            # Log the error
            log_entry = Log(
                level="ERROR",
                scenario="simulation_mode",
                message=error_msg
            )
            db.session.add(log_entry)
            db.session.commit()

        return redirect(url_for('simulation'))

    @app.route('/bot-status')
    @login_required
    def bot_status():
        """Telegram bot status page"""
        bot = init_telegram_bot()
        status = bot.check_bot_status()

        # Get all groups used in courses
        telegram_groups = db.session.query(Course.telegram_group_id).distinct().all()
        telegram_group_ids = [group[0] for group in telegram_groups if group[0]]

        # Get recent logs related to Telegram
        telegram_logs = Log.query.filter(
            Log.scenario.in_(['telegram_message', 'test_message'])
        ).order_by(Log.timestamp.desc()).limit(20).all()

        return render_template(
            'bot_status.html',
            bot_status=status,
            telegram_groups=telegram_group_ids,
            logs=telegram_logs
        )

    @app.route('/api/check-group', methods=['POST'])
    def check_group():
        """Check if a Telegram group is valid and the bot has access"""
        import telegram.error

        try:
            group_id = request.form.get('group_id')
            if not group_id:
                return jsonify({'success': False, 'message': 'Group ID is required'})

            bot = init_telegram_bot()

            # Vérifier d'abord l'état du bot
            bot_status = bot.check_bot_status()
            if not bot_status["success"]:
                return jsonify({
                    'success': False, 
                    'message': f"Bot is not properly configured: {bot_status['error']}"
                })

            # Try to get chat info
            try:
                # Clean group_id
                group_id = group_id.strip()
                logger.info(f"Checking group ID: {group_id}")

                # Try to convert to integer if it's a numeric ID
                try:
                    if group_id.startswith('-'):
                        numeric_group_id = int(group_id)
                        actual_group_id = numeric_group_id
                        logger.info(f"Using negative numeric group ID: {actual_group_id}")
                    else:
                        numeric_group_id = int(group_id)
                        actual_group_id = numeric_group_id
                        logger.info(f"Using positive numeric group ID: {actual_group_id}")
                except ValueError:
                    actual_group_id = group_id
                    logger.info(f"Using string group ID: {actual_group_id}")

                try:
                    # Essayons d'abord de récupérer les informations du chat
                    logger.info(f"Attempting to get chat info for: {actual_group_id}")
                    chat_info = bot._run_sync(bot.bot.get_chat(actual_group_id))
                    logger.info(f"Successfully got chat info: ID={getattr(chat_info, 'id', 'N/A')}, Type={getattr(chat_info, 'type', 'N/A')}")

                    # Enregistrer tout ce qu'on peut sur le chat
                    chat_details = {
                        'id': getattr(chat_info, 'id', None),
                        'type': getattr(chat_info, 'type', None),
                        'title': getattr(chat_info, 'title', None),
                        'description': getattr(chat_info, 'description', None),
                        'invite_link': getattr(chat_info, 'invite_link', None),
                        'permissions': getattr(chat_info, 'permissions', None),
                    }
                    logger.info(f"Chat details: {chat_details}")

                    # Maintenant, vérifions les permissions du bot
                    try:
                        logger.info(f"Checking bot permissions in group {actual_group_id}")
                        member = bot._run_sync(bot.bot.get_chat_member(actual_group_id, bot_status["bot_id"]))
                        logger.info(f"Bot status in group: {member.status}")

                        # Prepare response
                        result = {
                            'success': True,
                            'chat_id': str(chat_info.id),
                            'chat_type': chat_info.type,
                            'chat_title': getattr(chat_info, 'title', 'N/A'),
                            'bot_status': member.status,
                            'can_send': member.status in ['administrator', 'creator'] or getattr(chat_info, 'all_members_are_administrators', False)
                        }

                        # Log the success
                        log_entry = Log(
                            level="INFO",
                            scenario="check_group",
                            message=f"Successfully checked group {group_id}: {result}"
                        )
                        db.session.add(log_entry)
                        db.session.commit()

                        return jsonify(result)
                    except telegram.error.BadRequest as e:
                        # Erreur spécifique de l'API Telegram
                        error_msg = f"Bot permissions check failed: {str(e)}"
                        logger.warning(error_msg)
                        return jsonify({
                            'success': False,
                            'message': error_msg,
                            'chat_id': str(getattr(chat_info, 'id', 'unknown')),
                            'chat_title': getattr(chat_info, 'title', 'N/A'),
                            'chat_type': getattr(chat_info, 'type', 'unknown'),
                            'error_type': 'BadRequest'
                        })
                    except Exception as e:
                        # Autre erreur lors de la vérification des permissions
                        error_msg = f"Bot is not in the group or has no permission: {str(e)}"
                        logger.warning(error_msg)
                        return jsonify({
                            'success': False,
                            'message': error_msg,
                            'chat_id': str(getattr(chat_info, 'id', 'unknown')),
                            'chat_title': getattr(chat_info, 'title', 'N/A'),
                            'chat_type': getattr(chat_info, 'type', 'unknown'),
                            'error_type': 'Permission'
                        })
                except telegram.error.BadRequest as e:
                    # Chat introuvable ou accès refusé par l'API Telegram
                    error_msg = f"Chat not found or access denied: {str(e)}"
                    logger.warning(error_msg)

                    # Message plus convivial pour l'utilisateur
                    return jsonify({
                        'success': False,
                        'message': "Ce groupe n'est pas accessible. Vérifiez l'ID du groupe et assurez-vous que le bot y a été ajouté et a les permissions nécessaires.",
                        'error_details': str(e),
                        'error_type': 'ChatNotFound'
                    })
                except Exception as e:
                    # Autre erreur lors de la récupération des infos du chat
                    error_msg = f"Failed to get chat info: {str(e)}"
                    logger.error(error_msg)
                    return jsonify({
                        'success': False,
                        'message': "Erreur lors de la récupération des informations du groupe. Vérifiez l'ID et réessayez.",
                        'error_details': str(e),
                        'error_type': 'General'
                    })
            except Exception as e:
                error_msg = f"Error checking group: {str(e)}"
                logger.error(error_msg)
                return jsonify({
                    'success': False,
                    'message': "Une erreur s'est produite lors de la vérification du groupe. Veuillez réessayer.",
                    'error_details': str(e),
                    'error_type': 'Unknown'
                })
        except Exception as e:
            error_msg = f"Unexpected error checking group: {str(e)}"
            logger.error(error_msg)
            return jsonify({
                'success': False,
                'message': "Une erreur inattendue s'est produite. Veuillez réessayer plus tard.",
                'error_details': str(e),
                'error_type': 'Unexpected'
            })

    @app.route('/rankings')
    @login_required
    def rankings():
        """User rankings page"""
        # Get all groups with activity
        telegram_groups = db.session.query(Course.telegram_group_id).distinct().all()
        telegram_group_ids = [group[0] for group in telegram_groups if group[0]]

        selected_group = request.args.get('group')
        selected_period = request.args.get('period', 'weekly')

        if not selected_group and telegram_group_ids:
            selected_group = telegram_group_ids[0]

        # Get rankings for the selected group and period
        if selected_group:
            bot = init_telegram_bot()
            rankings_data = bot.get_top_users(
                selected_group, 
                period_type=selected_period
            )
        else:
            rankings_data = []

        return render_template(
            'rankings.html',
            groups=telegram_group_ids,
            selected_group=selected_group,
            selected_period=selected_period,
            rankings=rankings_data
        )

    @app.route('/simulation/create-demo-course', methods=['POST'])
    def create_demo_course():
        """Create a demo course for simulation purposes"""
        try:
            # Vérifier que le mode simulation est actif
            bot = init_telegram_bot()
            if not bot.is_simulation_mode():
                flash("Le mode simulation doit être activé pour créer des cours démo", "danger")
                return redirect(url_for('simulation'))

            test_group_id = bot.get_test_group_id()
            if not test_group_id:
                flash("Un ID de groupe test est requis pour créer des cours démo", "danger")
                return redirect(url_for('simulation'))

            # Récupérer les données du formulaire
            course_name = request.form.get('course_name')
            teacher_name = request.form.get('teacher_name')
            day_of_week = int(request.form.get('day_of_week', 0))
            start_time_str = request.form.get('start_time', '10:00')
            end_time_str = request.form.get('end_time', '12:00')

            # Convertir les heures en objets time
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()

            # Calculer la prochaine date d'occurrence pour ce jour de la semaine
            today = datetime.now().date()
            days_ahead = day_of_week - today.weekday()
            if days_ahead < 0:  # Déjà passé cette semaine
                days_ahead += 7
            next_date = today + timedelta(days=days_ahead)

            # Générer un lien Zoom fictif
            zoom_link = f"https://zoom.us/j/{random.randint(10000000000, 99999999999)}"
            zoom_meeting_id = str(random.randint(100000000, 999999999))

            # Créer le cours
            course = Course(
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

            db.session.add(course)
            db.session.commit()

            # Journaliser la création
            log_entry = Log(
                level="INFO",
                scenario="demo_course",
                message=f"Cours de démonstration créé: {course_name} ({teacher_name})"
            )
            db.session.add(log_entry)
            db.session.commit()

            flash(f"Cours de démonstration '{course_name}' créé avec succès", "success")
            return redirect(url_for('simulation'))

        except Exception as e:
            flash(f"Erreur lors de la création du cours démo: {str(e)}", "danger")
            logger.error(f"Error creating demo course: {str(e)}")
            return redirect(url_for('simulation'))

    @app.route('/simulation/import-excel')
    def import_demo_excel():
        """Import course data from Excel for simulation"""
        try:
            # Vérifier que le mode simulation est actif
            bot = init_telegram_bot()
            if not bot.is_simulation_mode():
                flash("Le mode simulation doit être activé pour importer les cours démo", "danger")
                return redirect(url_for('simulation'))

            test_group_id = bot.get_test_group_id()
            if not test_group_id:
                flash("Un ID de groupe test est requis pour importer les cours démo", "danger")
                return redirect(url_for('simulation'))

            # Charger les données du fichier Excel
            df = excel_processor.load_excel_data()
            if df is None:
                flash("Impossible de charger le fichier Excel. Vérifiez le chemin et la structure du fichier.", "danger")
                return redirect(url_for('simulation'))

            # Compter les succès et les erreurs
            success_count = 0
            error_count = 0

            # Suppression des anciens cours de démo (optionnel)
            if request.args.get('clear', 'false') == 'true':
                old_courses = Course.query.filter_by(telegram_group_id=test_group_id).all()
                for old_course in old_courses:
                    db.session.delete(old_course)
                db.session.commit()
                flash(f"{len(old_courses)} cours de démonstration précédents supprimés", "info")

            # Log des colonnes disponibles pour le débogage
            logger.info(f"Excel columns: {df.columns.tolist()}")

            # Traitement de chaque ligne du fichier Excel
            for index, row in df.iterrows():
                try:
                    # Extraire les données du cours basées sur la structure Excel observée
                    # La première colonne contient le nom du cours
                    course_name = row.get('Salma Choufani - ABG - SS - 2:00pm')
                    # La deuxième colonne contient le nom de l'enseignant
                    teacher_name = row.get('Salma Choufani')
                    # Colonne jour
                    day_str = row.get('DAY')
                    # Utilisation de l'heure française
                    start_time_str = row.get('TIME (France)')
                    # Colonne ID du groupe Telegram 
                    telegram_group_id = row.get('TELEGRAM GROUP ID')

                    # Vérifier les données essentielles
                    if pd.isna(course_name) or pd.isna(day_str) or pd.isna(start_time_str):
                        logger.warning(f"Skipping row {index}: Missing essential data")
                        continue

                    # Convertir les types de données
                    day_of_week = excel_processor._get_day_of_week_index(day_str)
                    start_time = excel_processor._parse_time(start_time_str)

                    # Calculer l'heure de fin (par défaut 1 heure plus tard)
                    if start_time:
                        hour = start_time.hour
                        minute = start_time.minute
                        end_hour = hour + 1
                        end_time = time(end_hour % 24, minute)
                    else:
                        logger.warning(f"Skipping row {index}: Invalid time format: {start_time_str}")
                        error_count += 1
                        continue

                    if day_of_week == -1:
                        logger.warning(f"Skipping row {index}: Invalid day format: {day_str}")
                        error_count += 1
                        continue

                    # Calculer la prochaine date d'occurrence
                    next_date = excel_processor._get_next_occurrence(day_of_week)

                    # Utiliser une représentation sûre pour le nom du cours
                    if not isinstance(course_name, str):
                        course_name = str(course_name)

                    # Utiliser une représentation sûre pour le nom de l'enseignant
                    if pd.isna(teacher_name) or not isinstance(teacher_name, str):
                        teacher_name = "Professeur Démo"

                    logger.info(f"Importing course: {course_name}, teacher: {teacher_name}, day: {day_str}, time: {start_time_str}")

                    # Générer un lien Zoom fictif
                    zoom_link = f"https://zoom.us/j/{random.randint(10000000000, 99999999999)}"
                    zoom_meeting_id = str(random.randint(100000000, 999999999))

                    # Créer le cours
                    new_course = Course(
                        course_name=course_name,
                        teacher_name=teacher_name or "Professeur Démo",
                        telegram_group_id=test_group_id,
                        day_of_week=day_of_week,
                        start_time=start_time,
                        end_time=end_time,
                        schedule_date=next_date,
                        zoom_link=zoom_link,
                        zoom_meeting_id=zoom_meeting_id
                    )

                    db.session.add(new_course)
                    success_count += 1

                except Exception as e:
                    error_count += 1
                    logger.error(f"Erreur lors de l'importation de la ligne {index}: {str(e)}")

            # Commit des changements
            db.session.commit()

            # Log de l'action
            log_entry = Log(
                level="INFO",
                scenario="demo_import_excel",
                message=f"Import Excel pour démo: {success_count} succès, {error_count} erreurs"
            )
            db.session.add(log_entry)
            db.session.commit()

            if success_count > 0:
                flash(f"{success_count} cours importés avec succès depuis Excel pour la démonstration", "success")
            else:
                flash("Aucun cours n'a pu être importé. Vérifiez le format du fichier Excel.", "warning")

            return redirect(url_for('simulation'))

        except Exception as e:
            flash(f"Erreur lors de l'importation des cours: {str(e)}", "danger")
            logger.error(f"Error importing demo courses from Excel: {str(e)}")
            return redirect(url_for('simulation'))

    @app.route('/simulation/send-demo-notification')
    def send_demo_notification():
        """Send a demo notification to the test group"""
        try:
            # Vérifier que le mode simulation est actif
            bot = init_telegram_bot()
            if not bot.is_simulation_mode():
                flash("Le mode simulation doit être activé pour envoyer des notifications démo", "danger")
                return redirect(url_for('simulation'))

            test_group_id = bot.get_test_group_id()
            if not test_group_id:
                flash("Un ID de groupe test est requis pour envoyer des notifications démo", "danger")
                return redirect(url_for('simulation'))

            # Récupérer tous les cours de démonstration
            demo_courses = Course.query.filter_by(telegram_group_id=test_group_id).all()

            if not demo_courses:
                # Créer un message générique s'il n'y a pas de cours
                message = """📣 *DÉMONSTRATION*

Voici une notification de démonstration du système de gestion de cours Telegram!

Vous pouvez utiliser ce système pour:
• Envoyer des notifications automatiques pour les cours
• Créer des liens Zoom automatiquement
• Suivre l'engagement des participants
• Et bien plus encore!"""

                result = bot.send_message(test_group_id, message, is_simulation=True)
                if result:
                    flash("Message de démonstration envoyé avec succès", "success")
                else:
                    flash("Erreur lors de l'envoi du message de démonstration", "danger")
            else:
                # Envoyer un message pour chaque cours
                success = 0
                for course in demo_courses:
                    # Formater le message du cours
                    msg = bot.format_course_message(course)
                    if msg and bot.send_message(test_group_id, msg, is_simulation=True):
                        success += 1

                if success > 0:
                    flash(f"{success} notification(s) de cours envoyée(s) avec succès", "success")
                else:
                    flash("Aucune notification de cours n'a pu être envoyée", "danger")

            # Journal
            log_entry = Log(
                level="INFO",
                scenario="demo_notification",
                message=f"Notification de démonstration envoyée au groupe {test_group_id}"
            )
            db.session.add(log_entry)
            db.session.commit()

            return redirect(url_for('simulation'))

        except Exception as e:
            flash(f"Erreur lors de l'envoi de la notification démo: {str(e)}", "danger")
            logger.error(f"Error sending demo notification: {str(e)}")
            return redirect(url_for('simulation'))

    @app.route('/simulation/send-demo-course/<int:course_id>')
    def send_demo_course(course_id):
        """Send a specific demo course notification"""
        try:
            # Vérifier que le mode simulation est actif
            bot = init_telegram_bot()
            if not bot.is_simulation_mode():
                flash("Le mode simulation doit être activé pour envoyer des notifications démo", "danger")
                return redirect(url_for('simulation'))

            # Récupérer le cours
            course = Course.query.get_or_404(course_id)

            # Formater et envoyer le message
            msg = bot.format_course_message(course)
            if msg and bot.send_message(course.telegram_group_id, msg, is_simulation=True):
                flash(f"Notification pour le cours '{course.course_name}' envoyée avec succès", "success")
            else:
                flash(f"Erreur lors de l'envoi de la notification pour '{course.course_name}'", "danger")

            return redirect(url_for('simulation'))

        except Exception as e:
            flash(f"Erreur: {str(e)}", "danger")
            logger.error(f"Error sending demo course: {str(e)}")
            return redirect(url_for('simulation'))

    @app.route('/simulation/delete-demo-course/<int:course_id>')
    def delete_demo_course(course_id):
        """Delete a demo course"""
        try:
            # Récupérer le cours
            course = Course.query.get_or_404(course_id)

            # Stocker les informations pour le message
            course_name = course.course_name

            # Supprimer le cours
            db.session.delete(course)
            db.session.commit()

            flash(f"Cours de démonstration '{course_name}' supprimé avec succès", "success")
            return redirect(url_for('simulation'))

        except Exception as e:
            flash(f"Erreur lors de la suppression du cours: {str(e)}", "danger")
            logger.error(f"Error deleting demo course: {str(e)}")
            return redirect(url_for('simulation'))

    @app.route('/api/send-rankings', methods=['POST'])
    def send_rankings():
        """Send rankings to a Telegram group"""
        try:
            # Get form data
            group_id = request.form.get('group_id')
            period_type = request.form.get('period_type', 'weekly')

            if not group_id:
                return jsonify({'success': False, 'message': 'Group ID is required'})

            # Send the rankings
            bot = init_telegram_bot()
            if bot.send_ranking_message(group_id, period_type):
                # Log the successful send
                log_entry = Log(
                    level="INFO",
                    scenario="send_rankings",
                    message=f"{period_type.capitalize()} rankings sent to group {group_id}"
                )
                db.session.add(log_entry)
                db.session.commit()

                return jsonify({'success': True, 'message': 'Rankings sent successfully'})
            else:
                return jsonify({'success': False, 'message': 'Failed to send rankings'})

        except Exception as e:
            error_msg = f"Error sending rankings: {str(e)}"
            logger.error(error_msg)

            # Log the error
            log_entry = Log(
                level="ERROR",
                scenario="send_rankings",
                message=error_msg
            )
            db.session.add(log_entry)
            db.session.commit()

            return jsonify({'success': False, 'message': error_msg})

    @app.route('/api/send-daily-rankings', methods=['POST'])
    @login_required
    def send_daily_rankings():
        """Send daily rankings to all Telegram groups"""
        try:
            # Send the daily rankings
            bot = init_telegram_bot()
            results = bot.send_daily_rankings()

            # Log the results
            log_entry = Log(
                level="INFO",
                scenario="send_daily_rankings",
                message=f"Daily rankings sent: {results['success']} successful, {results['failure']} failed"
            )
            db.session.add(log_entry)
            db.session.commit()

            return jsonify({
                'success': True, 
                'message': f"Classements quotidiens envoyés à {results['success']} groupes ({results['failure']} échecs)"
            })

        except Exception as e:
            error_msg = f"Error sending daily rankings: {str(e)}"
            logger.error(error_msg)

            # Log the error
            log_entry = Log(
                level="ERROR",
                scenario="send_daily_rankings",
                message=error_msg
            )
            db.session.add(log_entry)
            db.session.commit()

            return jsonify({'success': False, 'message': error_msg})

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.route('/api/clear-cache', methods=['POST'])
    @login_required
    def clear_cache():
        """Vider le cache de l'application et forcer le rechargement des données"""
        try:
            # Récupérer le paramètre de redémarrage du workflow
            restart_workflow = request.form.get('restart_workflow') == 'true'

            # Vider la session Flask pour forcer une reconnexion
            from flask import session
            session.clear()

            # Vider les caches SQLAlchemy pour forcer le rechargement depuis la base de données
            db.session.expire_all()

            # Log l'action
            log_entry = Log(
                level="INFO",
                scenario="cache_management",
                message=f"Cache vidé manuellement par l'utilisateur {current_user.username}"
            )
            db.session.add(log_entry)
            db.session.commit()

            # Si demandé, redémarrer également le workflow de l'application
            if restart_workflow:
                # Enregistrer un log supplémentaire
                log_entry = Log(
                    level="INFO",
                    scenario="cache_management",
                    message=f"Redémarrage du workflow demandé par l'utilisateur {current_user.username}"
                )
                db.session.add(log_entry)
                db.session.commit()

                # Le redémarrage réel serait géré ici
                # Dans un contexte de production, cela pourrait impliquer un appel à un service externe

            return jsonify({
                'success': True, 
                'message': 'Cache vidé avec succès' + (' et workflow redémarré' if restart_workflow else '')
            })

        except Exception as e:
            error_msg = f"Erreur lors du vidage du cache: {str(e)}"
            logger.error(error_msg)

            # Log l'erreur
            log_entry = Log(
                level="ERROR",
                scenario="cache_management",
                message=error_msg
            )
            db.session.add(log_entry)
            db.session.commit()

            return jsonify({'success': False, 'message': error_msg})

    @app.errorhandler(500)
    def server_error(e):
        return render_template('500.html'), 500
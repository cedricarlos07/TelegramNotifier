import logging
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, jsonify, flash
from app import app, db
from models import Course, ScheduledMessage, Log, UserRanking, AppSettings, TelegramMessage, ZoomAttendance
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
    
    @app.route('/')
    @app.route('/admin')
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
            top_groups=top_groups
        )
    
    @app.route('/courses')
    def courses():
        """Course management page"""
        # Get all courses
        all_courses = Course.query.order_by(Course.day_of_week, Course.start_time).all()
        
        # Group by day of week
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        courses_by_day = {day: [] for day in days}
        
        for course in all_courses:
            day_name = days[course.day_of_week]
            courses_by_day[day_name].append(course)
        
        return render_template('courses.html', courses_by_day=courses_by_day, days=days)
    
    @app.route('/courses/add', methods=['POST'])
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
    def scenarios():
        """Scenarios management page"""
        return render_template('scenarios.html')
    
    @app.route('/scenarios/run/<scenario_name>', methods=['POST'])
    def run_scenario(scenario_name):
        """Run a specific scenario"""
        try:
            # Run the requested scenario
            if run_job(scenario_name):
                flash(f"Scenario '{scenario_name}' executed successfully!", "success")
                
                # Log the action
                log_entry = Log(
                    level="INFO",
                    scenario="manual_run_scenario",
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
    
    @app.route('/logs')
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
            
            # Send the message
            bot = init_telegram_bot()
            if bot.send_message(group_id, message):
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
                return jsonify({'success': False, 'message': 'Failed to send message'})
                
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
            
    @app.route('/simulation')
    def simulation():
        """Simulation mode management page"""
        # Get app settings
        bot = init_telegram_bot()
        simulation_mode = bot.is_simulation_mode()
        test_group_id = bot.get_test_group_id()
        
        return render_template(
            'simulation.html',
            simulation_mode=simulation_mode,
            test_group_id=test_group_id
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
                flash(
                    f"Échec de {'l\'activation' if enabled else 'la désactivation'} du mode simulation", 
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
    
    @app.route('/rankings')
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

    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('500.html'), 500

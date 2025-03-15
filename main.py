from app import app
from routes import register_routes
from scheduler import initialize_scheduler

if __name__ == "__main__":
    # Register all routes for the application
    register_routes(app)
    
    # Initialize the scheduler with all the tasks
    initialize_scheduler(app)
    
    # Run the Flask application
    app.run(host="0.0.0.0", port=5000, debug=False)

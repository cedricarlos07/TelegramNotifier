from .main import bp as main_bp
from .auth import bp as auth_bp
from .admin import bp as admin_bp
from .api import bp as api_bp

def init_app(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp) 
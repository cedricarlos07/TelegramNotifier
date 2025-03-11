from app import app, db
from models import Log

with app.app_context():
    latest_log = Log.query.order_by(Log.timestamp.desc()).first()
    print(f'Latest log: {latest_log.timestamp} - {latest_log.level} - {latest_log.message}')
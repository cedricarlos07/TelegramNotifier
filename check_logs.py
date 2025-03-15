
from app import app, db
from models import Log

def check_logs():
    with app.app_context():
        latest_log = Log.query.order_by(Log.timestamp.desc()).first()
        if latest_log:
            print(f'Latest log: {latest_log.timestamp} - {latest_log.level} - {latest_log.message}')
        else:
            print('No logs found')

if __name__ == '__main__':
    check_logs()

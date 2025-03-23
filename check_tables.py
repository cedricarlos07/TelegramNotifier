import sqlite3
import os

def check_tables():
    db_path = os.path.join('instance', 'telegram_notifier.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    print("Tables dans la base de données :")
    print("===============================")
    for table in tables:
        print(table[0])
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        print("Colonnes :")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        print()
    
    conn.close()

if __name__ == '__main__':
    check_tables() 
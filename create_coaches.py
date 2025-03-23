import sqlite3
import os
from datetime import datetime

def create_coaches_table():
    db_path = os.path.join('instance', 'telegram_notifier.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Créer la table coaches
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS coaches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(100),
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            email VARCHAR(120),
            telegram_id VARCHAR(100),
            created_at DATETIME,
            updated_at DATETIME
        )
        """)
        
        # Créer la table de liaison coach_courses
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS coach_courses (
            coach_id INTEGER,
            course_id INTEGER,
            FOREIGN KEY(coach_id) REFERENCES coaches(id),
            FOREIGN KEY(course_id) REFERENCES courses(id),
            PRIMARY KEY(coach_id, course_id)
        )
        """)
        
        print("Tables créées avec succès")
        
        # Transférer les données de students vers coaches
        cursor.execute("""
        INSERT INTO coaches (username, first_name, last_name, telegram_id, created_at)
        SELECT username, first_name, last_name, telegram_id, created_at
        FROM students
        """)
        
        # Transférer les relations cours
        cursor.execute("""
        INSERT INTO coach_courses (coach_id, course_id)
        SELECT s.id, sc.course_id
        FROM students s
        JOIN student_courses sc ON s.id = sc.student_id
        """)
        
        # Supprimer les anciennes données
        cursor.execute("DELETE FROM student_courses")
        cursor.execute("DELETE FROM students")
        
        # Valider les changements
        conn.commit()
        print("Données transférées avec succès")
        
        # Afficher la liste des coachs
        cursor.execute("""
        SELECT c.first_name, c.last_name, GROUP_CONCAT(co.name) as courses
        FROM coaches c
        LEFT JOIN coach_courses cc ON c.id = cc.coach_id
        LEFT JOIN courses co ON cc.course_id = co.id
        GROUP BY c.id
        ORDER BY c.last_name, c.first_name
        """)
        
        print("\nListe des coachs et leurs cours :")
        print("================================")
        for coach in cursor.fetchall():
            print(f"\nCoach : {coach[0]} {coach[1]}")
            if coach[2]:
                print("Cours :")
                for course in coach[2].split(','):
                    print(f"  - {course.strip()}")
        
    except Exception as e:
        print(f"Erreur : {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    create_coaches_table() 
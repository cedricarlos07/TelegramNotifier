import sqlite3
import os

def check_db():
    # Connexion directe à la base de données SQLite
    db_path = os.path.join('instance', 'telegram_notifier.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Compter les entrées
    cursor.execute("SELECT COUNT(*) FROM courses")
    courses_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM zoom_links")
    zoom_links_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM telegram_groups")
    telegram_groups_count = cursor.fetchone()[0]
    
    print(f"Statistiques de la base de données :")
    print(f"===================================")
    print(f"Nombre de cours : {courses_count}")
    print(f"Nombre de liens Zoom : {zoom_links_count}")
    print(f"Nombre de groupes Telegram : {telegram_groups_count}")
    
    print(f"\nExemple de cours :")
    print(f"================")
    cursor.execute("""
        SELECT name, code, professor, day_of_week, start_time, end_time, description 
        FROM courses 
        LIMIT 1
    """)
    course = cursor.fetchone()
    if course:
        print(f"Nom : {course[0]}")
        print(f"Code : {course[1]}")
        print(f"Professeur : {course[2]}")
        print(f"Jour : {course[3]}")
        print(f"Heure de début : {course[4]}")
        print(f"Heure de fin : {course[5]}")
        print(f"Description : {course[6]}")
        
        # Vérifier le lien Zoom associé
        cursor.execute("""
            SELECT meeting_id, url 
            FROM zoom_links 
            WHERE course_id = (SELECT id FROM courses LIMIT 1)
        """)
        zoom_link = cursor.fetchone()
        if zoom_link:
            print(f"\nLien Zoom associé :")
            print(f"Meeting ID : {zoom_link[0]}")
            print(f"URL : {zoom_link[1]}")
    
    conn.close()

if __name__ == '__main__':
    check_db() 
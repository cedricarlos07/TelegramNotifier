import sqlite3
import os

def check_students():
    db_path = os.path.join('instance', 'telegram_notifier.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Compter le nombre total d'étudiants
    cursor.execute("SELECT COUNT(*) FROM students")
    student_count = cursor.fetchone()[0]
    
    print(f"Nombre total d'étudiants : {student_count}")
    print("\nListe des étudiants :")
    print("===================")
    
    # Récupérer les étudiants avec leurs cours
    cursor.execute("""
        SELECT s.id, s.username, s.first_name, s.last_name, s.email,
               GROUP_CONCAT(c.name) as courses
        FROM students s
        LEFT JOIN student_courses sc ON s.id = sc.student_id
        LEFT JOIN courses c ON sc.course_id = c.id
        GROUP BY s.id
        ORDER BY s.last_name, s.first_name
    """)
    
    students = cursor.fetchall()
    for student in students:
        print(f"\nID : {student[0]}")
        print(f"Nom d'utilisateur : {student[1]}")
        print(f"Prénom : {student[2]}")
        print(f"Nom : {student[3]}")
        print(f"Email : {student[4]}")
        if student[5]:
            print("Cours inscrits :")
            for course in student[5].split(','):
                print(f"  - {course.strip()}")
        else:
            print("Aucun cours inscrit")
        print("-" * 50)
    
    conn.close()

if __name__ == '__main__':
    check_students() 
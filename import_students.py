import pandas as pd
import sqlite3
import os
from datetime import datetime

def import_students():
    # Connexion à la base de données
    db_path = os.path.join('instance', 'telegram_notifier.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Lecture du fichier Excel
        excel_path = 'attached_assets/Kodjo English - Classes Schedules (1).xlsx'
        df = pd.read_excel(excel_path)
        
        print("Importation des étudiants...")
        
        # Parcourir les lignes du fichier Excel
        for index, row in df.iterrows():
            # Extraire le nom de l'étudiant du topic
            topic = str(row['Topic '])
            if pd.isna(topic) or not topic.strip():
                continue
                
            # Extraire le niveau (ABG, BBG, etc.)
            level = None
            for possible_level in ['ABG', 'BBG', 'ZBG', 'IG', 'IAG']:
                if possible_level in topic:
                    level = possible_level
                    break
            
            # Extraire le nom de l'étudiant
            student_name = topic.split('-')[0].strip()
            
            # Séparer le prénom et le nom
            name_parts = student_name.split(' ')
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = ' '.join(name_parts[1:])
            else:
                first_name = student_name
                last_name = ''
            
            # Créer un nom d'utilisateur basé sur le nom
            username = f"{first_name.lower()}_{last_name.lower()}".replace(' ', '_')
            
            # Créer un telegram_id temporaire basé sur le nom
            temp_telegram_id = f"temp_{username}"
            
            # Vérifier si l'étudiant existe déjà
            cursor.execute("""
                SELECT id FROM students 
                WHERE first_name = ? AND last_name = ?
            """, (first_name, last_name))
            
            existing_student = cursor.fetchone()
            
            if not existing_student:
                # Ajouter l'étudiant
                cursor.execute("""
                    INSERT INTO students (username, first_name, last_name, telegram_id, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (username, first_name, last_name, temp_telegram_id, datetime.now()))
                
                student_id = cursor.lastrowid
                print(f"Ajout de l'étudiant : {first_name} {last_name}")
                
                # Trouver le cours correspondant
                cursor.execute("""
                    SELECT id FROM courses 
                    WHERE name LIKE ?
                """, (f"%{student_name}%",))
                
                course = cursor.fetchone()
                if course:
                    # Lier l'étudiant au cours
                    cursor.execute("""
                        INSERT INTO student_courses (student_id, course_id)
                        VALUES (?, ?)
                    """, (student_id, course[0]))
        
        # Valider les changements
        conn.commit()
        print("\nImportation terminée avec succès!")
        
    except Exception as e:
        print(f"Erreur lors de l'importation : {str(e)}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    import_students() 
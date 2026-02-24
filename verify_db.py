import os
import django
from django.db import connection

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "face_attendance.settings")
django.setup()

def verify_connection():
    try:
        # Check connection parameters
        db_settings = connection.settings_dict
        print(f"--- Database Connection Settings ---")
        print(f"ENGINE: {db_settings['ENGINE']}")
        print(f"NAME:   {db_settings['NAME']}")
        print(f"USER:   {db_settings['USER']}")
        print(f"HOST:   {db_settings['HOST']}")
        print(f"PORT:   {db_settings['PORT']}")
        # Masking password for security in logs, but verifying it matches internally
        print(f"PASSWORD: {'*' * len(db_settings['PASSWORD'])} (Length: {len(db_settings['PASSWORD'])})")
        
        # Test Connection using a cursor
        with connection.cursor() as cursor:
            cursor.execute("SELECT DATABASE();")
            current_db = cursor.fetchone()[0]
            print(f"\n[SUCCESS] Connected to database: '{current_db}'")
            
            # List Tables
            cursor.execute("SHOW TABLES;")
            tables = cursor.fetchall()
            print(f"\n--- Existing Tables in '{current_db}' ---")
            for table in tables:
                print(f"- {table[0]}")
                
            # Quick check for specific tables expected
            expected_tables = ['students', 'professors', 'attendance_records']
            found_tables = [t[0] for t in tables]
            print("\n--- Verification of Expected Tables ---")
            for t in expected_tables:
                if t in found_tables:
                    print(f"[OK] Found table: {t}")
                else:
                    print(f"[WARNING] Missing table: {t}")

    except Exception as e:
        print(f"\n[ERROR] Database connection failed!")
        print(f"Error details: {e}")

if __name__ == "__main__":
    verify_connection()

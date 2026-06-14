from django.db import connection
with connection.cursor() as cursor:
    try:
        cursor.execute("ALTER TABLE professors CHANGE matier matiere VARCHAR(100)")
        print("Renamed matier to matiere")
    except Exception as e:
        print(f"Could not rename matier: {e}")
    
    try:
        cursor.execute("ALTER TABLE professors DROP COLUMN full_name")
        print("Dropped full_name")
    except Exception as e:
        print(f"Could not drop full_name (maybe already gone): {e}")

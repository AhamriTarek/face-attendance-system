# Manual migration: align Django state with actual DB
# The DB already has 'nom' (and possibly 'prenom') columns in 'students' table.
# We need to:
#   1. Remove full_name from Django's state (it may or may not still exist in DB)
#   2. Ensure nom and prenom exist in both Django state and DB

from django.db import migrations, models


def forwards(apps, schema_editor):
    """Check actual DB columns and fix accordingly."""
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        cursor.execute("DESCRIBE students")
        columns = {row[0] for row in cursor.fetchall()}

    # Drop full_name if it still exists in DB
    if 'full_name' in columns:
        with connection.cursor() as cursor:
            cursor.execute("ALTER TABLE students DROP COLUMN full_name")

    # Add prenom if it doesn't exist in DB
    if 'prenom' not in columns:
        with connection.cursor() as cursor:
            cursor.execute("ALTER TABLE students ADD COLUMN prenom varchar(100) NOT NULL DEFAULT ''")

    # Add nom if it doesn't exist in DB (shouldn't happen, but be safe)
    if 'nom' not in columns:
        with connection.cursor() as cursor:
            cursor.execute("ALTER TABLE students ADD COLUMN nom varchar(100) NOT NULL DEFAULT ''")


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_remove_professor_full_name_alter_student_email'),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
        # These SeparateDatabaseAndState ops tell Django the model now has nom/prenom
        # without trying to alter the DB (since we already did it above)
    ]

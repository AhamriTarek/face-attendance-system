from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Aggressively resets database state for the project apps.'

    def handle(self, *args, **options):
        # Tables to drop (in order of dependency)
        tables = [
             'attendance_records',
             'warnings',
             'absence_rules',
             'attendance_sessions',
             'student_faces',
             'enrollments',
             'courses',
             'students',
             'professors',
        ]
        
        pkgs = ['accounts', 'courses', 'attendance', 'face_recognition_app']

        with connection.cursor() as cursor:
            # 1. Drop Tables
            self.stdout.write("Dropping tables...")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table};")
                self.stdout.write(f"Dropped {table}")
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

            # 2. Clear Migration History
            self.stdout.write("Clearing migration history...")
            for pkg in pkgs:
                cursor.execute("DELETE FROM django_migrations WHERE app = %s", [pkg])
                self.stdout.write(f"Cleared history for {pkg}")
        
        self.stdout.write(self.style.SUCCESS("Database reset complete. You can now run 'migrate'."))

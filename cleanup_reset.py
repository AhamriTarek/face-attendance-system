import os
import shutil
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'face_attendance.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import Professor, Student
from courses.models import Course, Enrollment
from attendance.models import AttendanceSession, AttendanceRecord, Warning as AbsenceWarning

def cleanup():
    print("Starting cleanup...")

    # 1. Clear Filesystem
    paths_to_clear = [
        'media/student_faces/',
        'known_faces/',
        'media/videos/'
    ]

    for path in paths_to_clear:
        if os.path.exists(path):
            print(f"Cleaning directory: {path}")
            for filename in os.listdir(path):
                file_path = os.path.join(path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f'Failed to delete {file_path}. Reason: {e}')
        else:
            print(f"Directory not found: {path}")

    # 2. Clear Database
    print("Cleaning database tables...")
    
    # Delete related data first (though CASCADE should handle most)
    AbsenceWarning.objects.all().delete()
    AttendanceRecord.objects.all().delete()
    AttendanceSession.objects.all().delete()
    Enrollment.objects.all().delete()
    Course.objects.all().delete()
    
    # Delete Professor and Student records
    Professor.objects.all().delete()
    Student.objects.all().delete()
    
    # Delete non-admin users
    non_admin_users = User.objects.filter(is_superuser=False)
    count = non_admin_users.count()
    non_admin_users.delete()
    print(f"Deleted {count} non-admin users.")

    print("Cleanup complete.")

if __name__ == "__main__":
    cleanup()

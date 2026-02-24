import os
import django
import shutil

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'face_attendance.settings')
django.setup()

from accounts.models import Professor, Student
from face_recognition_app.models import StudentFace
from django.conf import settings

def cleanup_data():
    print("Starting System Reset...")

    # 1. Delete Student faces and images
    print("Cleaning up Student faces and images...")
    student_faces = StudentFace.objects.all()
    count_faces = student_faces.count()
    student_faces.delete()
    print(f"Deleted {count_faces} face encoding records.")

    # Delete files in student_faces media folder
    faces_dir = os.path.join(settings.MEDIA_ROOT, 'student_faces')
    if os.path.exists(faces_dir):
        for filename in os.listdir(faces_dir):
            file_path = os.path.join(faces_dir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f'Failed to delete {file_path}. Reason: {e}')
        print(f"Cleared contents of {faces_dir}")

    # 2. Delete Students
    students = Student.objects.all()
    count_students = students.count()
    students.delete()
    print(f"Deleted {count_students} student records (and cascaded data).")

    # 3. Delete Professors
    profs = Professor.objects.all()
    count_profs = profs.count()
    profs.delete()
    print(f"Deleted {count_profs} professor records (and cascaded data).")

    print("\nSystem Reset Complete.")
    print("Admin account and system configuration preserved.")

if __name__ == "__main__":
    cleanup_data()

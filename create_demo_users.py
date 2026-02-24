import os
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "face_attendance.settings")
django.setup()

from django.contrib.auth.models import User
from accounts.models import Professor, Student
from courses.models import Course

def create_demo_users():
    print("--- Creating Demo Accounts ---")

    # 1. Admin
    try:
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@gmail.com', 'admin')
            print("[SUCCESS] Admin created: admin@gmail.com / admin")
        else:
            print("[INFO] Admin already exists (admin@gmail.com)")
    except Exception as e:
        print(f"[ERROR] Admin creation failed: {e}")

    # 2. Professor
    try:
        if not Professor.objects.filter(email='professor@gmail.com').exists():
            prof = Professor.objects.create(
                full_name='Dr. John Doe',
                email='professor@gmail.com',
                password='professor123' # In real app, hash this
            )
            print("[SUCCESS] Professor created: professor@gmail.com / professor123")
            
            # Create a demo course for this professor
            Course.objects.create(name='Computer Vision 101', filiere='Computer Science', professor=prof)
            print("[SUCCESS] Course 'Computer Vision 101' assigned to Professor")
        else:
            print("[INFO] Professor already exists (professor@gmail.com)")
    except Exception as e:
        print(f"[ERROR] Professor creation failed: {e}")

    # 3. Student
    try:
        if not Student.objects.filter(email='student@gmail.com').exists():
            Student.objects.create(
                full_name='Alice Smith',
                code_masar='M1001',
                filiere='Computer Science',
                email='student@gmail.com',
                password='student123', # In real app, hash this
                # No photo/encoding for remote demo, user must upload one via admin
            )
            print("[SUCCESS] Student created: student@gmail.com / student123")
        else:
            print("[INFO] Student already exists (student@gmail.com)")
    except Exception as e:
        print(f"[ERROR] Student creation failed: {e}")

if __name__ == "__main__":
    create_demo_users()

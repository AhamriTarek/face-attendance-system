import os
import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "face_attendance.settings")
django.setup()

from accounts.models import Professor, Student

def reset_users():
    print("--- Resetting User Database ---")

    # 1. Delete Students
    student_count = Student.objects.count()
    Student.objects.all().delete()
    print(f"[SUCCESS] Deleted {student_count} Students.")

    # 2. Delete Professors
    prof_count = Professor.objects.count()
    Professor.objects.all().delete()
    print(f"[SUCCESS] Deleted {prof_count} Professors.")

    print("\n[INFO] Admin account (managed by Django Auth User) is untouched.")
    print("[DONE] Database cleaned.")

if __name__ == "__main__":
    reset_users()

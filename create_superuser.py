import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "face_attendance.settings")
django.setup()

from django.contrib.auth.models import User

try:
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@gmail.com', 'admin')
        print("Superuser 'admin' created successfully.")
    else:
        print("Superuser 'admin' already exists.")
except Exception as e:
    print(f"Error creating superuser: {e}")

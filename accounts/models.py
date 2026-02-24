from django.db import models
from django.utils import timezone

class Professor(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255) # Hashed
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'professors'

    def __str__(self):
        return self.full_name

class Student(models.Model):
    code_masar = models.CharField(max_length=50, unique=True)
    full_name = models.CharField(max_length=100)
    filiere = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255) # Hashed
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'students'

    def __str__(self):
        return f"{self.full_name} ({self.code_masar})"

    # New Fields for Face Attendance
    photo = models.ImageField(upload_to='student_faces/', blank=True, null=True)
    face_encoding = models.TextField(blank=True, null=True, help_text="Numpy array representation of the face encoding")
    total_absence_hours = models.FloatField(default=0.0)


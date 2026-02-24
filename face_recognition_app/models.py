from django.db import models
from accounts.models import Student

class StudentFace(models.Model):
    MODEL_CHOICES = [
        ('haar', 'Haar Cascade'),
        ('hog', 'HOG'),
        ('cnn', 'CNN'),
        ('facenet', 'FaceNet'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='faces')
    image_name = models.CharField(max_length=255)
    model_used = models.CharField(max_length=50, choices=MODEL_CHOICES)
    embedding = models.BinaryField() # LONGBLOB in MySQL
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'student_faces'

    def __str__(self):
        return f"Face for {self.student.full_name} ({self.model_used})"

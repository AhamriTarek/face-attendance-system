from django.db import models
from accounts.models import Professor, Student

class Course(models.Model):
    name = models.CharField(max_length=100)
    filiere = models.CharField(max_length=100)
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)

    class Meta:
        db_table = 'courses'

    def __str__(self):
        return self.name

class Enrollment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)

    class Meta:
        db_table = 'enrollments'
        unique_together = ('course', 'student')

    def __str__(self):
        return f"{self.student.full_name} -> {self.course.name}"

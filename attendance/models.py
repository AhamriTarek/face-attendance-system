from django.db import models
from courses.models import Course
from accounts.models import Student

class AttendanceSession(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sessions')
    session_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(null=True, blank=True)
    duration = models.FloatField(help_text="Duration in hours", default=1.5)
    seance_number = models.IntegerField(null=True, blank=True, default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'attendance_sessions'

    def __str__(self):
        return f"{self.course.name} - {self.session_date}"

class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
    ]
    METHOD_CHOICES = [
        ('face', 'Face Recognition'),
        ('manual', 'Manual'),
    ]

    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='records')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'attendance_records'

    def __str__(self):
        return f"{self.student.full_name} - {self.session}"

class AbsenceRule(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='absence_rules')
    warning_threshold = models.IntegerField(default=3)
    message_template = models.TextField(help_text="Use {student_name}, {course_name}, {count} as placeholders")

    class Meta:
        db_table = 'absence_rules'

    def __str__(self):
        return f"Rule for {self.course.name}"

class Warning(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='warnings')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='warnings')
    absence_count = models.IntegerField()
    message = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'warnings'

    def __str__(self):
        return f"Warning for {self.student.full_name} in {self.course.name}"


class AbsenceLevelRule(models.Model):
    """Global absence alert thresholds (3 levels). Stored in absence_level_rules table."""
    level = models.IntegerField(unique=True)           # 1, 2, 3
    label = models.CharField(max_length=50)            # Avertissement, Sérieux, Critique
    threshold_hours = models.FloatField()              # 8.0, 16.0, 24.0
    message = models.TextField()
    color = models.CharField(max_length=20, default='yellow')  # yellow / orange / red
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'absence_level_rules'
        ordering = ['level']

    def __str__(self):
        return f"Niveau {self.level} – {self.label}"

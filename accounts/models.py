from django.db import models
from django.utils import timezone

class Professor(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255, null=True, blank=True) # Optional for Google OAuth
    role = models.CharField(max_length=50, default='professor')
    filiere = models.CharField(max_length=100)
    matiere = models.CharField(max_length=100)
    admin_account = models.ForeignKey('AdminAccount', on_delete=models.CASCADE, null=True, blank=True, related_name='professors')
    
    # Planning fields (Optional)
    nb_semaines = models.IntegerField(null=True, blank=True)
    date_debut = models.DateField(null=True, blank=True)
    date_fin = models.DateField(null=True, blank=True)
    seances_semaine = models.IntegerField(null=True, blank=True)

    # Per-seance time slots (for up to 8 seances per week)
    heure_debut_s1 = models.TimeField(null=True, blank=True)
    heure_fin_s1   = models.TimeField(null=True, blank=True)
    heure_debut_s2 = models.TimeField(null=True, blank=True)
    heure_fin_s2   = models.TimeField(null=True, blank=True)
    heure_debut_s3 = models.TimeField(null=True, blank=True)
    heure_fin_s3   = models.TimeField(null=True, blank=True)
    heure_debut_s4 = models.TimeField(null=True, blank=True)
    heure_fin_s4   = models.TimeField(null=True, blank=True)
    heure_debut_s5 = models.TimeField(null=True, blank=True)
    heure_fin_s5   = models.TimeField(null=True, blank=True)
    heure_debut_s6 = models.TimeField(null=True, blank=True)
    heure_fin_s6   = models.TimeField(null=True, blank=True)
    heure_debut_s7 = models.TimeField(null=True, blank=True)
    heure_fin_s7   = models.TimeField(null=True, blank=True)
    heure_debut_s8 = models.TimeField(null=True, blank=True)
    heure_fin_s8   = models.TimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'professors'

    def __str__(self):
        return f"{self.nom} {self.prenom}"

class Student(models.Model):
    code_masar = models.CharField(max_length=50, unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    filiere = models.CharField(max_length=100)
    email = models.EmailField(unique=True, null=True, blank=True)
    admin_account = models.ForeignKey('AdminAccount', on_delete=models.CASCADE, null=True, blank=True, related_name='students')
    password = models.CharField(max_length=255) # Hashed
    raw_password = models.CharField(max_length=255, blank=True, null=True)  # Plain text for admin display
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'students'

    def __str__(self):
        return f"{self.nom} {self.prenom} ({self.code_masar})"

    # New Fields for Face Attendance
    photo = models.ImageField(upload_to='student_faces/', blank=True, null=True)
    face_encoding = models.TextField(blank=True, null=True, help_text="Numpy array representation of the face encoding")
    total_absence_hours = models.FloatField(default=0.0)


class AdminAccount(models.Model):
    email = models.EmailField(unique=True)
    nom = models.CharField(max_length=100, null=True, blank=True)
    prenom = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'admin_accounts'

    def __str__(self):
        return self.email


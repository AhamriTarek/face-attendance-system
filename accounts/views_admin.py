from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Student, Professor
from courses.models import Course
from attendance.utils import FaceRecognizer
from django.db import IntegrityError
import json
import os

def admin_dashboard(request):
    # Stats for dashboard
    student_count = Student.objects.count()
    professor_count = Professor.objects.count()
    course_count = Course.objects.count()
    
    context = {
        'student_count': student_count,
        'professor_count': professor_count,
        'course_count': course_count,
    }
    return render(request, 'admin/dashboard.html', context)

def create_course(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        filiere = request.POST.get('filiere')
        professor_id = request.POST.get('professor_id')
        
        try:
            professor = Professor.objects.get(id=professor_id)
            Course.objects.create(name=name, filiere=filiere, professor=professor)
            messages.success(request, "Matière créée avec succès !")
            return redirect('admin_dashboard')
        except Exception as e:
            messages.error(request, f"Erreur : {e}")
            
    professors = Professor.objects.all()
    return render(request, 'admin/create_course.html', {'professors': professors})

def create_professor(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            Professor.objects.create(
                full_name=full_name,
                email=email,
                password=password # Hash in production
            )
            messages.success(request, "Professeur créé avec succès !")
            return redirect('admin_dashboard')
        except IntegrityError:
            messages.error(request, "Cet Email existe déjà !")
    
    return render(request, 'admin/create_professor.html')


def add_student(request):
    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        code_masar = request.POST.get('code_masar')
        filiere = request.POST.get('filiere')
        email = request.POST.get('email')
        password = request.POST.get('password') # In a real app, hash this!
        photo = request.FILES.get('photo')

        if not photo:
            messages.error(request, "La photo est obligatoire !")
            return redirect('add_student')

        # Create basic student to save the file first (so we have a path)
        try:
            student = Student(
                full_name=full_name,
                code_masar=code_masar,
                filiere=filiere,
                email=email,
                password=password, # Use make_password in production
                photo=photo
            )
            student.save() # This saves the photo to MEDIA_ROOT/student_faces/...

            # Now generate encoding
            image_path = student.photo.path
            encoding = FaceRecognizer.get_face_encoding(image_path)

            if encoding:
                student.face_encoding = json.dumps(encoding) # Store as JSON string
                student.save()
                messages.success(request, f"Étudiant {full_name} ajouté avec succès avec Face ID !")
            else:
                # If no face found, might want to delete the student or warn
                messages.warning(request, "Étudiant ajouté, MAIS aucun visage détecté sur la photo. Veuillez mettre à jour la photo.")
        
        except Exception as e:
            messages.error(request, f"Erreur lors de l'ajout de l'étudiant : {e}")
            return redirect('add_student')

        return redirect('admin_dashboard') # Assuming this URL exists

    return render(request, 'admin/add_student.html')

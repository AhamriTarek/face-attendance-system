from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Student, Professor
from courses.models import Course
from attendance.models import AbsenceLevelRule
from attendance.utils import FaceRecognizer
from django.db import IntegrityError
from django.contrib.auth.hashers import make_password
import json
import os
from django.http import JsonResponse
from .decorators import admin_required

@admin_required
def admin_dashboard(request):
    # Stats for dashboard
    student_count = Student.objects.count()
    professor_count = Professor.objects.count()
    filieres_count = Student.objects.values('filiere').distinct().count()
    
    context = {
        'student_count': student_count,
        'professor_count': professor_count,
        'filieres_count': filieres_count,
    }
    return render(request, 'admin/dashboard.html', context)

@admin_required
def create_course(request):
    # Get all professors with their data
    professors = Professor.objects.all()
    
    # Get all students with their data  
    students = Student.objects.all()
    
    # Get all filières from both professors and students
    prof_filieres = set(professors.values_list('filiere', flat=True))
    stud_filieres = set(students.values_list('filiere', flat=True))
    all_filieres = sorted(prof_filieres | stud_filieres)
    
    dashboard_data = []
    for filiere in all_filieres:
        if not filiere:
            continue
        
        profs_in_filiere = professors.filter(filiere=filiere)
        studs_in_filiere = students.filter(filiere=filiere)
        
        dashboard_data.append({
            'filiere': filiere,
            'professors': [
                {
                    'nom': p.nom,
                    'prenom': p.prenom,
                    'matiere': p.matiere
                }
                for p in profs_in_filiere
            ],
            'students': [
                {
                    'nom': s.nom,
                    'prenom': s.prenom,
                }
                for s in studs_in_filiere
            ],
            'total_professors': profs_in_filiere.count(),
            'total_students': studs_in_filiere.count(),
        })
    
    return render(request, 'admin/create_course.html', {
        'dashboard_data': dashboard_data,
        'filieres_list': [f for f in all_filieres if f],
    })


@admin_required
def add_student(request):
    if request.method == 'POST':
        nom = request.POST.get('nom', '').strip()
        prenom = request.POST.get('prenom', '').strip()
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
                nom=nom,
                prenom=prenom,
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
                messages.success(request, f"Étudiant {nom} {prenom} ajouté avec succès avec Face ID !")
            else:
                # If no face found, might want to delete the student or warn
                messages.warning(request, "Étudiant ajouté, MAIS aucun visage détecté sur la photo. Veuillez mettre à jour la photo.")
        
        except Exception as e:
            messages.error(request, f"Erreur lors de l'ajout de l'étudiant : {e}")
            return redirect('add_student')

        return redirect('admin_dashboard') # Assuming this URL exists

    return render(request, 'admin/add_student.html')

@admin_required
def bulk_create_professors_view(request):
    admin_id = request.session.get('admin_account_id')
    if not admin_id:
        return redirect('/accueil/')
    
    from accounts.models import AdminAccount, Professor
    try:
        admin_acc = AdminAccount.objects.get(id=admin_id)
    except:
        return redirect('/accueil/')
    
    existing_professors = Professor.objects.filter(
        admin_account=admin_acc
    ).order_by('nom')
    
    print("=== DEBUG ===")
    print("ADMIN ID:", admin_id)
    print("PROFESSORS COUNT:", existing_professors.count())
    print("=============")
    
    return render(request, 'accounts/bulk_create_professors.html', {
        'existing_professors': existing_professors,
        'seances_range': range(1, 9)
    })

@admin_required
def bulk_save_professors(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
    
    admin_id = request.session.get('admin_account_id')
    if not admin_id:
        return JsonResponse({'success': False, 'error': 'Not logged in'})
    
    from accounts.models import AdminAccount, Professor
    try:
        admin_acc = AdminAccount.objects.get(id=admin_id)
    except AdminAccount.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Admin account not found'})
    
    try:
        data = json.loads(request.body)
        professeurs = data.get('professeurs', [])
        
        created_count = 0
        errors = []
        
        for p in professeurs:
            try:
                nom    = p.get('nom', '').strip()
                prenom = p.get('prenom', '').strip()
                email  = p.get('email', '').strip()
                filiere= p.get('filiere', '').strip()
                matiere= p.get('matiere', '').strip()
                
                if not all([nom, prenom, email, filiere, matiere]):
                    continue
                
                prof, created = Professor.objects.get_or_create(
                    email=email,
                    defaults={
                        'nom':    nom,
                        'prenom': prenom,
                        'filiere':filiere,
                        'matiere':matiere,
                        'admin_account': admin_acc,
                    }
                )
                if not created:
                    # Update existing
                    prof.nom     = nom
                    prof.prenom  = prenom
                    prof.filiere = filiere
                    prof.matiere = matiere
                    prof.admin_account = admin_acc
                
                # Planning fields
                for field in ['nb_semaines','date_debut','date_fin','seances_semaine',
                              'heure_debut_s1','heure_fin_s1','heure_debut_s2','heure_fin_s2',
                              'heure_debut_s3','heure_fin_s3','heure_debut_s4','heure_fin_s4']:
                    val = p.get(field)
                    if val is not None:
                        val = str(val).strip()
                        if val:
                            setattr(prof, field, val)
                    
                prof.save()
                if created:
                    created_count += 1
                    
            except Exception as e:
                errors.append(f"{p.get('nom','')} {p.get('prenom','')}: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'created_count': created_count,
            'errors': errors
        })
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@admin_required
def get_filieres(request):
    """Retourner la liste des filières existantes"""
    filieres = list(
        Student.objects.values_list('filiere', flat=True)
        .distinct()
        .order_by('filiere')
    )
    # Filter out empty values
    filieres = [f for f in filieres if f]
    return JsonResponse({'filieres': filieres})


@admin_required
def get_students_by_filiere(request):
    """Retourner les étudiants d'une filière donnée en JSON"""
    filiere = request.GET.get('filiere', '').strip()
    if not filiere:
        return JsonResponse({'students': []})
    
    students = Student.objects.filter(filiere=filiere).order_by('nom', 'prenom')
    result = []
    for s in students:
        result.append({
            'id': s.id,
            'code_masar': s.code_masar,
            'nom': s.nom,
            'prenom': s.prenom,
            'email': s.email or '',
            'raw_password': s.raw_password or '',
            'photo_url': s.photo.url if s.photo else '',
            'created_at': s.created_at.strftime('%d/%m/%Y %H:%M') if s.created_at else '',
        })
    return JsonResponse({'students': result, 'count': len(result)})


@admin_required
def bulk_save_students(request):
    """Sauvegarder plusieurs étudiants en une fois via FormData"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)

    created = 0
    errors = []

    total_count = int(request.POST.get('total_count', 0))
    filiere = request.POST.get('filiere', '').strip()

    if not filiere:
        return JsonResponse({'success': False, 'error': 'Filière non spécifiée', 'errors': ['Filière obligatoire']}, status=400)

    for i in range(total_count):
        try:
            masar = request.POST.get(f'masar_{i}', '').strip()
            nom = request.POST.get(f'nom_{i}', '').strip()
            prenom = request.POST.get(f'prenom_{i}', '').strip()
            email = request.POST.get(f'email_{i}', '').strip().lower()
            password = request.POST.get(f'password_{i}', '')
            photo = request.FILES.get(f'photo_{i}')

            # Validation: champs obligatoires (email optionnel)
            if not all([masar, nom, prenom, password]):
                errors.append(f"Ligne {i+1}: Champs obligatoires manquants")
                continue

            if not photo:
                errors.append(f"Ligne {i+1}: Photo obligatoire (Face ID)")
                continue

            # Validation: email optionnel mais si présent doit être @usmba.ac.ma
            if email and not email.endswith('@usmba.ac.ma'):
                errors.append(f"Ligne {i+1}: Email doit être @usmba.ac.ma ou vide")
                continue

            # Validation: mot de passe minimum 6 caractères
            if len(password) < 6:
                errors.append(f"Ligne {i+1}: Mot de passe trop court (min 6 caractères)")
                continue

            # Validation: MASAR unique
            if Student.objects.filter(code_masar=masar).exists():
                errors.append(f"Ligne {i+1}: Code Masar '{masar}' existe déjà")
                continue

            # Validation: Email unique si fourni
            if email and Student.objects.filter(email=email).exists():
                errors.append(f"Ligne {i+1}: Email '{email}' existe déjà")
                continue

            # Email: si vide, mettre à None

            # Si email vide, le mettre à None
            email_value = email if email else None

            # Créer l'étudiant
            student = Student(
                code_masar=masar,
                nom=nom,
                prenom=prenom,
                filiere=filiere,
                email=email_value,
                password=make_password(password),
                raw_password=password,
                photo=photo
            )
            student.save()

            # Générer le face encoding
            try:
                image_path = student.photo.path
                encoding = FaceRecognizer.get_face_encoding(image_path)
                if encoding:
                    student.face_encoding = json.dumps(encoding)
                    student.save()
            except Exception:
                pass  # Face encoding failed but student is created

            created += 1

        except Exception as e:
            errors.append(f"Ligne {i+1}: Erreur - {str(e)}")
            continue

    if created > 0:
        return JsonResponse({
            'success': True,
            'message': f'{created} étudiant(s) créé(s) avec succès',
            'created_count': created,
            'errors': errors if errors else None
        })
    else:
        return JsonResponse({
            'success': False,
            'error': 'Aucun étudiant créé',
            'errors': errors
        }, status=400)


@admin_required
def delete_student(request, student_id):
    if request.method == 'POST':
        try:
            student = Student.objects.get(id=student_id)
            nom = f"{student.nom} {student.prenom}"
            # Delete photo file if exists
            if student.photo:
                if os.path.exists(student.photo.path):
                    os.remove(student.photo.path)
            # Django CASCADE will handle AttendanceRecord and Enrollment
            student.delete()
            return JsonResponse({'success': True, 'message': f'{nom} supprimé avec succès.'})
        except Student.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Étudiant non trouvé'}, status=404)
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


@admin_required
def delete_professor(request, professor_id):
    if request.method == 'POST':
        try:
            professor = Professor.objects.get(id=professor_id)
            nom = f"{professor.nom} {professor.prenom}"
            # Django CASCADE will handle Course and AttendanceSession
            professor.delete()
            return JsonResponse({'success': True, 'message': f'{nom} supprimé avec succès.'})
        except Professor.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Professeur non trouvé'}, status=404)
    return JsonResponse({'error': 'Méthode non autorisée'}, status=405)


# ── Gestion des règles d'absence ──────────────────────────────────────
ABSENCE_LEVEL_DEFAULTS = [
    {
        'level': 1, 'label': 'Avertissement', 'threshold_hours': 8.0, 'color': 'yellow',
        'message': '⚠️ Attention: Vos absences dépassent 8h.'
    },
    {
        'level': 2, 'label': 'Sérieux', 'threshold_hours': 16.0, 'color': 'orange',
        'message': '🔴 Sérieux: Vos absences dépassent 16h.'
    },
    {
        'level': 3, 'label': 'Critique', 'threshold_hours': 24.0, 'color': 'red',
        'message': '🚨 CRITIQUE: Exclusion possible!'
    },
]


@admin_required
def absence_rules(request):
    # Seed defaults if table is empty
    if AbsenceLevelRule.objects.count() == 0:
        for d in ABSENCE_LEVEL_DEFAULTS:
            AbsenceLevelRule.objects.create(**d)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            rules = data.get('rules', [])
            for r in rules:
                level = int(r.get('level'))
                threshold = float(r.get('threshold_hours'))
                message = r.get('message', '').strip()
                AbsenceLevelRule.objects.filter(level=level).update(
                    threshold_hours=threshold, message=message
                )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)

    rules = list(AbsenceLevelRule.objects.all())
    return render(request, 'admin/absence_rules.html', {'rules': rules})

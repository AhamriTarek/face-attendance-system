from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from .models import Professor, Student

def login_view(request):
    # Check if a user is already logged in
    if request.session.get('role'):
        role = request.session.get('role')
        if role == 'admin' and request.session.get('role') == 'admin':
            return redirect('admin_dashboard')
        elif role == 'professor' and request.session.get('professor_id'):
            return redirect('professor_dashboard')
        elif role == 'student' and request.session.get('student_id'):
            return redirect('student_dashboard')
        else:
            # Invalid/Partial session state, flush it
            request.session.flush()

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')
        
        if not role:
            messages.error(request, "Veuillez sélectionner un rôle.")
            return render(request, 'auth/login_selection.html')

        if role == 'admin':
            if email == 'admin@gmail.com':
                if password == 'admin':
                    request.session['role'] = 'admin'
                    return redirect('admin_dashboard')
                else:
                    messages.error(request, "Mot de passe Admin incorrect.")
            else:
                messages.error(request, "Email Admin introuvable.")

        elif role == 'professor':
            try:
                prof = Professor.objects.get(email=email)
                if prof.password == password:
                    request.session['role'] = 'professor'
                    request.session['professor_id'] = prof.id
                    return redirect('professor_dashboard')
                else:
                    messages.error(request, "Mot de passe Professeur incorrect.")
            except Professor.DoesNotExist:
                messages.error(request, "Email Professeur introuvable.")

        elif role == 'student':
            try:
                # Assuming email/password for student as well
                student = Student.objects.get(email=email)
                if student.password == password:
                    request.session['role'] = 'student'
                    request.session['student_id'] = student.id
                    return redirect('student_dashboard')
                else:
                     messages.error(request, "Mot de passe Étudiant incorrect.")
            except Student.DoesNotExist:
                messages.error(request, "Email Étudiant introuvable.")
    
    return render(request, 'auth/login_selection.html')

def logout_view(request):
    request.session.flush()
    return redirect('accueil')

def accueil_view(request):
    """Page d'accueil avec vidéo background 4K et formulaire de login intégré"""
    # Check if a user is already logged in
    if request.session.get('role'):
        role = request.session.get('role')
        if role == 'admin' and request.session.get('role') == 'admin':
            return redirect('admin_dashboard')
        elif role == 'professor' and request.session.get('professor_id'):
            return redirect('professor_dashboard')
        elif role == 'student' and request.session.get('student_id'):
            return redirect('student_dashboard')
        else:
            # Invalid/Partial session state, flush it
            request.session.flush()

    # Handle POST (login form)
    show_login = False
    if request.method == 'POST':
        show_login = True
        email = request.POST.get('email')
        password = request.POST.get('password') or request.POST.get('code')
        role = request.POST.get('role')
        
        if not role:
            messages.error(request, "Veuillez sélectionner un rôle.")
        elif role == 'admin':
            if email == 'admin@gmail.com':
                if password == 'admin':
                    request.session['role'] = 'admin'
                    return redirect('admin_dashboard')
                else:
                    messages.error(request, "Code Admin incorrect.")
            else:
                messages.error(request, "Email Admin introuvable.")
        elif role == 'professor':
            try:
                prof = Professor.objects.get(email=email)
                if prof.password == password:
                    request.session['role'] = 'professor'
                    request.session['professor_id'] = prof.id
                    return redirect('professor_dashboard')
                else:
                    messages.error(request, "Code Professeur incorrect.")
            except Professor.DoesNotExist:
                messages.error(request, "Email Professeur introuvable.")
        elif role == 'student':
            try:
                student = Student.objects.get(email=email)
                if student.password == password:
                    request.session['role'] = 'student'
                    request.session['student_id'] = student.id
                    return redirect('student_dashboard')
                else:
                    messages.error(request, "Code Étudiant incorrect.")
            except Student.DoesNotExist:
                messages.error(request, "Email Étudiant introuvable.")
    
    context = {
        'MEDIA_URL': settings.MEDIA_URL,
        'show_login': show_login,
    }
    return render(request, 'accueil.html', context)

def student_dashboard(request):
    student_id = request.session.get('student_id')
    if not student_id:
        return redirect('login')
    
    student = Student.objects.get(id=student_id)
    # Get recent attendance records
    recent_records = student.attendance_records.select_related('session', 'session__course').order_by('-session__session_date')[:10]
    
    return render(request, 'student/dashboard.html', {'student': student, 'recent_records': recent_records})

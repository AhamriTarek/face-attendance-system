from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.hashers import check_password
from .models import Professor, Student, AdminAccount
from .decorators import login_required_custom

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
                if check_password(password, student.password):
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
                # The form uses the 'email' input field name to pass the 'Code MASSAR' now
                student = Student.objects.get(code_masar=email)
                if check_password(password, student.password):
                    request.session['role'] = 'student'
                    request.session['student_id'] = student.id
                    return redirect('student_dashboard')
                else:
                    messages.error(request, "Mot de passe Étudiant incorrect.")
            except Student.DoesNotExist:
                messages.error(request, "Code MASSAR Étudiant introuvable.")
    
    # Capture error from query string (e.g. ?error=not_admin from Google OAuth callback)
    error_code = request.GET.get('error', '')
    error_message = ''
    if error_code == 'not_admin':
        error_message = "Votre email Google n'est pas associé à un compte administrateur."

    context = {
        'MEDIA_URL': settings.MEDIA_URL,
        'show_login': show_login,
        'error_message': error_message,
    }
    return render(request, 'accueil.html', context)

@login_required_custom
def student_dashboard(request):
    student_id = request.session.get('student_id')
    
    student = Student.objects.get(id=student_id)
    
    from attendance.models import AttendanceSession, AttendanceRecord, AbsenceLevelRule
    from courses.models import Course
    from django.db.models import Count, Q
    
    # 1. Get all PROFESSORS in this filiere to ensure all matieres appear (MATH, PC...)
    # This solves the issue where courses might not be created until a prof logs in.
    profs = Professor.objects.filter(filiere__iexact=student.filiere.strip())
    
    print(f"\n[DEBUG] STUDENT: {student.nom} {student.prenom} | FILIERE: '{student.filiere}'")
    
    # 2. Build matieres breakdown
    matieres = []
    total_absences = 0
    total_presence = 0
    
    for prof in profs:
        # Get or create the course for this prof if it doesn't exist yet
        course, _ = Course.objects.get_or_create(
            professor=prof,
            defaults={
                'name': prof.matiere,
                'filiere': prof.filiere,
            }
        )
        
        abs_count = AttendanceRecord.objects.filter(
            student=student, 
            session__course=course, 
            status='absent'
        ).count()
        
        pres_count = AttendanceRecord.objects.filter(
            student=student, 
            session__course=course, 
            status='present'
        ).count()
        
        matieres.append({
            'code': course.name,
            'absences': abs_count
        })
        total_absences += abs_count
        total_presence += pres_count
        print(f"Course {course.name}: {abs_count} absences")

    # 3. Total sessions available for this filiere
    total_seances = AttendanceSession.objects.filter(course__filiere__iexact=student.filiere.strip()).count()
    
    # 4. calculated total absence hours (1h per absence)
    total_absence_hours = total_absences * 1
    
    # 5. Absence history (records)
    records_qs = AttendanceRecord.objects.filter(student=student).select_related('session', 'session__course').order_by('-session__session_date', '-session__created_at')
    
    absence_records = []
    for r in records_qs:
        absence_records.append({
            'date': r.session.session_date.strftime('%d/%m/%Y'),
            'matiere': r.session.course.name,
            'seance': f"S{r.session.seance_number}" if r.session.seance_number else "—",
            'status': r.status
        })

    # 6. Alert system based on total_absence_hours (using the REAL hours from model or calculated)
    current_hours = student.total_absence_hours or 0.0
    alert_rule = AbsenceLevelRule.objects.filter(threshold_hours__lte=current_hours).order_by('-level').first()
    
    alert = None
    if alert_rule:
        alert = {
            'level': alert_rule.level,
            'label': alert_rule.label,
            'icon': '⚠️' if alert_rule.level < 3 else '🚫',
            'message': alert_rule.message
        }

    return render(request, 'student/dashboard.html', {
        'student':             student,
        'filiere':             student.filiere,
        'matieres':            matieres,
        'total_absences':      total_absences,
        'total_absence_hours': total_absence_hours,
        'total_presence':      total_presence,
        'total_seances':       total_seances,
        'absence_records':     absence_records,
        'alert':               alert,
    })

# --- Google OAuth Flow ---
import requests
from urllib.parse import urlencode

def google_login(request, role):
    """
    Redirects to Google's OAuth 2.0 consent screen.
    We pass the chosen role in the 'state' parameter so the callback knows how to log the user in.
    """
    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
    # Reconstruct the redirect URI dynamically
    redirect_uri = request.build_absolute_uri('/oauth/google/callback/')
    
    # We use state to securely pass the selected role (professor or student)
    state = role 

    params = {
        'response_type': 'code',
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'openid email profile',
        'state': state,
        'access_type': 'online',
        'prompt': 'select_account',
    }

    url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urlencode(params)
    return redirect(url)

def google_admin_login(request):
    """
    Initiates Google Login for Admin.
    """
    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
    redirect_uri = request.build_absolute_uri('/oauth/google/callback/')
    
    # Store that this is an admin login attempt in the session
    request.session['pending_admin_login'] = True
    
    params = {
        'client_id':     client_id,
        'redirect_uri':  redirect_uri,
        'response_type': 'code',
        'scope':         'openid email profile',
        'state':         'admin_login',
        'access_type':   'offline',
        'prompt':        'select_account',
    }
    import urllib.parse
    url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(params)
    return redirect(url)

def google_callback(request):
    """
    Handles the Google OAuth 2.0 callback, gets the token, and fetches user details.
    """
    code = request.GET.get('code')
    role = request.GET.get('state') # This should be 'professor' or 'student'
    error = request.GET.get('error')

    if error or not code:
        messages.error(request, "L'authentification Google a échoué ou a été annulée.")
        return redirect('accueil')

    client_id = getattr(settings, 'GOOGLE_CLIENT_ID', '')
    client_secret = getattr(settings, 'GOOGLE_CLIENT_SECRET', '')
    redirect_uri = request.build_absolute_uri('/oauth/google/callback/')

    # 1. Exchange code for access token
    token_url = 'https://oauth2.googleapis.com/token'
    token_data = {
        'code': code,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'grant_type': 'authorization_code'
    }

    token_req = requests.post(token_url, data=token_data)
    if not token_req.ok:
        messages.error(request, "Impossible de récupérer le jeton d'accès Google.")
        return redirect('accueil')
        
    access_token = token_req.json().get('access_token')

    # 2. Get user info from Google
    user_info_url = 'https://www.googleapis.com/oauth2/v3/userinfo'
    user_info_req = requests.get(user_info_url, headers={'Authorization': f'Bearer {access_token}'})
    
    if not user_info_req.ok:
        messages.error(request, "Impossible de récupérer les informations du profil Google.")
        return redirect('accueil')
        
    user_info = user_info_req.json()
    email = user_info.get('email', '')
    given_name = user_info.get('given_name', '')
    family_name = user_info.get('family_name', '')

    # --- NEW: Admin Login Logic (using session 'pending_admin_login') ---
    if request.session.get('pending_admin_login') or role == 'admin_login':
        # Clear the flag
        if 'pending_admin_login' in request.session:
            del request.session['pending_admin_login']
            
        from accounts.models import AdminAccount
        try:
            admin = AdminAccount.objects.get(email=email)
            if not admin.prenom: admin.prenom = given_name
            if not admin.nom:    admin.nom    = family_name
            admin.save()

            request.session['admin_account_id'] = admin.id
            request.session['admin_nom']        = admin.nom
            request.session['admin_prenom']     = admin.prenom
            request.session['role']             = 'admin'
            return redirect('/admin-dashboard/')
        except AdminAccount.DoesNotExist:
            return redirect('/accueil/?error=not_admin')

    # --- Professor / Student logic ---
    hosted_domain = user_info.get('hd', '') # Hosted domain mapping

    # 3. Domain validation
    if not email.endswith('@usmba.ac.ma') and hosted_domain != 'usmba.ac.ma':
        messages.error(request, "Utilisez votre email universitaire @usmba.ac.ma.")
        return redirect('accueil')

    # 4. Database Lookup and Session Logic based on role
    if role == 'professor':
        try:
            prof = Professor.objects.get(email=email)
            request.session['role'] = 'professor'
            request.session['professor_id'] = prof.id
            return redirect('professor_dashboard')
        except Professor.DoesNotExist:
            messages.error(request, "Aucun professeur trouvé avec cet email.")
            return redirect('accueil')

    elif role == 'student':
        try:
            student = Student.objects.get(email=email)
            request.session['role'] = 'student'
            request.session['student_id'] = student.id
            return redirect('student_dashboard')
        except Student.DoesNotExist:
            messages.error(request, "Aucun étudiant trouvé avec cet email.")
            return redirect('accueil')

    # Backwards compatibility for old 'admin' state if it ever happens
    elif role == 'admin':
        from accounts.models import AdminAccount
        try:
            admin = AdminAccount.objects.get(email=email)
            if not admin.prenom: admin.prenom = given_name
            if not admin.nom:    admin.nom    = family_name
            admin.save()
            request.session['admin_account_id'] = admin.id
            request.session['admin_nom']        = admin.nom
            request.session['admin_prenom']     = admin.prenom
            request.session['role']             = 'admin'
            return redirect('/admin-dashboard/')
        except AdminAccount.DoesNotExist:
            return redirect('/accueil/?error=not_admin')

    messages.error(request, "Rôle non valide pour l'authentification.")
    return redirect('accueil')

def demo_login_view(request):
    """Bypass Google OAuth: log visitor in as a demo admin with full admin powers."""
    demo_admin, _ = AdminAccount.objects.get_or_create(
        email='demo@faceattendance.local',
        defaults={'nom': 'Démo', 'prenom': 'Admin'}
    )
    request.session.flush()
    request.session['role']             = 'admin'
    request.session['admin_account_id'] = demo_admin.id
    request.session['admin_nom']        = demo_admin.nom or 'Démo'
    request.session['admin_prenom']     = demo_admin.prenom or 'Admin'
    return redirect('admin_dashboard')

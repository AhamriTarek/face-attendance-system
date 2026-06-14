from django.shortcuts import render, redirect, get_object_or_404
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta, date
from accounts.decorators import login_required_custom

from .models import AttendanceSession, AttendanceRecord
from accounts.models import Student, Professor
from courses.models import Course

import json
import threading

# NOTE: FaceRecognizer (cv2 / face_recognition / numpy) is imported lazily
# inside VideoCamera so this module loads on a server without those libs.
# Live-capture views are gated behind settings.FACE_RECOGNITION_ENABLED.


def _face_disabled_response(request):
    """Friendly notice shown when live face capture is off (cloud mode)."""
    return render(request, 'face_disabled.html', status=200)

# Global storage for active sessions (In production, use Redis/Cache)
active_sessions = {}

class VideoCamera(object):
    def __init__(self, professor_id, course_id=None):
        import cv2
        self.video = cv2.VideoCapture(0) # Open default camera
        self.professor_id = professor_id
        
        # Load known faces from DB for recognition
        self.known_face_encodings = []
        self.known_face_names = [] # Store IDs actually
        
        # 1. Filter students by course if provided
        print(f"[DEBUG] Initializing VideoCamera for prof {professor_id}, course {course_id}")
        students = Student.objects.all()
        if course_id:
            try:
                course = Course.objects.get(id=course_id)
                students = students.filter(filiere=course.filiere)
                print(f"[DEBUG] Filtered students by filiere '{course.filiere}'. Found {students.count()} students.")
            except Course.DoesNotExist:
                print(f"[DEBUG] Course {course_id} not found, loading all students.")
                
        loaded_count = 0
        for student in students:
            if student.face_encoding:
                try:
                    encoding = json.loads(student.face_encoding)
                    self.known_face_encodings.append(encoding)
                    self.known_face_names.append(student.id)
                    loaded_count += 1
                except Exception as e:
                    print(f"[DEBUG] Error decoding face for {student.nom}: {e}")
        print(f"[DEBUG] Successfully loaded {loaded_count} face encodings out of {students.count()} registered students in this context.")

    def __del__(self):
        self.video.release()

    def get_frame(self):
        import cv2
        from .utils import FaceRecognizer
        success, image = self.video.read()
        if not success:
            return None

        # Face Recognition
        # Using 0.55 tolerance for stricter recognition to prevent false positives.
        face_locations, face_names = FaceRecognizer.recognize_faces(image, self.known_face_encodings, self.known_face_names, tolerance=0.55)

        # Update global state
        if self.professor_id in active_sessions and active_sessions[self.professor_id]['camera_active']:
            for student_id in face_names:
                if student_id != "Unknown":
                    active_sessions[self.professor_id]['present_students'].add(student_id)

        # Draw rectangles and names
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            # Scale back up by 2 (matching the 0.5x downscale in FaceRecognizer)
            top *= 2
            right *= 2
            bottom *= 2
            left *= 2

            cv2.rectangle(image, (left, top), (right, bottom), (0, 0, 255), 2)

            display_name = "Inconnu"
            if name != "Unknown":
                try:
                     s = Student.objects.get(id=name)
                     display_name = f"{s.nom} {s.prenom}"
                except:
                    pass
            
            cv2.rectangle(image, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(image, display_name, (left + 6, bottom - 6), font, 1.0, (255, 255, 255), 1)

        ret, jpeg = cv2.imencode('.jpg', image)
        return jpeg.tobytes()

def gen(camera):
    while True:
        frame = camera.get_frame()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')
        else:
            break

@login_required_custom
def professor_dashboard(request):
    professor_id = request.session.get('professor_id')
        
    professor = Professor.objects.get(id=professor_id)
    
    # Get or create a Course object for this professor (keep backward compatibility)
    from courses.models import Course
    Course.objects.get_or_create(
        professor=professor,
        defaults={
            'name': professor.matiere,
            'filiere': professor.filiere,
        }
    )
    
    courses_raw = Course.objects.filter(professor=professor)
    courses = []
    
    from datetime import date
    today = date.today()
    
    for course in courses_raw:
        prof = course.professor
        
        has_planning = bool(
            prof.nb_semaines and
            prof.date_debut and
            prof.seances_semaine
        )
        
        course_data = {
            'id':           course.id,
            'name':         course.name,
            'filiere':      course.filiere,
            'has_planning': has_planning,
            'weeks':        [],
        }
        
        if has_planning:
            nb_semaines     = int(prof.nb_semaines)
            seances_semaine = int(prof.seances_semaine)
            date_debut      = prof.date_debut
            
            for week_num in range(1, nb_semaines + 1):
                week_start = date_debut + timedelta(weeks=week_num - 1)
                week_end   = week_start + timedelta(days=6)
                
                if today < week_start:
                    status = 'future'
                elif today > week_end:
                    status = 'past'
                else:
                    status = 'current'
                    
                from datetime import datetime as _dt
                now_time = _dt.now().time()

                seances_list = []
                for s_num in range(1, seances_semaine + 1):
                    seance = {'number': s_num}

                    if status == 'current':
                        # 1. Already recorded today?
                        already_done = AttendanceSession.objects.filter(
                            course=course,
                            session_date=today,
                            seance_number=s_num,
                        ).exists()

                        # 2. Check if PREVIOUS seance is finished (done or time expired)
                        prev_finished = True  # seance 1 has no previous
                        prev_heure_fin = None
                        if s_num > 1:
                            prev_done = AttendanceSession.objects.filter(
                                course=course,
                                session_date=today,
                                seance_number=s_num - 1
                            ).exists()
                            prev_heure_fin = getattr(prof, f'heure_fin_s{s_num - 1}', None)
                            prev_time_passed = prev_heure_fin and now_time > prev_heure_fin
                            prev_finished = prev_done or prev_time_passed

                        # 3. Get seance times from professor model
                        heure_debut = getattr(prof, f'heure_debut_s{s_num}', None)
                        heure_fin   = getattr(prof, f'heure_fin_s{s_num}', None)

                        seance['heure_debut'] = heure_debut.strftime('%H:%M') if heure_debut else ''
                        seance['heure_fin']   = heure_fin.strftime('%H:%M')   if heure_fin   else ''

                        if already_done:
                            seance['unlocked']    = False
                            seance['lock_reason'] = 'done'
                        elif not prev_finished:
                            # Previous seance not finished yet
                            seance['unlocked']    = False
                            seance['lock_reason'] = 'prev_not_done'
                            seance['prev_heure_fin'] = prev_heure_fin.strftime('%H:%M') if prev_heure_fin else ''
                        elif heure_debut and now_time < heure_debut:
                            seance['unlocked']    = False
                            seance['lock_reason'] = 'not_yet'
                        elif heure_fin and now_time > heure_fin:
                            seance['unlocked']    = False
                            seance['lock_reason'] = 'expired'
                        else:
                            seance['unlocked']    = True
                            seance['lock_reason'] = None
                    else:
                        # Past / future week — locked at week level
                        seance['unlocked']    = False
                        seance['lock_reason'] = None
                        seance['heure_debut'] = None
                        seance['heure_fin']   = None

                    seances_list.append(seance)

                course_data['weeks'].append({
                    'number':     week_num,
                    'date_debut': week_start.strftime('%d/%m/%Y'),
                    'date_fin':   week_end.strftime('%d/%m/%Y'),
                    'seances':    seances_list,
                    'status':     status,
                })
                
        courses.append(course_data)
        
    return render(request, 'professor/dashboard.html', {
        'professor_nom':    professor.nom,
        'professor_prenom': professor.prenom,
        'courses':          courses,
        'today':            today.strftime('%d/%m/%Y'),
        'today_full':       today.strftime('%A %d %B %Y'),
    })

@login_required_custom
def take_attendance(request, course_id):
    if not settings.FACE_RECOGNITION_ENABLED:
        return _face_disabled_response(request)

    professor_id = request.session.get('professor_id')

    course = Course.objects.get(id=course_id)

    # Initialize session state if not exists
    if professor_id not in active_sessions:
        active_sessions[professor_id] = {'present_students': set(), 'camera_active': False}

    week   = request.GET.get('week', 1)
    seance = request.GET.get('seance', 1)

    return render(request, 'professor/take_attendance.html', {
        'course':       course,
        'professor_id': professor_id,
        'week':         week,
        'seance':       seance,
    })

@login_required_custom
def start_camera(request):
    if not settings.FACE_RECOGNITION_ENABLED:
        return JsonResponse({'status': 'disabled', 'message': 'Live face capture is available in local mode only.'}, status=400)

    professor_id = request.session.get('professor_id')

    if professor_id in active_sessions:
        active_sessions[professor_id]['camera_active'] = True

    return JsonResponse({'status': 'started'})

@login_required_custom
def stop_camera(request):
    if not settings.FACE_RECOGNITION_ENABLED:
        return JsonResponse({'status': 'disabled', 'message': 'Live face capture is available in local mode only.'}, status=400)

    professor_id = request.session.get('professor_id')

    if professor_id in active_sessions:
        active_sessions[professor_id]['camera_active'] = False

    return JsonResponse({'status': 'stopped'})

@login_required_custom
def video_feed(request, course_id):
    if not settings.FACE_RECOGNITION_ENABLED:
        return _face_disabled_response(request)

    professor_id = request.session.get('professor_id')
    return StreamingHttpResponse(gen(VideoCamera(professor_id, course_id)),
                    content_type='multipart/x-mixed-replace; boundary=frame')

@login_required_custom
def get_present_students(request):
    professor_id = request.session.get('professor_id')
    data = []
    if professor_id in active_sessions:
        student_ids = active_sessions[professor_id]['present_students']
        students = Student.objects.filter(id__in=student_ids)
        for s in students:
            data.append({'full_name': f"{s.nom} {s.prenom}", 'time': timezone.now().strftime('%H:%M:%S')})
            
    return JsonResponse({'students': data})

@login_required_custom
def save_session(request):
    if request.method == 'POST':
        professor_id = request.session.get('professor_id')
        course_id = request.POST.get('course_id')
        
        # Get manual times
        start_time_str = request.POST.get('start_time')
        end_time_str = request.POST.get('end_time')
        
        if not start_time_str or not end_time_str:
            messages.error(request, "Veuillez entrer les heures de début et de fin.")
            return redirect('take_attendance', course_id=course_id)
            
        try:
            course = Course.objects.get(id=course_id)
            
            # Parse times
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
            
            # Calculate duration
            start_dt = datetime.combine(datetime.today(), start_time)
            end_dt = datetime.combine(datetime.today(), end_time)
            
            # Handle overnight sessions if needed (assuming same day for now)
            if end_dt < start_dt:
                 messages.error(request, "L'heure de fin doit être après l'heure de début.")
                 return redirect('take_attendance', course_id=course_id)
            
            duration_hours = (end_dt - start_dt).total_seconds() / 3600.0
            
            # Read week / seance from POST (sent by hidden inputs in the form)
            week_num   = request.POST.get('week')
            seance_num = request.POST.get('seance')

            # Create Session
            session = AttendanceSession.objects.create(
                course=course,
                session_date=timezone.now().date(),
                start_time=start_time,
                end_time=end_time,
                duration=round(duration_hours, 2),
                seance_number=int(seance_num) if seance_num else 1,
            )
            
            # Get present students from memory
            present_ids = active_sessions.get(professor_id, {}).get('present_students', set())
            
            # Get ALL students
            all_students = Student.objects.filter(filiere=course.filiere) 
            
            for student in all_students:
                status = 'absent'
                if student.id in present_ids:
                    status = 'present'
                
                # Create Record
                AttendanceRecord.objects.create(
                    session=session,
                    student=student,
                    status=status,
                    method='face' if status == 'present' else 'manual'
                )
                
                # Update Absence Hours if absent
                if status == 'absent':
                    student.total_absence_hours += session.duration
                    student.save()
            
            # Clear global state
            if professor_id in active_sessions:
                active_sessions[professor_id]['present_students'] = set()
                active_sessions[professor_id]['camera_active'] = False
                
            # Clear session storage if any
            if 'current_db_session_id' in request.session:
                del request.session['current_db_session_id']
                
            messages.success(request, f"Séance de {session.duration}h sauvegardée avec succès !")
            return redirect('professor_dashboard')
            
        except ValueError:
             messages.error(request, "Format d'heure invalide.")
             return redirect('take_attendance', course_id=course_id)
        
    return redirect('professor_dashboard')

@login_required_custom
def absence_list(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    week   = request.GET.get('week', 1)
    seance = request.GET.get('seance', 1)

    # All students in this filiere
    all_students = Student.objects.filter(
        filiere=course.filiere
    ).order_by('nom', 'prenom')

    # Find the session for this course + seance_number
    # Also filter by week using date range if date_debut is available
    professor = course.professor
    absent_ids = set()
    try:
        qs = AttendanceSession.objects.filter(
            course=course,
            seance_number=int(seance)
        )
        # Narrow to the correct week by date range if planning data exists
        if professor.date_debut and professor.nb_semaines:
            from datetime import timedelta as _td
            wstart = professor.date_debut + _td(weeks=int(week) - 1)
            wend   = wstart + _td(days=6)
            qs = qs.filter(session_date__range=[wstart, wend])

        session = qs.latest('session_date')
        absent_ids = set(
            session.records.filter(status='absent')
                           .values_list('student_id', flat=True)
        )
    except AttendanceSession.DoesNotExist:
        absent_ids = set()

    # Build students list
    students_data = []
    for s in all_students:
        students_data.append({
            'name':      f"{s.nom} {s.prenom}",
            'is_absent': s.id in absent_ids,
        })

    absent_count   = sum(1 for s in students_data if s['is_absent'])
    total_students = len(students_data)
    present_count  = total_students - absent_count

    return render(request, 'professor/absence_list.html', {
        'course':         course,
        'week':           week,
        'seance':         seance,
        'students_data':  students_data,
        'total_students': total_students,
        'absent_count':   absent_count,
        'present_count':  present_count,
    })


@login_required_custom
def absence_total(request, course_id):
    course    = get_object_or_404(Course, id=course_id)
    professor = course.professor

    nb_semaines     = int(professor.nb_semaines     or 0)
    seances_semaine = int(professor.seances_semaine or 0)
    date_debut      = professor.date_debut

    # Build weeks structure
    weeks = []
    for w in range(1, nb_semaines + 1):
        wstart = date_debut + timedelta(weeks=w - 1) if date_debut else None
        wend   = wstart + timedelta(days=6) if wstart else None
        weeks.append({'number': w, 'date_debut': wstart.strftime('%d/%m') if wstart else '?', 'date_fin': wend.strftime('%d/%m') if wend else '?', 'seances': list(range(1, seances_semaine + 1))})

    students = Student.objects.filter(
        filiere=course.filiere
    ).order_by('nom', 'prenom')

    # Build absence lookup: {week_num: {seance_num: set(student_ids)}}
    absence_lookup = {}
    sessions = AttendanceSession.objects.filter(course=course)
    for session in sessions:
        if date_debut and session.session_date:
            delta      = (session.session_date - date_debut).days
            week_num   = max(1, (delta // 7) + 1)
            seance_num = session.seance_number or 1
        else:
            week_num, seance_num = 1, 1

        absent_ids = set(
            session.records.filter(status='absent')
                           .values_list('student_id', flat=True)
        )
        absence_lookup.setdefault(week_num, {}).setdefault(seance_num, set())
        absence_lookup[week_num][seance_num].update(absent_ids)

    # Build per-student grid
    students_grid    = []
    global_absences  = 0
    for student in students:
        abs_dict = {}
        total    = 0
        for w in range(1, nb_semaines + 1):
            abs_dict[w] = {}
            for s in range(1, seances_semaine + 1):
                is_absent      = student.id in absence_lookup.get(w, {}).get(s, set())
                abs_dict[w][s] = is_absent
                if is_absent:
                    total += 1
        global_absences += total
        students_grid.append({
            'nom':            student.nom,
            'prenom':         student.prenom,
            'absences':       abs_dict,
            'total_absences': total,
        })

    # DEBUG
    print("WEEK KEYS:", weeks[0].keys() if weeks else "empty")
    print("FIRST WEEK:", weeks[0] if weeks else "empty")

    return render(request, 'absence_total.html', {
        'course':          course,
        'nb_semaines':     nb_semaines,
        'seances_semaine': seances_semaine,
        'total_seances':   nb_semaines * seances_semaine,
        'total_students':  students.count(),
        'global_absences': global_absences,
        'weeks':           weeks,
        'students_grid':   students_grid,
    })

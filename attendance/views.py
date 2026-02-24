from django.shortcuts import render, redirect
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta

from .models import AttendanceSession, AttendanceRecord
from accounts.models import Student, Professor
from courses.models import Course
from .utils import FaceRecognizer

import cv2
import numpy as np
import json
import threading

# Global storage for active sessions (In production, use Redis/Cache)
active_sessions = {}

class VideoCamera(object):
    def __init__(self, professor_id):
        self.video = cv2.VideoCapture(0) # Open default camera
        self.professor_id = professor_id
        
        # Load known faces from DB for recognition
        self.known_face_encodings = []
        self.known_face_names = [] # Store IDs actually
        
        students = Student.objects.all()
        for student in students:
            if student.face_encoding:
                try:
                    encoding = json.loads(student.face_encoding)
                    self.known_face_encodings.append(encoding)
                    self.known_face_names.append(student.id)
                except:
                    pass

    def __del__(self):
        self.video.release()

    def get_frame(self):
        success, image = self.video.read()
        if not success:
            return None
        
        # Face Recognition
        face_locations, face_names = FaceRecognizer.recognize_faces(image, self.known_face_encodings, self.known_face_names)

        # Update global state
        if self.professor_id in active_sessions and active_sessions[self.professor_id]['camera_active']:
            for student_id in face_names:
                if student_id != "Unknown":
                    active_sessions[self.professor_id]['present_students'].add(student_id)

        # Draw rectangles and names
        for (top, right, bottom, left), name in zip(face_locations, face_names):
            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            cv2.rectangle(image, (left, top), (right, bottom), (0, 0, 255), 2)

            display_name = "Inconnu"
            if name != "Unknown":
                try:
                     s = Student.objects.get(id=name)
                     display_name = s.full_name
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

def professor_dashboard(request):
    professor_id = request.session.get('professor_id')
    if not professor_id:
        return redirect('login') 
        
    professor = Professor.objects.get(id=professor_id)
    courses = Course.objects.filter(professor=professor)
    
    return render(request, 'professor/dashboard.html', {'professor': professor, 'courses': courses})

def take_attendance(request, course_id):
    professor_id = request.session.get('professor_id')
    if not professor_id:
        return redirect('login')
        
    course = Course.objects.get(id=course_id)
    
    # Initialize session state if not exists
    if professor_id not in active_sessions:
        active_sessions[professor_id] = {'present_students': set(), 'camera_active': False}
    
    return render(request, 'professor/take_attendance.html', {'course': course, 'professor_id': professor_id})

def start_camera(request):
    professor_id = request.session.get('professor_id')
    
    if professor_id in active_sessions:
        active_sessions[professor_id]['camera_active'] = True
        
    return JsonResponse({'status': 'started'})

def stop_camera(request):
    professor_id = request.session.get('professor_id')
    
    if professor_id in active_sessions:
        active_sessions[professor_id]['camera_active'] = False
        
    return JsonResponse({'status': 'stopped'})

def video_feed(request):
    professor_id = request.session.get('professor_id')
    return StreamingHttpResponse(gen(VideoCamera(professor_id)),
                    content_type='multipart/x-mixed-replace; boundary=frame')

def get_present_students(request):
    professor_id = request.session.get('professor_id')
    data = []
    if professor_id in active_sessions:
        student_ids = active_sessions[professor_id]['present_students']
        students = Student.objects.filter(id__in=student_ids)
        for s in students:
            data.append({'full_name': s.full_name, 'time': timezone.now().strftime('%H:%M:%S')})
            
    return JsonResponse({'students': data})

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
            
            # Create Session
            session = AttendanceSession.objects.create(
                course=course,
                session_date=timezone.now().date(),
                start_time=start_time,
                end_time=end_time,
                duration=round(duration_hours, 2)
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

def absence_list(request, course_id):
    professor_id = request.session.get('professor_id')
    if not professor_id:
        return redirect('login')
        
    course = Course.objects.get(id=course_id)
    total_students_filiere = Student.objects.filter(filiere=course.filiere).count()
    date_str = request.GET.get('date')

    # MODE 1: Weekly Summary (No date provided)
    if not date_str:
        today = timezone.now().date()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        sessions_weekly = AttendanceSession.objects.filter(
            course=course,
            session_date__range=[week_start, week_end]
        ).order_by('session_date', 'start_time')
        
        active_days = sorted(list(set(s.session_date for s in sessions_weekly)))
        
        if not active_days:
            return render(request, 'professor/absence_list.html', {
                'course': course,
                'mode': 'weekly_active_days',
                'active_days': [],
                'selected_date': today
            })

        students = Student.objects.filter(filiere=course.filiere).order_by('full_name')
        all_records = AttendanceRecord.objects.filter(
            session__course=course,
            session__session_date__range=[week_start, week_end]
        ).select_related('student', 'session')

        status_map = {}
        for r in all_records:
            s_id = r.student.id
            day_key = r.session.session_date
            if s_id not in status_map: status_map[s_id] = {}
            if day_key not in status_map[s_id]: status_map[s_id][day_key] = False
            if r.status == 'present': status_map[s_id][day_key] = True

        students_rows = []
        grand_total_absences = 0
        for s in students:
            row_status = []
            student_absences = 0
            for day in active_days:
                is_present = status_map.get(s.id, {}).get(day, False)
                status = "Présent" if is_present else "Absent"
                if status == "Absent": student_absences += 1
                row_status.append({'day': day.strftime('%Y-%m-%d'), 'status': status})
            
            grand_total_absences += student_absences
            students_rows.append({
                'student': s,
                'status_list': row_status,
                'total_absences': student_absences
            })

        # Weekly Absence Rate Calculation
        total_possible = total_students_filiere * len(active_days)
        weekly_absence_rate = 0
        if total_possible > 0:
            weekly_absence_rate = round((grand_total_absences / total_possible) * 100, 1)

        return render(request, 'professor/absence_list.html', {
            'course': course,
            'mode': 'weekly_active_days',
            'active_days': active_days,
            'students_rows': students_rows,
            'total_sessions': sessions_weekly.count(),
            'total_absences': grand_total_absences,
            'total_students': total_students_filiere,
            'weekly_absence_rate': weekly_absence_rate,
            'selected_date': today
        })

    # MODE 2: Daily View (Date provided)
    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        selected_date = timezone.now().date()

    sessions_qs = AttendanceSession.objects.filter(
        course=course, 
        session_date=selected_date
    ).order_by('start_time').prefetch_related('records', 'records__student')
    
    all_records_for_date = AttendanceRecord.objects.filter(
        session__course=course,
        session__session_date=selected_date
    ).select_related('student')
    
    total_absences = all_records_for_date.filter(status='absent').count()
    student_stats = {}
    for record in all_records_for_date.filter(status='absent'):
        s_id = record.student.id
        if s_id not in student_stats:
            student_stats[s_id] = {'name': record.student.full_name, 'count': 0}
        student_stats[s_id]['count'] += 1
    
    absences_par_etudiant = sorted(student_stats.values(), key=lambda x: x['count'], reverse=True)
    students_with_absences = len(student_stats)

    sessions = []
    for session in sessions_qs:
        session.start_time_str = session.start_time.strftime("%H:%M") if session.start_time else "-"
        session.end_time_str = session.end_time.strftime("%H:%M") if session.end_time else "-"
        session.absent_count = session.records.filter(status='absent').count()
        session.total_count = session.records.count()
        sessions.append(session)
    
    return render(request, 'professor/absence_list.html', {
        'course': course, 
        'sessions': sessions,
        'selected_date': selected_date,
        'total_absences': total_absences,
        'absences_par_etudiant': absences_par_etudiant[:5],
        'total_students': total_students_filiere,
        'students_with_absences': students_with_absences,
        'mode': 'daily'
    })

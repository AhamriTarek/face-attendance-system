from django.shortcuts import render, get_object_or_404
from django.http import StreamingHttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from accounts.decorators import professor_required
from attendance.models import AttendanceSession, AttendanceRecord
from attendance.services.recognizer import FaceRecognizerService

recognizer_service = FaceRecognizerService()

def gen(session_id):
    while True:
        frame = recognizer_service.get_frame(session_id)
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@professor_required
def capture_page(request, session_id):
    session = get_object_or_404(AttendanceSession, id=session_id)
    # Reload faces to ensure latest data
    recognizer_service.reload_faces()
    return render(request, 'attendance/capture.html', {'session': session})

@professor_required
def video_feed(request, session_id):
    return StreamingHttpResponse(gen(session_id),
                                 content_type='multipart/x-mixed-replace; boundary=frame')

@professor_required
def get_activity(request, session_id):
    # Return last 10 records
    records = AttendanceRecord.objects.filter(session_id=session_id).select_related('student').order_by('-updated_at')[:15]
    
    # We need updated_at field in model to track latest changes accurately for polling? 
    # Actually 'created_at' is there. For check-out updates, we might need 'updated_at' or check check_out time.
    # Let's fallback to created_at logic or just manual check
    
    data = []
    for r in records:
        status_text = "Check In"
        time_act = r.check_in
        if r.check_out:
            status_text = "Check Out"
            time_act = r.check_out
            
        data.append({
            'name': r.student.full_name,
            'time': time_act.strftime("%H:%M:%S") if time_act else "",
            'status': status_text
        })
    return JsonResponse({'activity': data})

@professor_required
@csrf_exempt
def toggle_recognition(request, session_id):
    if request.method == "POST":
        import json
        body = json.loads(request.body)
        active = body.get('active', True)
        recognizer_service.set_active(active)
        return JsonResponse({'status': 'ok', 'active': active})
    return JsonResponse({'status': 'error'}, status=400)

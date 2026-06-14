from django.shortcuts import render, get_object_or_404
from django.http import StreamingHttpResponse, JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from accounts.decorators import professor_required
from attendance.models import AttendanceSession, AttendanceRecord

# NOTE: FaceRecognizerService opens a webcam, so it is imported and
# instantiated lazily (never at module import time) and only when
# settings.FACE_RECOGNITION_ENABLED is True. This keeps the server
# bootable without a webcam or the heavy face libraries (cloud mode).

_recognizer_service = None


def _get_recognizer_service():
    """Lazily create the singleton recognizer (opens the webcam)."""
    global _recognizer_service
    if _recognizer_service is None:
        from attendance.services.recognizer import FaceRecognizerService
        _recognizer_service = FaceRecognizerService()
    return _recognizer_service


def _face_disabled_response(request):
    """Friendly notice shown when live face capture is off (cloud mode)."""
    return render(request, 'face_disabled.html', status=200)


def gen(session_id):
    service = _get_recognizer_service()
    while True:
        frame = service.get_frame(session_id)
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@professor_required
def capture_page(request, session_id):
    if not settings.FACE_RECOGNITION_ENABLED:
        return _face_disabled_response(request)
    session = get_object_or_404(AttendanceSession, id=session_id)
    # Reload faces to ensure latest data
    _get_recognizer_service().reload_faces()
    return render(request, 'attendance/capture.html', {'session': session})

@professor_required
def video_feed(request, session_id):
    if not settings.FACE_RECOGNITION_ENABLED:
        return _face_disabled_response(request)
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
    if not settings.FACE_RECOGNITION_ENABLED:
        return JsonResponse({'status': 'disabled', 'message': 'Live face capture is available in local mode only.'}, status=400)
    if request.method == "POST":
        import json
        body = json.loads(request.body)
        active = body.get('active', True)
        _get_recognizer_service().set_active(active)
        return JsonResponse({'status': 'ok', 'active': active})
    return JsonResponse({'status': 'error'}, status=400)

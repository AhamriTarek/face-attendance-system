import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'face_attendance.settings')
django.setup()

from accounts.models import Student
try:
    from attendance.models import FaceEncoding
    has_face_encoding_model = True
except ImportError:
    has_face_encoding_model = False

students = Student.objects.all()
print('Total students:', students.count())

for s in students[:5]:
    if has_face_encoding_model:
        encodings = FaceEncoding.objects.filter(student=s)
        print(f'Student: {s.nom} {s.prenom} | Encodings: {encodings.count()}')
    else:
        # What is actually stored in Student model
        has_encoding = 'Yes' if s.face_encoding else 'No'
        print(f'Student: {s.nom} {s.prenom} | Has face_encoding field: {has_encoding}')
        if s.face_encoding:
            try:
                import json
                enc = json.loads(s.face_encoding)
                print(f'  -> Encoding shape/length: {len(enc) if isinstance(enc, list) else type(enc)}')
            except Exception as e:
                print(f'  -> Error decoding JSON: {e}')

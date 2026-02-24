from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from accounts.decorators import professor_required
from accounts.models import Student
from .forms import StudentFaceForm
from .models import StudentFace
from .utils import get_face_embedding, serialize_embedding
from attendance.services.recognizer import FaceRecognizerService
import os

@professor_required
def add_face(request):
    if request.method == 'POST':
        form = StudentFaceForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                # 1. Get arguments
                student = form.cleaned_data.get('student')
                code_masar = form.cleaned_data.get('code_masar')
                
                if not student and code_masar:
                    try:
                        student = Student.objects.get(code_masar=code_masar)
                    except Student.DoesNotExist:
                        messages.error(request, f"Student with Code Massar '{code_masar}' not found.")
                        return render(request, 'face_recognition_app/add_face.html', {'form': form})
                
                model_used = form.cleaned_data['model_used']
                image_file = request.FILES['image']
                
                # 2. Save temporary file to process (or use in-memory if util supports it)
                # For simplicity, we save it to a temp path or rely on Django's temporary file storage
                # Face recognition library needs a file path or numpy array. 
                # We can load it using face_recognition.load_image_file directly from the file object.
                
                import face_recognition
                
                # Load image
                image = face_recognition.load_image_file(image_file)
                
                # Detect Face & Encode
                # Using the utility we created earlier or inline logic to support 'cnn' choice
                # The utility `get_face_embedding` takes a path, let's adapt or use inline.
                
                face_locations = face_recognition.face_locations(image, model=model_used)
                
                if not face_locations:
                    messages.error(request, "No face detected in the image. Please try another.")
                    return render(request, 'face_recognition_app/add_face.html', {'form': form})
                
                if len(face_locations) > 1:
                    messages.warning(request, "Multiple faces detected. Using the first one found.")
                    
                # Encode
                encodings = face_recognition.face_encodings(image, face_locations)
                if not encodings:
                    messages.error(request, "Could not encode face.")
                    return render(request, 'face_recognition_app/add_face.html', {'form': form})
                
                embedding = encodings[0]
                
                # 3. Save to DB
                # Note: We are NOT saving the file to disk permanently in this requirement, 
                # but the user asked to "Save the uploaded image(s) to MEDIA_ROOT".
                # Django ImageField automatically does that if we had one on the model.
                # The model `StudentFace` has `image_name` (char) and `embedding` (binary).
                # We should probably save the file manually to MEDIA_ROOT if we want to keep it.
                
                from django.conf import settings
                import uuid
                
                ext = os.path.splitext(image_file.name)[1]
                filename = f"{student.id}_{uuid.uuid4().hex[:8]}{ext}"
                save_path = os.path.join(settings.MEDIA_ROOT, 'student_faces', str(student.id))
                os.makedirs(save_path, exist_ok=True)
                
                full_path = os.path.join(save_path, filename)
                
                with open(full_path, 'wb+') as destination:
                    for chunk in image_file.chunks():
                        destination.write(chunk)
                
                # Create Record
                StudentFace.objects.create(
                    student=student,
                    image_name=filename, # Storing relative or just name
                    model_used=model_used,
                    embedding=serialize_embedding(embedding)
                )
                
                messages.success(request, f"Face registered successfully for {student.full_name}!")
                
                # 4. Reload Recognizer
                FaceRecognizerService().reload_faces()
                
                return redirect('add_face')
                
            except Exception as e:
                messages.error(request, f"Error processing image: {str(e)}")
        
    else:
        form = StudentFaceForm()

    return render(request, 'face_recognition_app/add_face.html', {'form': form})

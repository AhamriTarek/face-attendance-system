import os
from django.core.management.base import BaseCommand
from accounts.models import Student
from face_recognition_app.models import StudentFace
from face_recognition_app.utils import get_face_embedding, serialize_embedding

class Command(BaseCommand):
    help = 'Register faces from a directory. Filenames must match Student code_masar.'

    def add_arguments(self, parser):
        parser.add_argument('directory', type=str, help='Path to directory containing images')

    def handle(self, *args, **options):
        directory = options['directory']
        
        if not os.path.isdir(directory):
            self.stdout.write(self.style.ERROR(f"Directory not found: {directory}"))
            return

        count = 0
        for filename in os.listdir(directory):
            if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                continue
                
            code_masar = os.path.splitext(filename)[0] # Assumption: filename is code_masar
            
            try:
                student = Student.objects.get(code_masar=code_masar)
            except Student.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"Student with code {code_masar} not found. Skipping {filename}."))
                continue

            image_path = os.path.join(directory, filename)
            self.stdout.write(f"Processing {filename}...")
            
            embedding, error = get_face_embedding(image_path)
            
            if error:
                self.stdout.write(self.style.ERROR(f"Error processing {filename}: {error}"))
                continue
                
            # Save to DB
            StudentFace.objects.create(
                student=student,
                image_name=filename,
                model_used='hog',
                embedding=serialize_embedding(embedding)
            )
            count += 1
            self.stdout.write(self.style.SUCCESS(f"Registered face for {student.full_name}"))

        self.stdout.write(self.style.SUCCESS(f"Finished. Registered {count} faces."))

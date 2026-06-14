import json
import os
from django.core.management.base import BaseCommand
from accounts.models import Student
from attendance.utils import FaceRecognizer

class Command(BaseCommand):
    help = 'Rebuilds face encodings for all students from their stored photos.'

    def handle(self, *args, **kwargs):
        students = Student.objects.all()
        total = students.count()
        success = 0
        failed = 0
        no_photo = 0

        self.stdout.write(f'Found {total} students. Starting encoding rebuild...')

        for student in students:
            if not student.photo or not student.photo.name:
                self.stdout.write(self.style.WARNING(f'Skipped {student.nom} {student.prenom} ({student.code_masar}) - No photo found.'))
                no_photo += 1
                continue

            image_path = student.photo.path
            if not os.path.exists(image_path):
                self.stdout.write(self.style.ERROR(f'File missing for {student.nom} {student.prenom}: {image_path}'))
                failed += 1
                continue

            self.stdout.write(f'Processing {student.nom} {student.prenom}...')
            try:
                encoding = FaceRecognizer.get_face_encoding(image_path)
                if encoding:
                    student.face_encoding = json.dumps(encoding)
                    student.save()
                    success += 1
                    self.stdout.write(self.style.SUCCESS(f'Successfully updated encoding for {student.nom} {student.prenom}.'))
                else:
                    self.stdout.write(self.style.WARNING(f'No faces found in photo for {student.nom} {student.prenom}.'))
                    failed += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error processing {student.nom} {student.prenom}: {e}'))
                failed += 1

        self.stdout.write(self.style.SUCCESS(f'\nRebuild complete! Success: {success}, Failed: {failed}, No Photo: {no_photo}'))

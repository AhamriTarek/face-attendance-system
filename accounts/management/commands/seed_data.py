from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from accounts.models import Professor, Student
from courses.models import Course, Enrollment
from attendance.models import AbsenceRule

class Command(BaseCommand):
    help = 'Seed database with demo data'

    def handle(self, *args, **options):
        self.stdout.write("Seeding data...")

        # 1. Professors
        prof1, created = Professor.objects.get_or_create(
            email='teacher@test.com',
            defaults={
                'full_name': 'Dr. Smith',
                'password': make_password('123456')
            }
        )
        if created: self.stdout.write("Created Professor Dr. Smith")

        # 2. Students
        students_data = [
            {'code': 'S001', 'name': 'Tarek', 'email': 'tarek@test.com'},
            {'code': 'S002', 'name': 'Alice', 'email': 'alice@test.com'},
            {'code': 'S003', 'name': 'Bob', 'email': 'bob@test.com'},
        ]
        
        created_students = []
        for s in students_data:
            stu, c = Student.objects.get_or_create(
                code_masar=s['code'],
                defaults={
                    'full_name': s['name'],
                    'filiere': 'Computer Science',
                    'email': s['email'],
                    'password': make_password('student123')
                }
            )
            created_students.append(stu)
            if c: self.stdout.write(f"Created Student {s['name']}")

        # 3. Courses
        course1, c = Course.objects.get_or_create(
            name='Computer Vision 101',
            defaults={'filiere': 'Computer Science', 'professor': prof1}
        )
        course2, c = Course.objects.get_or_create(
            name='Web Development',
            defaults={'filiere': 'Computer Science', 'professor': prof1}
        )
        if c: self.stdout.write("Created Courses")

        # 4. Enrollments
        for stu in created_students:
            Enrollment.objects.get_or_create(course=course1, student=stu)
            Enrollment.objects.get_or_create(course=course2, student=stu)
        self.stdout.write("Enrolled students")

        # 5. Absence Rules
        AbsenceRule.objects.get_or_create(
            course=course1,
            defaults={'warning_threshold': 3, 'message_template': 'Warning: {student_name}, you have exceeded absences in {course_name}.'}
        )
        AbsenceRule.objects.get_or_create(
            course=course2,
            defaults={'warning_threshold': 2, 'message_template': 'Critical: {student_name}, please contact {course_name} instructor.'}
        )
        self.stdout.write("Created Absence Rules")

        self.stdout.write(self.style.SUCCESS("Data seeding complete."))

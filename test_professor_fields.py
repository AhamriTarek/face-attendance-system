import os
import django
import json
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'face_attendance.settings')
django.setup()

from accounts.models import Professor

def test_professor_fields():
    print("Testing Professor model with new fields...")
    email = "test.prof@usmba.ac.ma"
    
    # Clean up if exists
    Professor.objects.filter(email=email).delete()
    
    try:
        # Test creation with fields
        p = Professor.objects.create(
            nom="Test",
            prenom="Prof",
            email=email,
            filiere="SMI",
            matiere="AI",
            nb_semaines=12,
            date_debut=date(2024, 1, 1),
            date_fin=date(2024, 4, 1),
            seances_semaine=2
        )
        print(f"Successfully created professor: {p.email}")
        
        # Test retrieval
        p_retrieved = Professor.objects.get(email=email)
        assert p_retrieved.nb_semaines == 12
        assert p_retrieved.date_debut == date(2024, 1, 1)
        print("Fields verified successfully.")
        
        # Test nullability
        email_null = "test.null@usmba.ac.ma"
        Professor.objects.filter(email=email_null).delete()
        p_null = Professor.objects.create(
            nom="Test",
            prenom="Null",
            email=email_null,
            filiere="SMI",
            matiere="AI",
            nb_semaines=None,
            date_debut=None,
            date_fin=None,
            seances_semaine=None
        )
        print(f"Successfully created professor with null fields: {p_null.email}")
        
    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        # Clean up
        Professor.objects.filter(email=email).delete()
        Professor.objects.filter(email=email_null).delete()

if __name__ == "__main__":
    test_professor_fields()

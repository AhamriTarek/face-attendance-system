from django import forms
from .models import StudentFace

class StudentFaceForm(forms.ModelForm):
    # Additional field for file upload
    image = forms.ImageField(required=True, help_text="Upload a clear face image")
    
    # Optional code_masar for lookup
    code_masar = forms.CharField(required=False, label="Student Code (Massar)", 
                                help_text="Enter student code if not selecting from list")
    
    class Meta:
        model = StudentFace
        fields = ['student', 'model_used']
        widgets = {
            'student': forms.Select(attrs={'class': 'form-select'}),
            'model_used': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['student'].required = False
        self.fields['code_masar'].widget.attrs.update({'class': 'form-control', 'placeholder': 'e.g. M123456'})
    
    def clean(self):
        cleaned_data = super().clean()
        student = cleaned_data.get('student')
        code_masar = cleaned_data.get('code_masar')
        
        if not student and not code_masar:
            raise forms.ValidationError("You must either select a student or enter a Code Massar.")
        
        return cleaned_data

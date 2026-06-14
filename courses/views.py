from django.shortcuts import render, get_object_or_404
from accounts.decorators import professor_required
from accounts.models import Professor
from .models import Course

@professor_required
def professor_dashboard(request):
    professor = Professor.objects.get(id=request.session['professor_id'])
    courses = Course.objects.filter(professor=professor)
    return render(request, 'professor/dashboard.html', {
        'courses': courses,
        'professor': professor,
        'professor_nom': professor.nom,
        'professor_prenom': professor.prenom,
    })

@professor_required
def course_list(request):
    professor = Professor.objects.get(id=request.session['professor_id'])
    courses = Course.objects.filter(professor=professor)
    return render(request, 'professor/course_list.html', {'courses': courses, 'professor': professor})

from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.professor_dashboard, name='professor_dashboard'),
    path('courses/', views.course_list, name='course_list'),
]

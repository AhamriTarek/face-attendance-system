from django.urls import path
from . import views
from . import views_admin

urlpatterns = [
    # Admin URLs
    path('admin-dashboard/', views_admin.admin_dashboard, name='admin_dashboard'),
    path('add-student/', views_admin.add_student, name='add_student'),
    path('create-professor/', views_admin.create_professor, name='create_professor'),
    path('create-course/', views_admin.create_course, name='create_course'),
    
    # Home page (default route)
    path('', views.accueil_view, name='accueil'),
    path('accueil/', views.accueil_view, name='accueil'),
    
    # Auth URLs (keep login for backward compatibility, but redirect to accueil)
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
]

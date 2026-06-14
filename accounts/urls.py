from django.urls import path
from . import views
from . import views_admin

urlpatterns = [
    # Admin URLs
    path('admin-dashboard/', views_admin.admin_dashboard, name='admin_dashboard'),
    path('add-student/', views_admin.add_student, name='add_student'),
    path('add-student/bulk-save/', views_admin.bulk_save_students, name='bulk_save_students'),
    path('get-filieres/', views_admin.get_filieres, name='get_filieres'),
    path('get-students-by-filiere/', views_admin.get_students_by_filiere, name='get_students_by_filiere'),
    path('create-professor/', views_admin.bulk_create_professors_view, name='create_professor'),
    path('create-professor/bulk-save/', views_admin.bulk_save_professors, name='bulk_save'),
    path('create-course/', views_admin.create_course, name='create_course'),
    path('delete-student/<int:student_id>/', views_admin.delete_student, name='delete_student'),
    path('delete-professor/<int:professor_id>/', views_admin.delete_professor, name='delete_professor'),
    path('absence-rules/', views_admin.absence_rules, name='absence_rules'),
    
    # Home page (default route)
    path('', views.accueil_view, name='accueil'),
    path('accueil/', views.accueil_view, name='accueil'),
    
    # Auth URLs (keep login for backward compatibility, but redirect to accueil)
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),

    # Demo login (no OAuth required)
    path('demo-login/', views.demo_login_view, name='demo_login'),

    # Google OAuth Custom Routes
    path('google-login/<str:role>/', views.google_login, name='google_login'),
    path('google-login/', views.google_admin_login, name='google_admin_login'),
    path('oauth/google/callback/', views.google_callback, name='google_callback'),
]

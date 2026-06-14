from django.urls import path
from . import views

urlpatterns = [
    path('professor/dashboard/', views.professor_dashboard, name='professor_dashboard'),
    path('professor/take-attendance/<int:course_id>/', views.take_attendance, name='take_attendance'),
    path('professor/absence-list/<int:course_id>/', views.absence_list, name='absence_list'),
    path('video_feed/<int:course_id>/', views.video_feed, name='video_feed'),
    path('start_camera/', views.start_camera, name='start_camera'),
    path('stop_camera/', views.stop_camera, name='stop_camera'),
    path('get_present_students/', views.get_present_students, name='get_present_students'),
    path('save_session/', views.save_session, name='save_session'),
    path('professor/absence-total/<int:course_id>/', views.absence_total, name='absence_total'),
]

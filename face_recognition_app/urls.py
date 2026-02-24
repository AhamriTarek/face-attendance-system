from django.urls import path
from .api_views import RecognizeFaceAPI
from .views import add_face

urlpatterns = [
    path('recognize/', RecognizeFaceAPI.as_view(), name='recognize_api'),
    path('add/', add_face, name='add_face'),
]

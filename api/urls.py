from django.urls import path
from .views import create_basic_information

urlpatterns = [
    path('basic-information/', create_basic_information, name='basic-information-create'),
]
from django.urls import path
from .views import create_basic_information, get_basic_information, delete_basic_information

urlpatterns = [
    path('basic-information/', create_basic_information, name='basic-information-create'),
    path('basic-information/<int:client_id>/', get_basic_information, name='basic-information-get'),
    path('basic-information/<int:client_id>/delete/', delete_basic_information, name='basic-information-delete'),
]
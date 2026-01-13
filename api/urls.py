from django.urls import path
from .views import (
    create_basic_information,
    get_basic_information,
    delete_basic_information,
    calculate_retirement,
    get_breakdown,
    get_projection
)

urlpatterns = [
    path('basic-information/', create_basic_information, name='basic-information-create'),
    path('basic-information/<int:client_id>/', get_basic_information, name='basic-information-get'),
    path('basic-information/<int:client_id>/delete/', delete_basic_information, name='basic-information-delete'),
    path('calculate-retirement/<int:client_id>/', calculate_retirement, name='calculate-retirement'),
    path('breakdown/<int:client_id>/', get_breakdown, name='breakdown'),
    path('projection/<int:client_id>/', get_projection, name='projection'),
]
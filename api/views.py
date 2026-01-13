from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import BasicInformationSerializer


@api_view(['POST'])
def create_basic_information(request):
    basic_info_data = request.data.get('basic_information', {})
    investment_accounts_data = request.data.get('investment_accounts', [])
    life_events_data = request.data.get('life_events', [])
    
    combined_data = basic_info_data.copy()
    if investment_accounts_data:
        combined_data['investment_accounts'] = investment_accounts_data
    if life_events_data:
        combined_data['life_events'] = life_events_data
    
    serializer = BasicInformationSerializer(data=combined_data)
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

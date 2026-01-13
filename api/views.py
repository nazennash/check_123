from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import BasicInformationSerializer
from .models import BasicInformation


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
    
    current_age = basic_info_data.get('current_age')
    serializer = BasicInformationSerializer(data=combined_data, context={'current_age': current_age})
    
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def get_basic_information(request, client_id):
    try:
        basic_info = BasicInformation.objects.get(client_id=client_id)
        serializer = BasicInformationSerializer(basic_info)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except BasicInformation.DoesNotExist:
        return Response(
            {'error': f'Basic information with client_id {client_id} not found.'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['DELETE'])
def delete_basic_information(request, client_id):
    try:
        basic_info = BasicInformation.objects.get(client_id=client_id)
        basic_info.delete()
        return Response(
            {'message': f'Basic information with client_id {client_id} has been deleted successfully.'},
            status=status.HTTP_200_OK
        )
    except BasicInformation.DoesNotExist:
        return Response(
            {'error': f'Basic information with client_id {client_id} not found.'},
            status=status.HTTP_404_NOT_FOUND
        )

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import BasicInformationSerializer
from .models import BasicInformation
from calculator.services.orchestrator import run_retirement_calculation


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
        
        if basic_info.has_work_pension:
            basic_info.has_work_pension.delete()
        
        basic_info.investment_accounts.all().delete()
        basic_info.life_events.all().delete()
        
        basic_info.delete()
        
        return Response(
            {'message': f'Basic information with client_id {client_id} and all related data (work pension, investment accounts, life events) has been deleted successfully.'},
            status=status.HTTP_200_OK
        )
    except BasicInformation.DoesNotExist:
        return Response(
            {'error': f'Basic information with client_id {client_id} not found.'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
def calculate_retirement(request, client_id):
    """
    Calculate retirement projection for a given client_id.
    
    POST /api/calculate-retirement/<client_id>/
    """
    try:
        basic_info = BasicInformation.objects.get(client_id=client_id)
        
        # Run the retirement calculation
        results = run_retirement_calculation(basic_info, force_recalculate=True)
        
        # Prepare response data
        response_data = {
            'client_id': client_id,
            'projected_savings': results['projected_savings'],
            'savings_needed': results['savings_needed'],
            'extra_savings': results['extra_savings'],
            'is_on_track': results['is_on_track'],
            'run_out_age': results['run_out_age'],
            'success_probability': results['success_probability'],
            'additional_monthly_needed': results['additional_monthly_needed'],
            'retirement_age': results['projection'].retirement_age,
            'account_balances_at_retirement': results['account_balances_at_retirement'],
            'gap_analysis': results['gap_analysis'],
            'monte_carlo': {
                'success_probability': results['monte_carlo_results'].get('success_probability', 0.0),
                'percentile_10': results['monte_carlo_results'].get('percentile_10', 0.0),
                'percentile_25': results['monte_carlo_results'].get('percentile_25', 0.0),
                'percentile_50': results['monte_carlo_results'].get('percentile_50', 0.0),
                'percentile_75': results['monte_carlo_results'].get('percentile_75', 0.0),
                'percentile_90': results['monte_carlo_results'].get('percentile_90', 0.0),
            },
            'projection_id': results['projection'].id,
            'yearly_breakdown_count': len(results['yearly_breakdown'])
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except BasicInformation.DoesNotExist:
        return Response(
            {'error': f'Basic information with client_id {client_id} not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Error calculating retirement: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

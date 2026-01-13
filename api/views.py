from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import BasicInformationSerializer
from .models import BasicInformation
from calculator.services.orchestrator import run_retirement_calculation
from calculator.models import Projection


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


@api_view(['GET'])
def get_breakdown(request, client_id):
    """
    Get yearly breakdown table data for a given client_id.
    
    GET /api/breakdown/<client_id>/
    
    Returns the complete yearly breakdown with all financial details
    for the retirement projection.
    """
    try:
        basic_info = BasicInformation.objects.get(client_id=client_id)
        
        # Get the latest projection
        projection = basic_info.projections.first()
        
        if not projection:
            return Response(
                {'error': f'No projection found for client_id {client_id}. Please run calculation first.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get yearly breakdown from projection
        yearly_breakdown = projection.yearly_breakdown if projection.yearly_breakdown else []
        
        # Format breakdown data for table display
        formatted_breakdown = []
        for year_data in yearly_breakdown:
            formatted_year = {
                'age': year_data.get('age', 0),
                'year': year_data.get('year', 0),
                'phase': year_data.get('phase', 'unknown'),
                'starting_balance': year_data.get('starting_balance', 0.0),
                'tfsa': year_data.get('tfsa', 0.0),
                'rrsp': year_data.get('rrsp', 0.0),
                'non_reg': year_data.get('non_reg', 0.0),
                'total_contributions': year_data.get('total_contributions', 0.0),
                'portfolio_growth': year_data.get('portfolio_growth', 0.0),
                'work_optional_income_need': year_data.get('work_optional_income', 0.0) or year_data.get('income_needed', 0.0),
                'pension': year_data.get('pension', 0.0),
                'cpp': year_data.get('cpp', 0.0),
                'oas': year_data.get('oas', 0.0),
                'total_guaranteed_income': year_data.get('total_guaranteed_income', 0.0),
                'withdrawal_needed': year_data.get('withdrawal_needed', 0.0),
                'life_event': year_data.get('life_event', 0.0),
                'taxes': year_data.get('taxes', 0.0),
                'ending_balance': year_data.get('ending_balance', 0.0),
                'tfsa_ending': year_data.get('tfsa_ending', 0.0),
                'rrsp_ending': year_data.get('rrsp_ending', 0.0),
                'non_reg_ending': year_data.get('non_reg_ending', 0.0),
            }
            formatted_breakdown.append(formatted_year)
        
        response_data = {
            'client_id': client_id,
            'projection_id': projection.id,
            'retirement_age': projection.retirement_age,
            'total_years': len(formatted_breakdown),
            'breakdown': formatted_breakdown
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except BasicInformation.DoesNotExist:
        return Response(
            {'error': f'Basic information with client_id {client_id} not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Error retrieving breakdown: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_projection(request, client_id):
    """
    Get projection data for the projection dashboard.
    
    GET /api/projection/<client_id>/
    
    Returns projection summary data including:
    - Retirement savings goal
    - Projected savings at retirement
    - Shortfall/surplus
    - Additional monthly needed
    - Projection graph data points
    - Current contribution amounts
    - Forecast status
    """
    try:
        basic_info = BasicInformation.objects.get(client_id=client_id)
        
        # Get the latest projection
        projection = basic_info.projections.first()
        
        if not projection:
            return Response(
                {'error': f'No projection found for client_id {client_id}. Please run calculation first.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get yearly breakdown for graph data
        yearly_breakdown = projection.yearly_breakdown if projection.yearly_breakdown else []
        
        # Build graph data points (age vs balance)
        graph_data = []
        for year_data in yearly_breakdown:
            graph_data.append({
                'age': year_data.get('age', 0),
                'year': year_data.get('year', 0),
                'balance': year_data.get('ending_balance', 0.0),
                'phase': year_data.get('phase', 'unknown')
            })
        
        # Get current contribution amounts from investment accounts
        accounts = basic_info.investment_accounts.all()
        current_contributions = {
            'tfsa_monthly': 0.0,
            'rrsp_monthly': 0.0,
            'non_registered_monthly': 0.0
        }
        
        for account in accounts:
            account_type = account.account_type.upper() if account.account_type else ''
            monthly_contrib = float(account.monthly_contribution) / 100 if account.monthly_contribution else 0.0
            
            if account_type == 'TFSA':
                current_contributions['tfsa_monthly'] = monthly_contrib
            elif account_type == 'RRSP':
                current_contributions['rrsp_monthly'] = monthly_contrib
            elif account_type in ['NON_REG', 'NON_REGISTERED']:
                current_contributions['non_registered_monthly'] = monthly_contrib
        
        # Calculate shortfall/surplus (convert Decimal to float)
        extra_savings_float = float(projection.extra_savings) if projection.extra_savings else 0.0
        shortfall = abs(extra_savings_float) if extra_savings_float < 0 else 0.0
        surplus = extra_savings_float if extra_savings_float > 0 else 0.0
        
        # Convert Decimal to float for calculations
        savings_needed_float = float(projection.savings_needed) if projection.savings_needed else 0.0
        
        # Determine forecast status
        if projection.is_on_track:
            forecast_status = "on_track"
            forecast_message = "You're on track!"
            forecast_submessage = f"You'll have ${surplus:,.0f} more than needed."
        elif shortfall > 0:
            forecast_status = "almost_there" if shortfall < savings_needed_float * 0.1 else "off_track"
            if forecast_status == "almost_there":
                forecast_message = "Almost there"
                forecast_submessage = f"It looks like you'll be short by about ${shortfall:,.0f}"
            else:
                forecast_message = "Off track"
                forecast_submessage = f"You'll be short by ${shortfall:,.0f}"
        else:
            forecast_status = "on_track"
            forecast_message = "You're on track!"
            forecast_submessage = ""
        
        # Get additional monthly needed (from gap analysis if available)
        additional_monthly_needed = 0.0
        if shortfall > 0:
            # Calculate from shortfall, years to retirement, and expected return
            years_to_retirement = projection.retirement_age - basic_info.current_age
            if years_to_retirement > 0:
                # Get expected return from accounts
                total_balance = sum(float(acc.balance) / 100 for acc in accounts)
                weighted_return = 0.05  # Default
                if total_balance > 0:
                    # Simple weighted return calculation
                    weighted_return = sum(
                        (float(acc.balance) / 100) * 0.05  # Using 5% as default
                        for acc in accounts
                    ) / total_balance
                
                # Calculate monthly payment needed using future value of annuity
                monthly_return = (1 + weighted_return) ** (1/12) - 1
                months_to_retirement = years_to_retirement * 12
                
                if monthly_return > 0:
                    fv_factor = ((1 + monthly_return) ** months_to_retirement - 1) / monthly_return
                    additional_monthly_needed = shortfall / fv_factor if fv_factor > 0 else 0
                else:
                    additional_monthly_needed = shortfall / months_to_retirement
        
        # Convert all Decimal fields to float for JSON serialization
        projected_savings_float = float(projection.projected_savings) if projection.projected_savings else 0.0
        savings_needed_float = float(projection.savings_needed) if projection.savings_needed else 0.0
        
        response_data = {
            'client_id': client_id,
            'projection_id': projection.id,
            'retirement_savings_goal': savings_needed_float,
            'projected_savings_at_retirement': projected_savings_float,
            'what_youll_have': projected_savings_float,
            'what_youll_need': savings_needed_float,
            'shortfall': shortfall,
            'surplus': surplus,
            'is_on_track': projection.is_on_track,
            'additional_monthly_needed': round(additional_monthly_needed, 2),
            'retirement_age': projection.retirement_age,
            'current_age': basic_info.current_age,
            'plan_until_age': basic_info.plan_until_age if basic_info.plan_until_age else 90,
            'forecast': {
                'status': forecast_status,
                'message': forecast_message,
                'submessage': forecast_submessage,
                'additional_monthly_needed': round(additional_monthly_needed, 2) if shortfall > 0 else 0
            },
            'current_contributions': current_contributions,
            'graph_data': graph_data,
            'retirement_peak': {
                'age': projection.retirement_age,
                'what_youll_have': projected_savings_float,
                'what_youll_need': savings_needed_float
            }
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except BasicInformation.DoesNotExist:
        return Response(
            {'error': f'Basic information with client_id {client_id} not found.'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {'error': f'Error retrieving projection: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# file objective - runs the whole retirement calculation in the correct order - main entry point retirement calculations.

from typing import Dict, Any
from api.models import BasicInformation
from calculator.services.preprocessing import preprocess_retirement_plan
from calculator.services.accumulation_engine import (
    run_accumulation_phase,
    get_projected_savings_at_retirement,
    get_account_balances_at_retirement
)
from calculator.services.withdrawal_engine import run_withdrawal_phase, find_run_out_age
from calculator.services.savings_needed import calculate_savings_needed
from calculator.services.gap_analysis import perform_gap_analysis, calculate_additional_monthly_needed
from calculator.services.projection_creation import (
    create_or_update_projection,
    consolidate_projection_data
)
from calculator.services.monte_carlo import run_monte_carlo_simulation


def run_retirement_calculation(
    basic_info: BasicInformation,
    force_recalculate: bool = False
) -> Dict[str, Any]:
    """
    Main orchestrator function that runs the complete retirement calculation process.
    
    INPUTS:
        basic_info: BasicInformation object - User's retirement plan data
        force_recalculate: bool - If True, delete old projections and create new
    
    OUTPUTS:
        Dict containing all calculation results:
        {
            'projection': Projection object,
            'projected_savings': float,
            'savings_needed': float,
            'extra_savings': float,
            'is_on_track': bool,
            'run_out_age': int or None,
            'success_probability': float,
            'additional_monthly_needed': float,
            'yearly_breakdown': List[Dict],
            'monte_carlo_results': Dict,
            'gap_analysis': Dict
        }
    """
    # Step 1: Preprocessing
    accounts = list(basic_info.investment_accounts.all())
    preprocessed_data = preprocess_retirement_plan(basic_info, accounts)
    
    years_to_retirement = preprocessed_data['years_to_retirement']
    years_in_retirement = preprocessed_data['years_in_retirement']
    retirement_age = preprocessed_data['retirement_age']
    life_expectancy = preprocessed_data['life_expectancy']
    
    # Step 2: Accumulation Phase
    accumulation_breakdown = run_accumulation_phase(
        basic_info=basic_info,
        accounts=accounts,
        years_to_retirement=years_to_retirement,
        preprocessed_data=preprocessed_data
    )
    
    # Step 3: Get Projected Savings at Retirement
    projected_savings = get_projected_savings_at_retirement(
        accumulation_breakdown,
        years_to_retirement
    )
    
    # Step 4: Get Account Balances at Retirement
    account_balances_at_retirement = get_account_balances_at_retirement(
        accumulation_breakdown,
        years_to_retirement
    )
    
    # Step 5: Calculate Savings Needed
    savings_needed = calculate_savings_needed(
        basic_info=basic_info,
        preprocessed_data=preprocessed_data
    )
    
    # Step 6: Withdrawal Phase
    withdrawal_breakdown = run_withdrawal_phase(
        basic_info=basic_info,
        account_balances_at_retirement=account_balances_at_retirement,
        years_in_retirement=years_in_retirement,
        years_to_retirement=years_to_retirement,
        preprocessed_data=preprocessed_data
    )
    
    # Step 7: Find Run-Out Age
    run_out_age = find_run_out_age(withdrawal_breakdown)
    
    # Step 8: Consolidate Yearly Breakdown
    yearly_breakdown = consolidate_projection_data(
        accumulation_breakdown,
        withdrawal_breakdown
    )
    
    # Step 9: Gap Analysis
    gap_analysis = perform_gap_analysis(
        projected_savings=projected_savings,
        savings_needed=savings_needed,
        yearly_breakdown=yearly_breakdown,
        retirement_age=retirement_age,
        life_expectancy=life_expectancy
    )
    
    # Step 10: Monte Carlo Simulation
    expected_return = preprocessed_data['accumulation_returns']['weighted_return']
    monte_carlo_results = run_monte_carlo_simulation(
        accumulation_breakdown=accumulation_breakdown,
        withdrawal_breakdown=withdrawal_breakdown,
        years_to_retirement=years_to_retirement,
        years_in_retirement=years_in_retirement,
        expected_return=expected_return
    )
    
    # Step 11: Calculate Additional Monthly Needed (if shortfall)
    additional_monthly_needed = 0.0
    if gap_analysis['shortfall_amount'] > 0:
        additional_monthly_needed = calculate_additional_monthly_needed(
            shortfall_amount=gap_analysis['shortfall_amount'],
            years_to_retirement=years_to_retirement,
            expected_return=expected_return
        )
    
    # Step 12: Create or Update Projection
    projection = create_or_update_projection(
        basic_info=basic_info,
        projected_savings=projected_savings,
        savings_needed=savings_needed,
        extra_savings=gap_analysis['extra_savings'],
        is_on_track=gap_analysis['is_on_track'],
        yearly_breakdown=yearly_breakdown,
        monte_carlo_results=monte_carlo_results,
        run_out_age=run_out_age,
        force_recalculate=force_recalculate
    )
    
    return {
        'projection': projection,
        'projected_savings': projected_savings,
        'savings_needed': savings_needed,
        'extra_savings': gap_analysis['extra_savings'],
        'is_on_track': gap_analysis['is_on_track'],
        'run_out_age': run_out_age,
        'success_probability': monte_carlo_results.get('success_probability', 0.0),
        'additional_monthly_needed': additional_monthly_needed,
        'yearly_breakdown': yearly_breakdown,
        'monte_carlo_results': monte_carlo_results,
        'gap_analysis': gap_analysis,
        'account_balances_at_retirement': account_balances_at_retirement
    }


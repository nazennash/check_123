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
    print("\n" + "-"*8)
    print("-"*8)
    print("RETIREMENT CALCULATION ORCHESTRATOR - MAIN ENTRY POINT")
    print("-"*8)
    print("-"*8)
    
    print("\n[INPUT DATA]")
    print(f"  Client ID: {basic_info.client_id}")
    print(f"  Current Age: {basic_info.current_age}")
    print(f"  Work Optional Age: {basic_info.work_optional_age}")
    print(f"  Plan Until Age: {basic_info.plan_until_age}")
    print(f"  Force Recalculate: {force_recalculate}")
    
    # Step 1: Preprocessing
    print("\n" + "-"*8)
    print("STEP 1: PREPROCESSING")
    print("-"*8)
    accounts = list(basic_info.investment_accounts.all())
    print(f"  Number of accounts: {len(accounts)}")
    preprocessed_data = preprocess_retirement_plan(basic_info, accounts)
    
    years_to_retirement = preprocessed_data['years_to_retirement']
    years_in_retirement = preprocessed_data['years_in_retirement']
    retirement_age = preprocessed_data['retirement_age']
    life_expectancy = preprocessed_data['life_expectancy']
    
    print(f"\n  [PREPROCESSING RESULTS]")
    print(f"    Years to retirement: {years_to_retirement}")
    print(f"    Years in retirement: {years_in_retirement}")
    print(f"    Retirement age: {retirement_age}")
    print(f"    Life expectancy: {life_expectancy}")
    
    # Step 2: Accumulation Phase
    print("\n" + "-"*8)
    print("STEP 2: ACCUMULATION PHASE")
    print("-"*8)
    print(f"  Running accumulation phase for {years_to_retirement} years...")
    accumulation_breakdown = run_accumulation_phase(
        basic_info=basic_info,
        accounts=accounts,
        years_to_retirement=years_to_retirement,
        preprocessed_data=preprocessed_data
    )
    print(f"  Accumulation phase complete: {len(accumulation_breakdown)} years simulated")
    
    # Step 3: Get Projected Savings at Retirement
    print("\n" + "-"*8)
    print("STEP 3: EXTRACT PROJECTED SAVINGS AT RETIREMENT")
    print("-"*8)
    projected_savings = get_projected_savings_at_retirement(
        accumulation_breakdown,
        years_to_retirement
    )
    print(f"  Projected savings at retirement: ${projected_savings:,.2f}")
    
    # Step 4: Get Account Balances at Retirement
    print("\n" + "-"*8)
    print("STEP 4: EXTRACT ACCOUNT BALANCES AT RETIREMENT")
    print("-"*8)
    account_balances_at_retirement = get_account_balances_at_retirement(
        accumulation_breakdown,
        years_to_retirement
    )
    print(f"  Account balances at retirement:")
    print(f"    TFSA: ${account_balances_at_retirement.get('TFSA', 0.0):,.2f}")
    print(f"    RRSP: ${account_balances_at_retirement.get('RRSP', 0.0):,.2f}")
    print(f"    NON_REG: ${account_balances_at_retirement.get('NON_REG', 0.0):,.2f}")
    total_at_retirement = sum(account_balances_at_retirement.values())
    print(f"    Total: ${total_at_retirement:,.2f}")
    
    # Step 5: Calculate Savings Needed
    print("\n" + "-"*8)
    print("STEP 5: CALCULATE SAVINGS NEEDED")
    print("-"*8)
    savings_needed = calculate_savings_needed(
        basic_info=basic_info,
        preprocessed_data=preprocessed_data
    )
    print(f"  Savings needed at retirement: ${savings_needed:,.2f}")
    
    # Step 6: Withdrawal Phase
    print("\n" + "-"*8)
    print("STEP 6: WITHDRAWAL PHASE")
    print("-"*8)
    print(f"  Running withdrawal phase for {years_in_retirement} years...")
    withdrawal_breakdown = run_withdrawal_phase(
        basic_info=basic_info,
        account_balances_at_retirement=account_balances_at_retirement,
        years_in_retirement=years_in_retirement,
        years_to_retirement=years_to_retirement,
        preprocessed_data=preprocessed_data
    )
    print(f"  Withdrawal phase complete: {len(withdrawal_breakdown)} years simulated")
    
    # Step 7: Find Run-Out Age
    print("\n" + "-"*8)
    print("STEP 7: FIND RUN-OUT AGE")
    print("-"*8)
    run_out_age = find_run_out_age(withdrawal_breakdown)
    if run_out_age:
        print(f"  Money runs out at age: {run_out_age}")
    else:
        print(f"  Money lasts through retirement (no run-out age)")
    
    # Step 8: Consolidate Yearly Breakdown
    print("\n" + "-"*8)
    print("STEP 8: CONSOLIDATE YEARLY BREAKDOWN")
    print("-"*8)
    yearly_breakdown = consolidate_projection_data(
        accumulation_breakdown,
        withdrawal_breakdown
    )
    print(f"  Total years in breakdown: {len(yearly_breakdown)}")
    print(f"    Accumulation years: {len(accumulation_breakdown)}")
    print(f"    Withdrawal years: {len(withdrawal_breakdown)}")
    
    # Step 9: Gap Analysis
    print("\n" + "-"*8)
    print("STEP 9: GAP ANALYSIS")
    print("-"*8)
    gap_analysis = perform_gap_analysis(
        projected_savings=projected_savings,
        savings_needed=savings_needed,
        yearly_breakdown=yearly_breakdown,
        retirement_age=retirement_age,
        life_expectancy=life_expectancy
    )
    print(f"  Gap analysis results:")
    print(f"    Extra savings: ${gap_analysis['extra_savings']:,.2f}")
    print(f"    Shortfall amount: ${gap_analysis['shortfall_amount']:,.2f}")
    print(f"    Surplus amount: ${gap_analysis['surplus_amount']:,.2f}")
    print(f"    Is on track: {gap_analysis['is_on_track']}")
    print(f"    Run-out age: {gap_analysis['run_out_age']}")
    
    # Step 10: Monte Carlo Simulation
    print("\n" + "-"*8)
    print("STEP 10: MONTE CARLO SIMULATION")
    print("-"*8)
    expected_return = preprocessed_data['accumulation_returns']['weighted_return']
    print(f"  Expected return: {expected_return * 100:.2f}%")
    print(f"  Running {1000} simulations...")
    monte_carlo_results = run_monte_carlo_simulation(
        accumulation_breakdown=accumulation_breakdown,
        withdrawal_breakdown=withdrawal_breakdown,
        years_to_retirement=years_to_retirement,
        years_in_retirement=years_in_retirement,
        expected_return=expected_return
    )
    print(f"  Monte Carlo results:")
    print(f"    Success probability: {monte_carlo_results.get('success_probability', 0.0):.2f}%")
    print(f"    10th percentile: ${monte_carlo_results.get('percentile_10', 0.0):,.2f}")
    print(f"    50th percentile (median): ${monte_carlo_results.get('percentile_50', 0.0):,.2f}")
    print(f"    90th percentile: ${monte_carlo_results.get('percentile_90', 0.0):,.2f}")
    
    # Step 11: Calculate Additional Monthly Needed (if shortfall)
    print("\n" + "-"*8)
    print("STEP 11: CALCULATE ADDITIONAL MONTHLY NEEDED")
    print("-"*8)
    additional_monthly_needed = 0.0
    if gap_analysis['shortfall_amount'] > 0:
        print(f"  Shortfall detected: ${gap_analysis['shortfall_amount']:,.2f}")
        print(f"  Calculating additional monthly contribution needed...")
        additional_monthly_needed = calculate_additional_monthly_needed(
            shortfall_amount=gap_analysis['shortfall_amount'],
            years_to_retirement=years_to_retirement,
            expected_return=expected_return
        )
        print(f"  Additional monthly needed: ${additional_monthly_needed:,.2f}")
    else:
        print(f"  No shortfall - no additional monthly contribution needed")
    
    # Step 12: Create or Update Projection
    print("\n" + "-"*8)
    print("STEP 12: CREATE OR UPDATE PROJECTION")
    print("-"*8)
    print(f"  Saving results to database...")
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
    print(f"  Projection saved: ID {projection.id}")
    
    print("\n" + "-"*8)
    print("-"*8)
    print("ORCHESTRATOR COMPLETE - ALL CALCULATIONS FINISHED")
    print("-"*8)
    print("-"*80 + "\n")
    
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


"""
WITHDRAWAL ENGINE
================

This module handles the withdrawal phase of retirement planning - simulating
retirement withdrawals from savings to meet income needs during retirement.

The Withdrawal Engine calculates income needs, applies government benefits,
withdraws from accounts based on strategy, and tracks if money runs out.

INPUTS: Preprocessed assumptions, account balances at retirement, income needs
OUTPUTS: Year-by-year withdrawal breakdown, run-out age if applicable
"""

from typing import List, Dict, Any
from api.models import BasicInformation, LifeEvent
from .utils import calculate_life_event_impact, apply_withdrawal_strategy, calculate_inflated_income_need


def simulate_withdrawal_year(
    account_balances: Dict[str, float],
    basic_info: BasicInformation,
    age: int,
    year: int,
    years_to_retirement: int,
    years_since_retirement: int,
    preprocessed_data: Dict[str, Any],
    life_events: List[LifeEvent]
) -> Dict[str, Any]:
    """
    Simulate a single year of retirement withdrawals.
    
    INPUTS:
        account_balances: Dict[str, float] - Current balances by account type
            Format: {'TFSA': 200000.0, 'RRSP': 300000.0, 'NON_REG': 100000.0}
        plan: RetirementPlan object containing user inputs
        age: int - Current age
        year: int - Calendar year
        years_to_retirement: int - Years from start to retirement
        years_since_retirement: int - Years since retirement started
        preprocessed_data: Dict from preprocessing layer containing:
            - 'cpp_adjusted': float - Adjusted CPP annual amount
            - 'oas_adjusted': float - Adjusted OAS annual amount
            - 'pension_amount': float - Pension annual amount
            - 'inflation_rate': float - Inflation rate as decimal
            - 'return_after_retirement': float - Post-retirement return as decimal
        life_events: List[LifeEvent] - Life events that may affect this year
    
    OUTPUTS:
        Dict containing:
        {
            'age': int,
            'year': int,
            'phase': 'retirement',
            'starting_balance': float,           # Total starting balance
            'tfsa': float,                      # TFSA starting balance
            'rrsp': float,                      # RRSP starting balance
            'non_reg': float,                   # Non-Registered starting balance
            'total_contributions': 0,           # No contributions in retirement
            'portfolio_growth': float,          # Growth on remaining balances
            'work_optional_income': float,      # Inflated income need
            'income_needed': float,             # Same as work_optional_income
            'pension': float,                   # Pension income this year
            'cpp': float,                       # CPP income this year
            'oas': float,                       # OAS income this year
            'total_guaranteed_income': float,   # Sum of guaranteed income
            'withdrawal_needed': float,         # Amount to withdraw from portfolio
            'life_event': float,                # Net life event impact
            'taxes': float,                     # Estimated taxes (simplified, currently 0)
            'ending_balance': float,            # Total ending balance
            'tfsa_ending': float,              # TFSA ending balance
            'rrsp_ending': float,              # RRSP ending balance
            'non_reg_ending': float            # Non-Registered ending balance
        }
        
    PROCESS:
        1. Calculate inflated income need
        2. Calculate guaranteed income (CPP, OAS, Pension)
        3. Calculate withdrawal needed
        4. Apply withdrawal strategy
        5. Apply life events
        6. Apply growth to remaining balances
    """
    if years_since_retirement % 5 == 0 or years_since_retirement < 3:  # Print every 5 years or early years
        print(f"\n    [WITHDRAWAL YEAR {year} - Age {age}, Year {years_since_retirement} of retirement]")
    
    # Record starting balances
    starting_balance = sum(account_balances.values())
    tfsa_start = account_balances.get('TFSA', 0.0)
    rrsp_start = account_balances.get('RRSP', 0.0)
    nonreg_start = account_balances.get('NON_REG', 0.0)
    
    if years_since_retirement % 5 == 0 or years_since_retirement < 3:
        print(f"      Starting balances: TFSA=${tfsa_start:,.2f}, RRSP=${rrsp_start:,.2f}, NON_REG=${nonreg_start:,.2f}, Total=${starting_balance:,.2f}")
    
    # Extract preprocessed data
    cpp_adjusted = preprocessed_data['cpp_adjusted']
    oas_adjusted = preprocessed_data['oas_adjusted']
    pension_amount = preprocessed_data['pension_amount']
    inflation_rate = preprocessed_data['inflation_rate']
    return_after_retirement = preprocessed_data['return_after_retirement']
    
    # Step 1: Calculate Inflated Income Need
    yearly_income_goal = float(basic_info.yearly_income_for_ideal_lifestyle) / 100 if basic_info.yearly_income_for_ideal_lifestyle else 0.0
    inflated_income_need = calculate_inflated_income_need(
        yearly_income_goal=yearly_income_goal,
        inflation_rate=inflation_rate,
        years_to_retirement=years_to_retirement,
        years_since_retirement=years_since_retirement
    )
    
    if years_since_retirement % 5 == 0 or years_since_retirement < 3:
        print(f"      Income need (inflated): ${inflated_income_need:,.2f}")
    
    # Step 2: Calculate Guaranteed Income for This Year
    # Government benefits start at specified ages
    cpp_start_age = basic_info.cpp_start_age if basic_info.cpp_start_age else 65
    oas_start_age = basic_info.oas_start_age if basic_info.oas_start_age else 65
    work_pension = basic_info.work_pensions.first()  # Get first work pension (supports multiple now)
    pension_start_age = work_pension.pension_start_age if work_pension and work_pension.pension_start_age else 65
    has_pension = work_pension and work_pension.has_pension if work_pension else False
    
    cpp_income = cpp_adjusted if age >= cpp_start_age else 0.0
    oas_income = oas_adjusted if age >= oas_start_age else 0.0
    pension_income = pension_amount if has_pension and age >= pension_start_age else 0.0
    total_guaranteed_income = cpp_income + oas_income + pension_income
    
    if years_since_retirement % 5 == 0 or years_since_retirement < 3:
        print(f"      Guaranteed income: CPP=${cpp_income:,.2f}, OAS=${oas_income:,.2f}, Pension=${pension_income:,.2f}, Total=${total_guaranteed_income:,.2f}")
    
    # Step 3: Calculate Withdrawal Needed from Portfolio
    withdrawal_needed = max(0.0, inflated_income_need - total_guaranteed_income)
    
    if years_since_retirement % 5 == 0 or years_since_retirement < 3:
        print(f"      Withdrawal needed from portfolio: ${withdrawal_needed:,.2f}")
    
    # Step 4: Apply Life Events
    life_event_impacts = calculate_life_event_impact(
        life_events, age, inflation_rate, years_since_retirement
    )
    total_life_event_impact = sum(life_event_impacts.values())
    
    if total_life_event_impact != 0 and (years_since_retirement % 5 == 0 or years_since_retirement < 3):
        print(f"      Life event impact: ${total_life_event_impact:,.2f}")
    
    # Step 5: Apply Withdrawal Strategy and Life Events
    if starting_balance > 0:
        # Apply withdrawal strategy (modifies account_balances in place)
        strategy = basic_info.withdrawal_strategy.lower() if basic_info.withdrawal_strategy else 'optimized'
        if years_since_retirement % 5 == 0 or years_since_retirement < 3:
            print(f"      Applying withdrawal strategy: {strategy}")
        apply_withdrawal_strategy(
            strategy=strategy,
            withdrawal_needed=withdrawal_needed,
            account_balances=account_balances
        )
        
        # Add life events to appropriate accounts
        for acc_type, impact in life_event_impacts.items():
            if acc_type in account_balances:
                account_balances[acc_type] += impact
        
        # Step 6: Apply Growth to Remaining Balances
        # All accounts use the same return_after_retirement rate
        tfsa_growth = account_balances.get('TFSA', 0.0) * return_after_retirement
        rrsp_growth = account_balances.get('RRSP', 0.0) * return_after_retirement
        nonreg_growth = account_balances.get('NON_REG', 0.0) * return_after_retirement
        portfolio_growth = tfsa_growth + rrsp_growth + nonreg_growth
        
        if years_since_retirement % 5 == 0 or years_since_retirement < 3:
            print(f"      Portfolio growth ({return_after_retirement*100:.2f}%): ${portfolio_growth:,.2f}")
        
        # Add growth to balances
        account_balances['TFSA'] = account_balances.get('TFSA', 0.0) + tfsa_growth
        account_balances['RRSP'] = account_balances.get('RRSP', 0.0) + rrsp_growth
        account_balances['NON_REG'] = account_balances.get('NON_REG', 0.0) + nonreg_growth
    else:
        portfolio_growth = 0.0
    
    # Calculate ending balances
    ending_balance = sum(account_balances.values())
    ending_balance = max(0.0, ending_balance)  # Cannot be negative
    tfsa_ending = account_balances.get('TFSA', 0.0)
    rrsp_ending = account_balances.get('RRSP', 0.0)
    nonreg_ending = account_balances.get('NON_REG', 0.0)
    
    if years_since_retirement % 5 == 0 or years_since_retirement < 3:
        print(f"      Ending balances: TFSA=${tfsa_ending:,.2f}, RRSP=${rrsp_ending:,.2f}, NON_REG=${nonreg_ending:,.2f}, Total=${ending_balance:,.2f}")
    
    # Estimate taxes (simplified - currently returns 0)
    taxes = 0.0
    
    return {
        'age': age,
        'year': year,
        'phase': 'retirement',
        'starting_balance': round(starting_balance, 2),
        'tfsa': round(tfsa_start, 2),
        'rrsp': round(rrsp_start, 2),
        'non_reg': round(nonreg_start, 2),
        'total_contributions': 0,
        'portfolio_growth': round(portfolio_growth, 2),
        'work_optional_income': round(inflated_income_need, 2),
        'income_needed': round(inflated_income_need, 2),
        'pension': round(pension_income, 2),
        'cpp': round(cpp_income, 2),
        'oas': round(oas_income, 2),
        'total_guaranteed_income': round(total_guaranteed_income, 2),
        'withdrawal_needed': round(withdrawal_needed, 2),
        'life_event': round(total_life_event_impact, 2),
        'taxes': round(taxes, 2),
        'ending_balance': round(ending_balance, 2),
        'tfsa_ending': round(tfsa_ending, 2),
        'rrsp_ending': round(rrsp_ending, 2),
        'non_reg_ending': round(nonreg_ending, 2),
    }


def run_withdrawal_phase(
    basic_info: BasicInformation,
    account_balances_at_retirement: Dict[str, float],
    years_to_retirement: int,
    years_in_retirement: int,
    preprocessed_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Run the complete withdrawal phase from retirement age to life expectancy.
    
    INPUTS:
        basic_info: BasicInformation object containing user inputs
        account_balances_at_retirement: Dict[str, float] - Starting balances at retirement
            Format: {'TFSA': 200000.0, 'RRSP': 300000.0, 'NON_REG': 100000.0}
        years_to_retirement: int - Years from start to retirement
        years_in_retirement: int - Years in retirement phase
        preprocessed_data: Dict from preprocessing layer
    
    OUTPUTS:
        List[Dict[str, Any]] - Year-by-year breakdown of withdrawal phase
        Each dict contains the same structure as simulate_withdrawal_year()
        
    PROCESS:
        For each year from retirement age to life expectancy:
            1. Simulate withdrawal for that year
            2. Update account balances for next year
            3. Store year data in breakdown
    """
    print("\n[INPUT DATA]")
    retirement_age = basic_info.work_optional_age if basic_info.work_optional_age else basic_info.current_age + 30
    print(f"  Retirement age: {retirement_age}")
    print(f"  Years in retirement: {years_in_retirement}")
    print(f"  Starting account balances at retirement:")
    print(f"    TFSA: ${account_balances_at_retirement.get('TFSA', 0.0):,.2f}")
    print(f"    RRSP: ${account_balances_at_retirement.get('RRSP', 0.0):,.2f}")
    print(f"    NON_REG: ${account_balances_at_retirement.get('NON_REG', 0.0):,.2f}")
    total_start = sum(account_balances_at_retirement.values())
    print(f"    Total: ${total_start:,.2f}")
    
    breakdown = []
    current_year = 2025  # Base year
    
    # Start with balances at retirement
    account_balances = account_balances_at_retirement.copy()
    
    # Get life events
    life_events = list(basic_info.life_events.all())
    print(f"  Number of life events: {len(life_events)}")
    
    print(f"\n[PROCESSING]")
    print(f"  Simulating {years_in_retirement} years of withdrawals...")
    
    # Simulate each year during retirement
    for year_idx in range(years_in_retirement):
        age = retirement_age + year_idx
        year = current_year + years_to_retirement + year_idx
        years_since_retirement = year_idx
        
        # Simulate this year
        year_data = simulate_withdrawal_year(
            account_balances=account_balances,
            basic_info=basic_info,
            age=age,
            year=year,
            years_to_retirement=years_to_retirement,
            years_since_retirement=years_since_retirement,
            preprocessed_data=preprocessed_data,
            life_events=life_events
        )
        
        # Update balances for next iteration
        account_balances['TFSA'] = year_data['tfsa_ending']
        account_balances['RRSP'] = year_data['rrsp_ending']
        account_balances['NON_REG'] = year_data['non_reg_ending']
        
        breakdown.append(year_data)
    
    print(f"\n[OUTPUT RESULTS]")
    if breakdown:
        final_year = breakdown[-1]
        print(f"  Final year (age {final_year['age']}):")
        print(f"    Ending balance: ${final_year['ending_balance']:,.2f}")
        print(f"    TFSA ending: ${final_year['tfsa_ending']:,.2f}")
        print(f"    RRSP ending: ${final_year['rrsp_ending']:,.2f}")
        print(f"    NON_REG ending: ${final_year['non_reg_ending']:,.2f}")
    print(f"  Total years simulated: {len(breakdown)}")
    
    return breakdown


def find_run_out_age(
    withdrawal_breakdown: List[Dict[str, Any]]
) -> int:
    """
    Find the age at which money runs out (if applicable).
    
    INPUTS:
        withdrawal_breakdown: List[Dict] - Year-by-year withdrawal data
    
    OUTPUTS:
        int or None - Age when money runs out, or None if money lasts
    """
    print(f"\n[PROCESSING]")
    print(f"  Searching for run-out age in {len(withdrawal_breakdown)} years of withdrawal data...")
    
    for year_data in withdrawal_breakdown:
        ending_balance = year_data.get('ending_balance', 0)
        age = year_data.get('age')
        if ending_balance <= 0:
            print(f"  Found run-out at age {age} (ending balance: ${ending_balance:,.2f})")
            return age
    
    print(f"  No run-out age found - money lasts through retirement")
    return None


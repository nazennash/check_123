"""
ACCUMULATION ENGINE
===================

This module handles the accumulation phase of retirement planning - simulating
savings growth from current age until retirement age.

The Accumulation Engine applies contributions, life events, and investment growth
year-by-year to project how savings will grow before retirement.

INPUTS: Preprocessed assumptions, account data, life events
OUTPUTS: Year-by-year accumulation breakdown, projected savings at retirement
"""

from typing import List, Dict, Any
from ..models import RetirementPlan, InvestmentAccount, LifeEvent
from .utils import calculate_life_event_impact
from .preprocessing import prepare_account_data


def simulate_accumulation_year(
    account_balances: Dict[str, float],
    account_contributions: Dict[str, float],
    account_returns: Dict[str, float],
    life_events: List[LifeEvent],
    age: int,
    inflation_rate: float,
    year: int
) -> Dict[str, Any]:
    """
    Simulate a single year of accumulation (before retirement).
    
    INPUTS:
        account_balances: Dict[str, float] - Current balances by account type
            Format: {'TFSA': 100000.0, 'RRSP': 150000.0, 'NON_REG': 50000.0}
        account_contributions: Dict[str, float] - Annual contributions by account type
            Format: {'TFSA': 6000.0, 'RRSP': 9600.0, 'NON_REG': 0.0}
        account_returns: Dict[str, float] - Expected returns by account type (as decimals)
            Format: {'TFSA': 0.05, 'RRSP': 0.05, 'NON_REG': 0.10}
        life_events: List[LifeEvent] - Life events that may affect this year
        age: int - Current age
        inflation_rate: float - Annual inflation rate as decimal (e.g., 0.025 for 2.5%)
        year: int - Calendar year
    
    OUTPUTS:
        Dict containing:
        {
            'age': int,
            'year': int,
            'phase': 'accumulation',
            'starting_balance': float,        # Total starting balance
            'tfsa': float,                   # TFSA starting balance
            'rrsp': float,                   # RRSP starting balance
            'non_reg': float,                # Non-Registered starting balance
            'total_contributions': float,    # Total contributions added
            'portfolio_growth': float,       # Total growth for the year
            'life_event': float,             # Net life event impact
            'ending_balance': float,         # Total ending balance
            'tfsa_ending': float,            # TFSA ending balance
            'rrsp_ending': float,            # RRSP ending balance
            'non_reg_ending': float          # Non-Registered ending balance
        }
        
    PROCESS:
        1. Record starting balances
        2. Apply life events (income/expenses)
        3. Add monthly contributions (converted to annual)
        4. Apply investment growth based on profile returns
        5. Calculate ending balances
    """
    # Record starting balances
    starting_balance = sum(account_balances.values())
    tfsa_start = account_balances.get('TFSA', 0.0)
    rrsp_start = account_balances.get('RRSP', 0.0)
    nonreg_start = account_balances.get('NON_REG', 0.0)
    
    # Calculate contributions for each account
    tfsa_contrib = account_contributions.get('TFSA', 0.0)
    rrsp_contrib = account_contributions.get('RRSP', 0.0)
    nonreg_contrib = account_contributions.get('NON_REG', 0.0)
    total_contributions = tfsa_contrib + rrsp_contrib + nonreg_contrib
    
    # Step 1: Apply Life Events
    # Life events can add income or subtract expenses
    years_since_retirement = 0  # Not retired yet
    life_event_impacts = calculate_life_event_impact(
        life_events, age, inflation_rate, years_since_retirement
    )
    total_life_event_impact = sum(life_event_impacts.values())
    
    # Apply life event impacts to appropriate accounts
    for acc_type, impact in life_event_impacts.items():
        if acc_type in account_balances:
            account_balances[acc_type] += impact
    
    # Step 2: Apply Monthly Contributions (converted to annual)
    account_balances['TFSA'] = account_balances.get('TFSA', 0.0) + tfsa_contrib
    account_balances['RRSP'] = account_balances.get('RRSP', 0.0) + rrsp_contrib
    account_balances['NON_REG'] = account_balances.get('NON_REG', 0.0) + nonreg_contrib
    
    # Step 3: Apply Investment Growth
    # Growth is calculated on the balance after contributions
    tfsa_return = account_returns.get('TFSA', 0.05)
    rrsp_return = account_returns.get('RRSP', 0.05)
    nonreg_return = account_returns.get('NON_REG', 0.05)
    
    tfsa_growth = account_balances.get('TFSA', 0.0) * tfsa_return
    rrsp_growth = account_balances.get('RRSP', 0.0) * rrsp_return
    nonreg_growth = account_balances.get('NON_REG', 0.0) * nonreg_return
    portfolio_growth = tfsa_growth + rrsp_growth + nonreg_growth
    
    # Add growth to balances
    account_balances['TFSA'] = account_balances.get('TFSA', 0.0) + tfsa_growth
    account_balances['RRSP'] = account_balances.get('RRSP', 0.0) + rrsp_growth
    account_balances['NON_REG'] = account_balances.get('NON_REG', 0.0) + nonreg_growth
    
    # Calculate ending balances
    ending_balance = sum(account_balances.values())
    tfsa_ending = account_balances.get('TFSA', 0.0)
    rrsp_ending = account_balances.get('RRSP', 0.0)
    nonreg_ending = account_balances.get('NON_REG', 0.0)
    
    return {
        'age': age,
        'year': year,
        'phase': 'accumulation',
        'starting_balance': round(starting_balance, 2),
        'tfsa': round(tfsa_start, 2),
        'rrsp': round(rrsp_start, 2),
        'non_reg': round(nonreg_start, 2),
        'total_contributions': round(total_contributions, 2),
        'portfolio_growth': round(portfolio_growth, 2),
        'work_optional_income': 0,
        'income_needed': 0,
        'pension': 0,
        'cpp': 0,
        'oas': 0,
        'total_guaranteed_income': 0,
        'withdrawal_needed': 0,
        'life_event': round(total_life_event_impact, 2),
        'taxes': 0,
        'ending_balance': round(max(0, ending_balance), 2),
        'tfsa_ending': round(tfsa_ending, 2),
        'rrsp_ending': round(rrsp_ending, 2),
        'non_reg_ending': round(nonreg_ending, 2),
    }


def run_accumulation_phase(
    plan: RetirementPlan,
    accounts: List[InvestmentAccount],
    years_to_retirement: int,
    preprocessed_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Run the complete accumulation phase from current age to retirement age.
    
    INPUTS:
        plan: RetirementPlan object containing user inputs
        accounts: List[InvestmentAccount objects
        years_to_retirement: int - Number of years until retirement
        preprocessed_data: Dict from preprocessing layer containing:
            - 'account_data': Dict with balances, contributions, returns
            - 'inflation_rate': float - Inflation rate as decimal
            - Other preprocessed assumptions
    
    OUTPUTS:
        List[Dict[str, Any]] - Year-by-year breakdown of accumulation phase
        Each dict contains the same structure as simulate_accumulation_year()
        
    PROCESS:
        For each year from current age to retirement age:
            1. Simulate accumulation for that year
            2. Update account balances for next year
            3. Store year data in breakdown
    """
    breakdown = []
    current_year = 2025  # Base year
    
    # Extract preprocessed data
    account_data = preprocessed_data['account_data']
    account_balances = account_data['account_balances'].copy()
    account_contributions = account_data['account_contributions']
    account_returns = account_data['account_returns']
    inflation_rate = preprocessed_data['inflation_rate']
    
    # Get life events
    life_events = list(plan.life_events.all())
    
    # Simulate each year until retirement
    for year_idx in range(years_to_retirement):
        age = plan.current_age + year_idx
        year = current_year + year_idx
        
        # Simulate this year
        year_data = simulate_accumulation_year(
            account_balances=account_balances,
            account_contributions=account_contributions,
            account_returns=account_returns,
            life_events=life_events,
            age=age,
            inflation_rate=inflation_rate,
            year=year
        )
        
        # Update balances for next iteration (balances are modified in place)
        account_balances['TFSA'] = year_data['tfsa_ending']
        account_balances['RRSP'] = year_data['rrsp_ending']
        account_balances['NON_REG'] = year_data['non_reg_ending']
        
        breakdown.append(year_data)
    
    return breakdown


def get_projected_savings_at_retirement(
    accumulation_breakdown: List[Dict[str, Any]],
    years_to_retirement: int
) -> float:
    """
    Extract projected savings at retirement from accumulation breakdown.
    
    INPUTS:
        accumulation_breakdown: List[Dict] - Year-by-year accumulation data
        years_to_retirement: int - Number of years until retirement
    
    OUTPUTS:
        float - Projected total savings at retirement age (starting balance)
        
    NOTE:
        Uses starting_balance of retirement year (what you HAVE at retirement)
        Not ending_balance (which is after first year's growth and withdrawal)
    """
    if years_to_retirement <= 0 or not accumulation_breakdown:
        return 0.0
    
    # Get the last year of accumulation (the year you reach retirement age)
    retirement_year_data = accumulation_breakdown[years_to_retirement - 1]
    return retirement_year_data['starting_balance']


def get_account_balances_at_retirement(
    accumulation_breakdown: List[Dict[str, Any]],
    years_to_retirement: int
) -> Dict[str, float]:
    """
    Extract account balances at retirement from accumulation breakdown.
    
    INPUTS:
        accumulation_breakdown: List[Dict] - Year-by-year accumulation data
        years_to_retirement: int - Number of years until retirement
    
    OUTPUTS:
        Dict[str, float] - Account balances at retirement
            Format: {'TFSA': 200000.0, 'RRSP': 300000.0, 'NON_REG': 100000.0}
    """
    if years_to_retirement <= 0 or not accumulation_breakdown:
        return {'TFSA': 0.0, 'RRSP': 0.0, 'NON_REG': 0.0}
    
    # Get the last year of accumulation
    retirement_year_data = accumulation_breakdown[years_to_retirement - 1]
    
    return {
        'TFSA': retirement_year_data.get('tfsa_ending', 0.0),
        'RRSP': retirement_year_data.get('rrsp_ending', 0.0),
        'NON_REG': retirement_year_data.get('non_reg_ending', 0.0),
    }


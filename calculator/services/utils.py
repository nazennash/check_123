from typing import List, Dict, Any
from api.models import LifeEvent


def calculate_life_event_impact(
    life_events: List[LifeEvent],
    age: int,
    inflation_rate: float,
    years_since_retirement: int
) -> Dict[str, float]:
    """
    Calculate the net impact of life events for a given age.
    
    INPUTS:
        life_events: List[LifeEvent] - Life events to process
        age: int - Current age
        inflation_rate: float - Annual inflation rate as decimal
        years_since_retirement: int - Years since retirement started
    
    OUTPUTS:
        Dict[str, float] - Net impact by account type
            Format: {'TFSA': 1000.0, 'RRSP': -5000.0, 'NON_REG': 0.0}
    """
    impacts = {'TFSA': 0.0, 'RRSP': 0.0, 'NON_REG': 0.0}
    
    for event in life_events:
        if event.start_age <= age <= event.end_age:
            amount = float(event.amount) / 100
            
            if event.frequency == 'one_time' and age == event.start_age:
                impact = amount
            elif event.frequency == 'monthly':
                impact = amount * 12
            elif event.frequency == 'annually':
                impact = amount
            else:
                impact = 0.0
            
            if event.event_type == 'expenses':
                impact = -impact
            
            account_type = event.account.upper() if event.account else 'NON_REG'
            if account_type in ['TFSA', 'RRSP', 'NON_REG']:
                impacts[account_type] += impact
    
    return impacts


def apply_withdrawal_strategy(
    strategy: str,
    withdrawal_needed: float,
    account_balances: Dict[str, float]
) -> None:
    """
    Apply withdrawal strategy to account balances (modifies in place).
    
    INPUTS:
        strategy: str - Withdrawal strategy name
        withdrawal_needed: float - Amount needed to withdraw
        account_balances: Dict[str, float] - Account balances (modified in place)
    
    WITHDRAWAL STRATEGIES:
        - 'optimized': NON_REG → RRSP → TFSA (preserves TFSA)
        - 'rrsp': RRSP → NON_REG → TFSA
        - 'non_registered': NON_REG → TFSA → RRSP
        - 'tfsa': TFSA → NON_REG → RRSP
    """
    if withdrawal_needed <= 0:
        return
    
    withdrawal_strategies = {
        'optimized': ['NON_REG', 'RRSP', 'TFSA'],
        'rrsp': ['RRSP', 'NON_REG', 'TFSA'],
        'non_registered': ['NON_REG', 'TFSA', 'RRSP'],
        'tfsa': ['TFSA', 'NON_REG', 'RRSP'],
    }
    
    withdrawal_order = withdrawal_strategies.get(strategy.lower(), ['NON_REG', 'RRSP', 'TFSA'])
    remaining_withdrawal = withdrawal_needed
    
    for account_type in withdrawal_order:
        if remaining_withdrawal <= 0:
            break
        
        balance = account_balances.get(account_type, 0.0)
        if balance > 0:
            withdrawal_amount = min(balance, remaining_withdrawal)
            account_balances[account_type] = balance - withdrawal_amount
            remaining_withdrawal -= withdrawal_amount


def calculate_inflated_income_need(
    yearly_income_goal: float,
    inflation_rate: float,
    years_to_retirement: int,
    years_since_retirement: int
) -> float:
    """
    Calculate inflated income need for a specific retirement year.
    
    INPUTS:
        yearly_income_goal: float - Income goal in today's dollars
        inflation_rate: float - Annual inflation rate as decimal
        years_to_retirement: int - Years until retirement
        years_since_retirement: int - Years since retirement started
    
    OUTPUTS:
        float - Inflated income need for that retirement year
    """
    total_years = years_to_retirement + years_since_retirement
    return yearly_income_goal * ((1 + inflation_rate) ** total_years)


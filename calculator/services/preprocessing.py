"""
PRE-PROCESSING LAYER
===================

This module handles all pre-processing tasks that prepare data and assumptions
before running retirement calculations. It processes CPP/OAS adjustments, 
inflation assumptions, return assumptions, and withdrawal strategy settings.

The Pre-Processing Layer ensures all assumptions are properly calculated and
formatted before being passed to the Accumulation Engine and Withdrawal Engine.

INPUTS: Raw user data from RetirementPlan, InvestmentAccount, and LifeEvent models
OUTPUTS: Processed assumptions and adjusted values ready for calculations

LAYER FUNCTIONS:
1. CPP/OAS Adjustment Processing
2. Pension Calculations with Indexing
3. Inflation Assumption Processing
4. Return Assumption Processing
5. Withdrawal Strategy Configuration
6. Event Preprocessing
7. Account Data Preparation
8. Comprehensive Pre-processing
"""

from typing import List, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime
from api.models import BasicInformation, InvestmentAccount, LifeEvent


# ============================================================================
# CONSTANTS AND CONFIGURATION
# ============================================================================

# Investment Profile Return Assumptions
PROFILE_RETURNS = {
    'conservative': 0.02,  # 2% annual return
    'balanced': 0.05,      # 5% annual return
    'growth': 0.10,        # 10% annual return
}

# Withdrawal Strategy Configuration
WITHDRAWAL_STRATEGIES = {
    'optimized': ['NON_REG', 'RRSP', 'TFSA'],  # Preserves TFSA
    'rrsp': ['RRSP', 'NON_REG', 'TFSA'],
    'non_registered': ['NON_REG', 'TFSA', 'RRSP'],
    'tfsa': ['TFSA', 'NON_REG', 'RRSP'],
}

# Default Assumptions
DEFAULT_INFLATION_RATE = 0.025  # 2.5%
DEFAULT_RETURN_AFTER_RETIREMENT = 0.04  # 4%
DEFAULT_PENSION_INDEXING_RATE = 0.015  # 1.5%


# ============================================================================
# 1. CPP/OAS ADJUSTMENT PROCESSING
# ============================================================================

def calculate_cpp_adjustment(basic_info: BasicInformation) -> Dict[str, Any]:
    """
    Calculate CPP amount adjusted for early/late start age.
    
    BUSINESS RULES:
        - Standard CPP age: 65
        - Early start (before 65): 0.6% reduction per month before 65
          Maximum reduction: 36% at age 60
        - Late start (after 65): 0.7% increase per month after 65
          Maximum increase: 42% at age 70
    
    RETURNS: Dictionary with CPP adjustment details
    """
    cpp_base = float(basic_info.cpp_amount_at_age) / 100 if basic_info.cpp_amount_at_age else 0.0
    start_age = basic_info.cpp_start_age if basic_info.cpp_start_age else 65
    adjustment_factor = 1.0
    adjustment_type = "standard"
    
    if start_age < 65:
        # Early start: reduce by 0.6% per month
        months_early = (65 - start_age) * 12
        reduction = min(0.006 * months_early, 0.36)  # Cap at 36%
        adjustment_factor = 1 - reduction
        adjustment_type = "early"
    elif start_age > 65:
        # Late start: increase by 0.7% per month
        months_late = (start_age - 65) * 12
        increase = min(0.007 * months_late, 0.42)  # Cap at 42%
        adjustment_factor = 1 + increase
        adjustment_type = "late"
    
    adjusted_amount = cpp_base * adjustment_factor
    
    return {
        'base_amount': cpp_base,
        'start_age': start_age,
        'adjusted_amount': adjusted_amount,
        'adjustment_factor': adjustment_factor,
        'adjustment_type': adjustment_type,
        'start_year': start_age - basic_info.current_age if start_age > basic_info.current_age else 0
    }


def calculate_oas_adjustment(basic_info: BasicInformation) -> Dict[str, Any]:
    """
    Calculate OAS amount adjusted for late start age.
    
    BUSINESS RULES:
        - Standard OAS age: 65
        - OAS cannot be taken early (before 65)
        - Late start (after 65): 0.6% increase per month after 65
          Maximum increase: 36% at age 70
    
    RETURNS: Dictionary with OAS adjustment details
    """
    oas_base = float(basic_info.oas_amount_at_OAS_age) / 100 if basic_info.oas_amount_at_OAS_age else 0.0
    start_age = max(basic_info.oas_start_age if basic_info.oas_start_age else 65, 65)  # Cannot start before 65
    adjustment_factor = 1.0
    adjustment_type = "standard"
    
    if start_age > 65:
        # Late start: increase by 0.6% per month
        months_late = (start_age - 65) * 12
        increase = min(0.006 * months_late, 0.36)  # Cap at 36%
        adjustment_factor = 1 + increase
        adjustment_type = "late"
    
    adjusted_amount = oas_base * adjustment_factor
    
    return {
        'base_amount': oas_base,
        'start_age': start_age,
        'adjusted_amount': adjusted_amount,
        'adjustment_factor': adjustment_factor,
        'adjustment_type': adjustment_type,
        'start_year': start_age - basic_info.current_age if start_age > basic_info.current_age else 0
    }


# ============================================================================
# 2. PENSION CALCULATIONS WITH INDEXING
# ============================================================================

def calculate_pension_with_indexing(basic_info: BasicInformation) -> Dict[str, Any]:
    """
    Calculate pension amounts with indexing rules applied.
    
    BUSINESS RULES:
        - Indexing starts at pension start age
        - Annual indexing based on DEFAULT_PENSION_INDEXING_RATE (1.5%)
        - Returns indexed amounts for each retirement year
    
    RETURNS: Dictionary with pension calculation details
    """
    if not basic_info.has_work_pension or not basic_info.has_work_pension.has_pension:
        return {
            'has_pension': False,
            'base_amount': 0.0,
            'indexing_rate': 0.0,
            'start_age': 0,
            'indexed_amounts': {}
        }
    
    pension = basic_info.has_work_pension
    base_amount = float(pension.monthly_pension_amount) / 100 * 12 if pension.monthly_pension_amount else 0.0
    indexing_rate = DEFAULT_PENSION_INDEXING_RATE
    start_age = pension.pension_start_age if pension.pension_start_age else 65
    
    # Calculate start year relative to current age
    start_year = max(0, start_age - basic_info.current_age)
    
    # Pre-calculate indexed amounts for first 30 years of retirement
    indexed_amounts = {}
    for year_offset in range(0, 31):  # Up to 30 years of retirement
        if year_offset >= start_year:
            years_of_indexing = year_offset - start_year
            indexed_amount = base_amount * ((1 + indexing_rate) ** years_of_indexing)
            indexed_amounts[year_offset] = indexed_amount
    
    return {
        'has_pension': True,
        'base_amount': base_amount,
        'indexing_rate': indexing_rate,
        'start_age': start_age,
        'start_year': start_year,
        'indexed_amounts': indexed_amounts
    }


# ============================================================================
# 3. INFLATION ASSUMPTION PROCESSING
# ============================================================================

def process_inflation_assumptions(basic_info: BasicInformation) -> Dict[str, Any]:
    """
    Process and setup global inflation assumptions.
    
    RETURNS: Dictionary with inflation configuration
    """
    inflation_rate = float(basic_info.inflation_rate) / 100 if basic_info.inflation_rate else DEFAULT_INFLATION_RATE
    
    return {
        'annual_rate': inflation_rate,
        'monthly_rate': ((1 + inflation_rate) ** (1/12)) - 1,
        'compounding_factor': 1 + inflation_rate
    }


def apply_inflation_to_amount(
    base_amount: float,
    inflation_rate: float,
    years: int,
    monthly: bool = False
) -> float:
    """
    Apply inflation to an amount over a specified number of years/months.
    
    FORMULA:
        Future amount = Base amount × (1 + inflation_rate)^periods
    """
    if monthly:
        periods = years * 12
        monthly_rate = ((1 + inflation_rate) ** (1/12)) - 1
        return base_amount * ((1 + monthly_rate) ** periods)
    else:
        return base_amount * ((1 + inflation_rate) ** years)


def calculate_inflation_adjusted_series(
    base_amount: float,
    inflation_rate: float,
    start_year: int,
    end_year: int
) -> Dict[int, float]:
    """
    Calculate inflation-adjusted amounts for a series of years.
    
    RETURNS: Dictionary mapping year offset to inflated amount
    """
    adjusted_series = {}
    
    for year in range(start_year, end_year + 1):
        if year >= start_year:
            adjusted_series[year] = apply_inflation_to_amount(base_amount, inflation_rate, year)
    
    return adjusted_series


# ============================================================================
# 4. RETURN ASSUMPTION PROCESSING
# ============================================================================

def get_account_return_profile(account: InvestmentAccount) -> Dict[str, Any]:
    """
    Get the expected return profile for a specific investment account.
    """
    profile = account.investment_profile.lower() if account.investment_profile else 'balanced'
    expected_return = PROFILE_RETURNS.get(profile, 0.05)  # Default to balanced
    
    return {
        'profile': profile,
        'expected_return': expected_return,
        'is_conservative': profile == 'conservative',
        'is_growth': profile == 'growth'
    }


def calculate_weighted_portfolio_return(accounts: List[InvestmentAccount]) -> Dict[str, Any]:
    """
    Calculate weighted average return based on account balances and investment profiles.
    
    BUSINESS RULES:
        - Weight by account balances
        - If no balances, weight by contributions
        - Default to 5% if no data
    """
    # Calculate total balance
    total_balance = sum(float(acc.balance) for acc in accounts)
    
    if total_balance > 0:
        # Weight by balances (convert from cents to dollars)
        weighted_return = sum(
            (float(acc.balance) / 100) * get_account_return_profile(acc)['expected_return']
            for acc in accounts
        ) / total_balance
        
        # Calculate contribution weights for reference (convert from cents to dollars)
        total_contribution = sum((float(acc.monthly_contribution) / 100) for acc in accounts if acc.monthly_contribution)
        contribution_weights = {}
        for acc in accounts:
            if total_contribution > 0 and acc.monthly_contribution:
                weight = (float(acc.monthly_contribution) / 100) / total_contribution
                acc_type = acc.account_type.upper() if acc.account_type else 'NON_REG'
                contribution_weights[acc_type] = weight
        
        return {
            'weighted_return': weighted_return,
            'total_balance': total_balance,
            'weighting_method': 'balance',
            'contribution_weights': contribution_weights,
            'account_count': len(accounts)
        }
    else:
        # Weight by contributions (convert from cents to dollars)
        total_contribution = sum((float(acc.monthly_contribution) / 100) for acc in accounts if acc.monthly_contribution)
        
        if total_contribution > 0:
            weighted_return = sum(
                (float(acc.monthly_contribution) / 100) * get_account_return_profile(acc)['expected_return']
                for acc in accounts if acc.monthly_contribution
            ) / total_contribution
            
            return {
                'weighted_return': weighted_return,
                'total_balance': total_balance,
                'weighting_method': 'contribution',
                'contribution_weights': {(acc.account_type.upper() if acc.account_type else 'NON_REG'): (float(acc.monthly_contribution) / 100)/total_contribution for acc in accounts if acc.monthly_contribution},
                'account_count': len(accounts)
            }
        else:
            # Default to balanced profile
            return {
                'weighted_return': 0.05,
                'total_balance': 0.0,
                'weighting_method': 'default',
                'contribution_weights': {},
                'account_count': len(accounts)
            }


def process_return_after_retirement(basic_info: BasicInformation) -> Dict[str, Any]:
    """
    Process return assumptions for the retirement phase.
    """
    return_rate = float(basic_info.return_after_work_optional) / 100 if basic_info.return_after_work_optional else DEFAULT_RETURN_AFTER_RETIREMENT
    
    return {
        'annual_return': return_rate,
        'monthly_return': ((1 + return_rate) ** (1/12)) - 1,
        'is_conservative': return_rate < 0.05,
        'is_growth': return_rate >= 0.07
    }


# ============================================================================
# 5. WITHDRAWAL STRATEGY CONFIGURATION
# ============================================================================

def configure_withdrawal_strategy(basic_info: BasicInformation) -> Dict[str, Any]:
    """
    Load and configure withdrawal strategy settings.
    
    RETURNS: Complete withdrawal strategy configuration
    """
    strategy = basic_info.withdrawal_strategy.lower() if basic_info.withdrawal_strategy else 'optimized'
    withdrawal_order = WITHDRAWAL_STRATEGIES.get(strategy, WITHDRAWAL_STRATEGIES['optimized'])
    
    # Get withdrawal rate (as decimal) - default 4%
    withdrawal_rate = 0.04
    
    # Get withdrawal limits if specified
    floor_amount = 0.0
    ceiling_amount = None
    
    # Additional strategy parameters
    dynamic_adjustment = False
    guardrail_threshold = 0.2  # 20% threshold
    
    return {
        'strategy_name': strategy,
        'withdrawal_order': withdrawal_order,
        'withdrawal_rate': withdrawal_rate,
        'floor_amount': floor_amount,
        'ceiling_amount': ceiling_amount,
        'dynamic_adjustment': dynamic_adjustment,
        'guardrail_threshold': guardrail_threshold,
        'annual_withdrawal_sequence': generate_withdrawal_sequence(strategy, withdrawal_rate),
        'description': get_strategy_description(strategy)
    }


def generate_withdrawal_sequence(strategy: str, withdrawal_rate: float) -> List[Dict[str, Any]]:
    """
    Generate annual withdrawal sequence based on strategy.
    """
    order = WITHDRAWAL_STRATEGIES.get(strategy, WITHDRAWAL_STRATEGIES['optimized'])
    
    sequence = []
    for position, account_type in enumerate(order, 1):
        sequence.append({
            'step': position,
            'account_type': account_type,
            'priority': position,
            'max_percentage': 1.0 if position == 1 else 0.0,  # First in order gets full withdrawal
            'conditions': get_withdrawal_conditions(account_type, position)
        })
    
    return sequence


def get_withdrawal_conditions(account_type: str, priority: int) -> Dict[str, Any]:
    """
    Get conditions for withdrawing from a specific account type.
    """
    conditions = {
        'RRSP': {
            'min_age': 65,  # Could be earlier with penalty
            'max_age': 71,  # Must convert to RRIF
            'tax_implications': True,
            'mandatory_withdrawal': priority == 1  # If RRSP first, mandatory
        },
        'TFSA': {
            'min_age': 18,
            'max_age': None,
            'tax_implications': False,
            'penalty_free': True
        },
        'NON_REG': {
            'min_age': 0,
            'max_age': None,
            'tax_implications': True,  # Capital gains
            'preferred_for_estate': False
        }
    }
    
    return conditions.get(account_type, {})


def get_strategy_description(strategy: str) -> str:
    """
    Get description for each withdrawal strategy.
    """
    descriptions = {
        'optimized': "Preserves TFSA by withdrawing from Non-Registered accounts first, then RRSP, then TFSA. Optimizes for tax efficiency and estate planning.",
        'rrsp': "Withdraws from RRSP first to reduce mandatory withdrawals later. May increase tax burden in early retirement.",
        'non_registered': "Withdraws from Non-Registered accounts first to defer RRSP taxation. Good for those expecting lower future tax rates.",
        'tfsa': "Withdraws from TFSA first to preserve taxable accounts. Useful for those needing maximum flexibility."
    }
    
    return descriptions.get(strategy.lower(), descriptions['optimized'])


# ============================================================================
# 6. EVENT PREPROCESSING
# ============================================================================

def preprocess_life_events(basic_info: BasicInformation) -> List[Dict[str, Any]]:
    """
    Preprocess life events for the calculation engine.
    
    TAGS each event with:
    - year_of_effect: Year when event occurs (relative to current age)
    - amount: Dollar amount
    - type: 'income' or 'expense'
    - account_affected: Which account is impacted
    - description: Event description
    - is_recurring: Whether event repeats
    - duration_years: How long event lasts
    
    RETURNS: List of processed events
    """
    processed_events = []
    
    # Get events from basic_info
    events = basic_info.life_events.all()
    
    for event in events:
        # Calculate year of effect relative to current age
        year_of_effect = event.start_age - basic_info.current_age
        
        # Determine event type
        event_type = 'expenses' if event.event_type == 'expenses' else 'contribution'
        
        # Process event data
        amount_cents = float(event.amount) if event.amount else 0.0
        amount_dollars = amount_cents / 100
        
        processed_event = {
            'id': event.id,
            'year_of_effect': max(0, year_of_effect),
            'amount': amount_dollars,
            'type': event_type,
            'account_affected': event.account.upper() if event.account else 'NON_REG',
            'description': event.name if event.name else 'Life Event',
            'is_recurring': event.frequency != 'one_time',
            'duration_years': max(1, event.end_age - event.start_age) if event.end_age > event.start_age else 1,
            'inflation_adjusted': True,
            'tax_implications': False,
            'category': 'other',
            'priority': 'medium',
            'frequency': event.frequency,
            'start_age': event.start_age,
            'end_age': event.end_age
        }
        
        # Adjust for inflation if needed
        if processed_event['inflation_adjusted'] and processed_event['year_of_effect'] > 0:
            inflation_config = process_inflation_assumptions(basic_info)
            processed_event['future_value'] = apply_inflation_to_amount(
                processed_event['amount'],
                inflation_config['annual_rate'],
                processed_event['year_of_effect']
            )
        else:
            processed_event['future_value'] = processed_event['amount']
        
        processed_events.append(processed_event)
    
    # Sort events by year of effect
    processed_events.sort(key=lambda x: x['year_of_effect'])
    
    return processed_events


def categorize_events_by_year(events: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    """
    Categorize events by the year they occur.
    
    RETURNS: Dictionary mapping year to list of events in that year
    """
    events_by_year = {}
    
    for event in events:
        year = event['year_of_effect']
        if year not in events_by_year:
            events_by_year[year] = []
        
        events_by_year[year].append(event)
    
    return events_by_year


# ============================================================================
# 7. ACCOUNT DATA PREPARATION
# ============================================================================

def prepare_account_data(accounts: List[InvestmentAccount]) -> Dict[str, Any]:
    """
    Prepare comprehensive account data structures for calculations.
    
    RETURNS: Dictionary with all account data organized by type
    """
    # Initialize account structures
    account_balances = {'TFSA': 0.0, 'RRSP': 0.0, 'NON_REG': 0.0}
    account_contributions = {'TFSA': 0.0, 'RRSP': 0.0, 'NON_REG': 0.0}
    account_returns = {'TFSA': 0.05, 'RRSP': 0.05, 'NON_REG': 0.05}
    account_profiles = {'TFSA': 'balanced', 'RRSP': 'balanced', 'NON_REG': 'balanced'}
    
    # Track individual accounts
    individual_accounts = []
    
    # Populate from accounts
    for acc in accounts:
        acc_type = acc.account_type.upper() if acc.account_type else 'NON_REG'
        if acc_type in ['TFSA', 'RRSP', 'NON_REG', 'NON_REGISTERED']:
            if acc_type == 'NON_REGISTERED':
                acc_type = 'NON_REG'
            
            # Basic account data (convert from cents to dollars)
            account_balances[acc_type] = float(acc.balance) / 100
            monthly_contrib = float(acc.monthly_contribution) / 100 if acc.monthly_contribution else 0.0
            account_contributions[acc_type] = monthly_contrib * 12  # Annual
            
            # Return profile
            profile_data = get_account_return_profile(acc)
            account_returns[acc_type] = profile_data['expected_return']
            account_profiles[acc_type] = acc.investment_profile
            
            # Individual account details
            individual_accounts.append({
                'id': acc.id,
                'name': f"{acc_type} Account",
                'type': acc_type,
                'balance': account_balances[acc_type],
                'annual_contribution': account_contributions[acc_type],
                'investment_profile': acc.investment_profile if acc.investment_profile else 'balanced',
                'expected_return': profile_data['expected_return'],
                'institution': 'Unknown',
                'account_number': '',
                'is_active': True
            })
    
    # Calculate totals
    total_balance = sum(account_balances.values())
    total_annual_contribution = sum(account_contributions.values())
    
    # Calculate allocation percentages
    allocation_percentages = {}
    if total_balance > 0:
        for acc_type, balance in account_balances.items():
            allocation_percentages[acc_type] = (balance / total_balance) * 100
    
    return {
        'account_balances': account_balances,
        'account_contributions': account_contributions,
        'account_returns': account_returns,
        'account_profiles': account_profiles,
        'allocation_percentages': allocation_percentages,
        'individual_accounts': individual_accounts,
        'total_balance': total_balance,
        'total_annual_contribution': total_annual_contribution,
        'account_count': len(accounts)
    }


# ============================================================================
# 8. COMPREHENSIVE PRE-PROCESSING FUNCTION
# ============================================================================

def preprocess_retirement_plan(
    basic_info: BasicInformation,
    accounts: List[InvestmentAccount],
    events: List[Any] = None
) -> Dict[str, Any]:
    """
    Comprehensive pre-processing function that prepares all assumptions and data.
    
    This is the main entry point for the Pre-Processing Layer.
    It processes all inputs and returns a complete dictionary of processed assumptions.
    
    RETURNS: Comprehensive dictionary with all processed data
    """
    # Calculate time periods
    current_year = datetime.now().year
    work_optional_age = basic_info.work_optional_age if basic_info.work_optional_age else basic_info.current_age + 30
    plan_until_age = basic_info.plan_until_age if basic_info.plan_until_age else 90
    years_to_retirement = max(0, work_optional_age - basic_info.current_age)
    years_in_retirement = max(0, plan_until_age - work_optional_age)
    
    # 1. Process government benefits
    cpp_data = calculate_cpp_adjustment(basic_info)
    oas_data = calculate_oas_adjustment(basic_info)
    
    # 2. Process pension with indexing
    pension_data = calculate_pension_with_indexing(basic_info)
    
    # 3. Process inflation assumptions
    inflation_data = process_inflation_assumptions(basic_info)
    
    # 4. Process return assumptions
    weighted_return_data = calculate_weighted_portfolio_return(accounts)
    post_retirement_return_data = process_return_after_retirement(basic_info)
    
    # 5. Configure withdrawal strategy
    withdrawal_config = configure_withdrawal_strategy(basic_info)
    
    # 6. Preprocess life events
    if events is None:
        events_data = preprocess_life_events(basic_info)
    else:
        # Use provided events
        events_data = events
    
    events_by_year = categorize_events_by_year(events_data)
    
    # 7. Prepare account data
    account_data = prepare_account_data(accounts)
    
    # 8. Calculate base income needs (inflation adjusted)
    yearly_income_goal = float(basic_info.yearly_income_for_ideal_lifestyle) / 100 if basic_info.yearly_income_for_ideal_lifestyle else 0.0
    
    # Calculate income needs for each retirement year
    retirement_income_needs = {}
    for year in range(years_in_retirement + 1):
        inflated_amount = apply_inflation_to_amount(
            yearly_income_goal,
            inflation_data['annual_rate'],
            years_to_retirement + year
        )
        retirement_income_needs[year] = inflated_amount
    
    # 9. Compile all data
    preprocessed_data = {
        # Time and age data
        'current_age': basic_info.current_age,
        'retirement_age': work_optional_age,
        'life_expectancy': plan_until_age,
        'years_to_retirement': years_to_retirement,
        'years_in_retirement': years_in_retirement,
        'calculation_horizon': years_to_retirement + years_in_retirement,
        'current_year': current_year,
        
        # Government benefits
        'cpp': cpp_data,
        'oas': oas_data,
        'cpp_adjusted': cpp_data['adjusted_amount'],
        'oas_adjusted': oas_data['adjusted_amount'],
        
        # Pension data
        'pension': pension_data,
        'pension_amount': pension_data['base_amount'] if pension_data['has_pension'] else 0.0,
        
        # Inflation data
        'inflation': inflation_data,
        'inflation_rate': inflation_data['annual_rate'],
        
        # Return assumptions
        'accumulation_returns': weighted_return_data,
        'retirement_returns': post_retirement_return_data,
        'return_after_retirement': post_retirement_return_data['annual_return'],
        
        # Withdrawal strategy
        'withdrawal_strategy': withdrawal_config,
        
        # Life events
        'life_events': events_data,
        'events_by_year': events_by_year,
        
        # Account data
        'accounts': account_data,
        'account_data': account_data,
        
        # Income needs
        'yearly_income_goal': yearly_income_goal,
        'retirement_income_needs': retirement_income_needs,
        
        # Additional plan data
        'has_spouse': False,
        'spouse_age': None,
        'retirement_location': 'Canada',
        'risk_tolerance': 'moderate',
        'estate_planning_goal': 'preserve_capital',
        
        # Metadata
        'preprocessing_timestamp': datetime.now().isoformat(),
        'plan_id': basic_info.user_id,
        'plan_name': 'Retirement Plan',
        'user_id': basic_info.user_id,
        'client_id': basic_info.client_id
    }
    
    # Add summary statistics
    preprocessed_data['summary'] = generate_preprocessing_summary(preprocessed_data)
    
    return preprocessed_data


def generate_preprocessing_summary(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a summary of the preprocessed data.
    """
    # Calculate total guaranteed income in retirement
    guaranteed_income = 0
    if data['cpp']['adjusted_amount'] > 0:
        guaranteed_income += data['cpp']['adjusted_amount']
    if data['oas']['adjusted_amount'] > 0:
        guaranteed_income += data['oas']['adjusted_amount']
    if data['pension']['has_pension'] and data['pension']['base_amount'] > 0:
        guaranteed_income += data['pension']['base_amount']
    
    # Calculate income gap
    first_year_income_need = data['retirement_income_needs'].get(0, 0)
    income_gap = max(0, first_year_income_need - guaranteed_income)
    
    # Calculate required savings rate
    years_to_retirement = data['years_to_retirement']
    expected_return = data['accumulation_returns']['weighted_return']
    future_value_factor = ((1 + expected_return) ** years_to_retirement)
    
    # Approximate required nest egg (using 4% rule for simplicity)
    required_nest_egg = income_gap / 0.04 if income_gap > 0 else 0
    
    return {
        'total_savings': data['accounts']['total_balance'],
        'total_annual_contributions': data['accounts']['total_annual_contribution'],
        'guaranteed_annual_income': guaranteed_income,
        'first_year_income_need': first_year_income_need,
        'annual_income_gap': income_gap,
        'required_nest_egg': required_nest_egg,
        'current_progress': (data['accounts']['total_balance'] / required_nest_egg * 100) if required_nest_egg > 0 else 100,
        'average_return': data['accumulation_returns']['weighted_return'],
        'inflation_rate': data['inflation']['annual_rate'],
        'withdrawal_strategy': data['withdrawal_strategy']['strategy_name'],
        'life_event_count': len(data['life_events']),
        'account_count': data['accounts']['account_count']
    }


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================

def validate_preprocessed_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate the preprocessed data for consistency and completeness.
    
    RETURNS: Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Check required fields
    required_fields = [
        'years_to_retirement', 'years_in_retirement',
        'inflation', 'accounts', 'withdrawal_strategy',
        'cpp', 'oas', 'pension'
    ]
    
    for field in required_fields:
        if field not in data:
            issues.append(f"Missing required field: {field}")
    
    # Validate numeric ranges
    if data.get('inflation', {}).get('annual_rate', 0) > 0.10:  # > 10%
        issues.append("Inflation rate unusually high (>10%)")
    
    if data.get('accumulation_returns', {}).get('weighted_return', 0) > 0.15:  # > 15%
        issues.append("Expected return unusually high (>15%)")
    
    if data.get('years_in_retirement', 0) > 50:
        issues.append("Retirement period unusually long (>50 years)")
    
    # Check account balances
    if data.get('accounts', {}).get('total_balance', 0) < 0:
        issues.append("Negative total account balance")
    
    # Check withdrawal rate
    withdrawal_rate = data.get('withdrawal_strategy', {}).get('withdrawal_rate', 0)
    if withdrawal_rate > 0.10:  # > 10%
        issues.append(f"Withdrawal rate unusually high: {withdrawal_rate*100:.1f}%")
    
    return len(issues) == 0, issues


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_preprocessing_report(data: Dict[str, Any]) -> str:
    """
    Generate a human-readable report of the preprocessing results.
    """
    summary = data.get('summary', {})
    
    report_lines = [
        "=" * 60,
        "PRE-PROCESSING LAYER REPORT",
        "=" * 60,
        f"Plan: {data.get('plan_name', 'Unknown')}",
        f"Processed: {data.get('preprocessing_timestamp', 'Unknown')}",
        "",
        "TIME HORIZONS:",
        f"  Current Age: {data.get('current_age', 0)}",
        f"  Retirement Age: {data.get('retirement_age', 0)}",
        f"  Years to Retirement: {data.get('years_to_retirement', 0)}",
        f"  Years in Retirement: {data.get('years_in_retirement', 0)}",
        "",
        "FINANCIAL SNAPSHOT:",
        f"  Current Savings: ${summary.get('total_savings', 0):,.2f}",
        f"  Annual Contributions: ${summary.get('total_annual_contributions', 0):,.2f}",
        f"  Guaranteed Income: ${summary.get('guaranteed_annual_income', 0):,.2f}/year",
        "",
        "INCOME NEEDS:",
        f"  First Year Need: ${summary.get('first_year_income_need', 0):,.2f}",
        f"  Annual Gap: ${summary.get('annual_income_gap', 0):,.2f}",
        f"  Required Nest Egg: ${summary.get('required_nest_egg', 0):,.2f}",
        f"  Current Progress: {summary.get('current_progress', 0):.1f}%",
        "",
        "ASSUMPTIONS:",
        f"  Expected Return: {summary.get('average_return', 0)*100:.1f}%",
        f"  Inflation Rate: {summary.get('inflation_rate', 0)*100:.1f}%",
        f"  Withdrawal Strategy: {summary.get('withdrawal_strategy', 'Unknown')}",
        "",
        f"Accounts: {summary.get('account_count', 0)}, Events: {summary.get('life_event_count', 0)}",
        "=" * 60
    ]
    
    return "\n".join(report_lines)
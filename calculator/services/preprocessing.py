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
DEFAULT_PENSION_INDEXING_RATE = 0.02  # 2%


# ============================================================================
# 1. CPP/OAS ADJUSTMENT PROCESSING
# ============================================================================

def calculate_cpp_adjustment(basic_info: BasicInformation) -> Dict[str, Any]:
    """
    Calculate CPP amount adjusted for early/late start age.
    
    BUSINESS RULES (6.1.1):
        A) If CPP start age < 65: Apply 0.6% monthly reduction
           monthsEarly = (65 - cpp_start_age) * 12
           cpp_final = cpp_at_65 * (1 - 0.006 * monthsEarly)
        B) If CPP start age > 65: Apply 0.7% monthly increase
           monthsLate = (cpp_start_age - 65) * 12
           cpp_final = cpp_at_65 * (1 + 0.007 * monthsLate)
        C) Convert to annual: cpp_annual = cpp_final * 12
    
    RETURNS: Dictionary with CPP adjustment details (annual amounts)
    """
    print("cpp adjustment")
    print("-----")
    
    # input data
    print("\n[INPUT DATA]")
    print(f"  cpp_amount_at_age (cents): {basic_info.cpp_amount_at_age}")
    print(f"  cpp_start_age: {basic_info.cpp_start_age}")
    print(f"  current_age: {basic_info.current_age}")
    
    # cpp_amount_at_age is the monthly amount at the START AGE (not necessarily 65)
    cpp_at_start_age_monthly_cents = float(basic_info.cpp_amount_at_age) if basic_info.cpp_amount_at_age else 0.0
    cpp_at_start_age_monthly = cpp_at_start_age_monthly_cents / 100
    start_age = basic_info.cpp_start_age if basic_info.cpp_start_age else 65
    
    print(f"\n[PROCESSING]")
    print(f"  CPP monthly amount at start age ({start_age}): ${cpp_at_start_age_monthly:,.2f}/month")
    print(f"  CPP start age: {start_age}")
    print(f"  Standard CPP age: 65")
    
    if start_age < 65:
        # A) Early start: user provided amount at start_age, need to calculate what it would be at 65
        # Then reduce it to get the final amount at start_age
        months_early = (65 - start_age) * 12
        print(f"\n  [A) EARLY START CALCULATION]")
        print(f"    User provided amount at age {start_age}: ${cpp_at_start_age_monthly:,.2f}/month")
        print(f"    monthsEarly = (65 - {start_age}) * 12 = {months_early} months")
        print(f"    Reduction per month: 0.6%")
        print(f"    Total reduction: 0.006 * {months_early} = {0.006 * months_early:.4f} = {0.006 * months_early * 100:.2f}%")
        
        # Calculate what it would be at 65: cpp_at_65 = cpp_at_start_age / (1 - 0.006 * monthsEarly)
        cpp_at_65_monthly = cpp_at_start_age_monthly / (1 - 0.006 * months_early)
        print(f"    Calculating amount at age 65: cpp_at_65 = ${cpp_at_start_age_monthly:,.2f} / (1 - {0.006 * months_early:.4f}) = ${cpp_at_65_monthly:,.2f}/month")
        
        # Final amount is the user-provided amount at start_age
        cpp_final_monthly = cpp_at_start_age_monthly
        adjustment_factor = 1 - 0.006 * months_early
        adjustment_type = "early"
        
        print(f"    cpp_final (monthly) at age {start_age} = ${cpp_final_monthly:,.2f}/month (user-provided amount)")
        
    elif start_age > 65:
        # B) Late start: user provided amount at start_age, need to calculate what it would be at 65
        months_late = (start_age - 65) * 12
        print(f"\n  [B) LATE START CALCULATION]")
        print(f"    User provided amount at age {start_age}: ${cpp_at_start_age_monthly:,.2f}/month")
        print(f"    monthsLate = ({start_age} - 65) * 12 = {months_late} months")
        print(f"    Increase per month: 0.7%")
        print(f"    Total increase: 0.007 * {months_late} = {0.007 * months_late:.4f} = {0.007 * months_late * 100:.2f}%")
        
        # Calculate what it would be at 65: cpp_at_65 = cpp_at_start_age / (1 + 0.007 * monthsLate)
        cpp_at_65_monthly = cpp_at_start_age_monthly / (1 + 0.007 * months_late)
        print(f"    Calculating amount at age 65: cpp_at_65 = ${cpp_at_start_age_monthly:,.2f} / (1 + {0.007 * months_late:.4f}) = ${cpp_at_65_monthly:,.2f}/month")
        
        # Final amount is the user-provided amount at start_age
        cpp_final_monthly = cpp_at_start_age_monthly
        adjustment_factor = 1 + 0.007 * months_late
        adjustment_type = "late"
        
        print(f"    cpp_final (monthly) at age {start_age} = ${cpp_final_monthly:,.2f}/month (user-provided amount)")
        
    else:
        # Start age = 65, no adjustment
        print(f"\n  [STANDARD START]")
        print(f"    Start age is 65, no adjustment needed")
        cpp_at_65_monthly = cpp_at_start_age_monthly
        cpp_final_monthly = cpp_at_start_age_monthly
        adjustment_factor = 1.0
        adjustment_type = "standard"
        print(f"    cpp_final (monthly) at age 65 = ${cpp_final_monthly:,.2f}/month (user-provided amount)")
    
    # C) Convert to annual: cpp_annual = cpp_final * 12
    cpp_annual = cpp_final_monthly * 12
    print(f"\n  [C) CONVERT TO ANNUAL]")
    print(f"    cpp_annual = cpp_final × 12")
    print(f"    cpp_annual = ${cpp_final_monthly:,.2f} × 12 = ${cpp_annual:,.2f}/year")
    
    # Calculate years until CPP starts
    start_year = start_age - basic_info.current_age if start_age > basic_info.current_age else 0
    current_year = datetime.now().year
    start_calendar_year = current_year + start_year if start_year > 0 else current_year
    
    print(f"\n  [TIMING INFORMATION]")
    print(f"    Current age: {basic_info.current_age}")
    print(f"    CPP start age: {start_age}")
    print(f"    Years until CPP starts: {start_age} - {basic_info.current_age} = {start_year} years")
    if start_year > 0:
        print(f"    CPP will start in year: {start_calendar_year} (in {start_year} years)")
    else:
        print(f"    CPP starts now (current year: {start_calendar_year})")
    
    result = {
        'base_amount': cpp_annual,  # Store annual amount
        'base_monthly': cpp_at_65_monthly,  # Store calculated monthly at 65 (for reference)
        'final_monthly': cpp_final_monthly,  # Store user-provided monthly at start_age
        'start_age': start_age,
        'adjusted_amount': cpp_annual,  # Annual adjusted amount
        'adjustment_factor': adjustment_factor,
        'adjustment_type': adjustment_type,
        'start_year': start_year,  # Years until start (not calendar year)
        'start_calendar_year': start_calendar_year  # Actual calendar year
    }
    
    print(f"\n[OUTPUT RESULTS]")
    print(f"  base_amount (annual): ${result['base_amount']:,.2f}/year")
    print(f"  base_monthly (calculated at 65): ${result['base_monthly']:,.2f}/month")
    print(f"  final_monthly (at start age {start_age}): ${result['final_monthly']:,.2f}/month")
    print(f"  start_age: {result['start_age']} years old")
    print(f"  adjusted_amount (annual): ${result['adjusted_amount']:,.2f}/year")
    print(f"  adjustment_factor: {result['adjustment_factor']:.4f}")
    print(f"  adjustment_type: {result['adjustment_type']}")
    print(f"  start_year: {result['start_year']} years from now")
    print(f"  start_calendar_year: {result['start_calendar_year']}")
    
    
    return result


def calculate_oas_adjustment(basic_info: BasicInformation) -> Dict[str, Any]:
    """
    Calculate OAS amount adjusted for late start age.
    
    BUSINESS RULES (6.1.2):
        OAS cannot start before 65.
        A) If OAS start age > 65:
           monthsLate = (oas_start_age - 65) * 12
           oas_final = oas_at_65 * (1 + 0.006 * monthsLate)
           oas_annual = oas_final * 12
        B) If OAS start age = 65:
           oas_final = oas_at_65
           oas_annual = oas_final * 12
    
    RETURNS: Dictionary with OAS adjustment details (annual amounts)
    """
    print("-----")
    print("oas adjustment")
    
    # INPUT DATA
    print("\n[INPUT DATA]")
    print(f"  oas_amount_at_OAS_age (cents): {basic_info.oas_amount_at_OAS_age}")
    print(f"  oas_start_age: {basic_info.oas_start_age}")
    print(f"  current_age: {basic_info.current_age}")
    
    # oas_amount_at_OAS_age is the monthly amount at the START AGE (not necessarily 65)
    oas_at_start_age_monthly_cents = float(basic_info.oas_amount_at_OAS_age) if basic_info.oas_amount_at_OAS_age else 0.0
    oas_at_start_age_monthly = oas_at_start_age_monthly_cents / 100
    requested_start_age = basic_info.oas_start_age if basic_info.oas_start_age else 65
    start_age = max(requested_start_age, 65)  # Cannot start before 65
    
    print(f"\n[PROCESSING]")
    print(f"  OAS monthly amount at start age ({start_age}): ${oas_at_start_age_monthly:,.2f}/month")
    print(f"  Requested OAS start age: {requested_start_age}")
    print(f"  Adjusted start age (cannot be < 65): {start_age}")
    print(f"  Standard OAS age: 65")
    
    if start_age > 65:
        # A) Late start: user provided amount at start_age, need to calculate what it would be at 65
        months_late = (start_age - 65) * 12
        print(f"\n  [A) LATE START CALCULATION]")
        print(f"    User provided amount at age {start_age}: ${oas_at_start_age_monthly:,.2f}/month")
        print(f"    monthsLate = ({start_age} - 65) * 12 = {months_late} months")
        print(f"    Increase per month: 0.6%")
        print(f"    Total increase: 0.006 * {months_late} = {0.006 * months_late:.4f} = {0.006 * months_late * 100:.2f}%")
        
        # Calculate what it would be at 65: oas_at_65 = oas_at_start_age / (1 + 0.006 * monthsLate)
        oas_at_65_monthly = oas_at_start_age_monthly / (1 + 0.006 * months_late)
        print(f"    Calculating amount at age 65: oas_at_65 = ${oas_at_start_age_monthly:,.2f} / (1 + {0.006 * months_late:.4f}) = ${oas_at_65_monthly:,.2f}/month")
        
        # Final amount is the user-provided amount at start_age
        oas_final_monthly = oas_at_start_age_monthly
        adjustment_factor = 1 + 0.006 * months_late
        adjustment_type = "late"
        
        print(f"    oas_final (monthly) at age {start_age} = ${oas_final_monthly:,.2f}/month (user-provided amount)")
        
    else:
        # B) Start age = 65, no adjustment
        print(f"\n  [B) STANDARD START]")
        print(f"    Start age is 65, no adjustment needed")
        oas_at_65_monthly = oas_at_start_age_monthly
        oas_final_monthly = oas_at_start_age_monthly
        adjustment_factor = 1.0
        adjustment_type = "standard"
        print(f"    oas_final (monthly) at age 65 = ${oas_final_monthly:,.2f}/month (user-provided amount)")
    
    # Convert to annual: oas_annual = oas_final * 12
    oas_annual = oas_final_monthly * 12
    print(f"\n  [CONVERT TO ANNUAL]")
    print(f"    oas_annual = oas_final × 12")
    print(f"    oas_annual = ${oas_final_monthly:,.2f} × 12 = ${oas_annual:,.2f}/year")
    
    # Calculate years until OAS starts
    start_year = start_age - basic_info.current_age if start_age > basic_info.current_age else 0
    current_year = datetime.now().year
    start_calendar_year = current_year + start_year if start_year > 0 else current_year
    
    print(f"\n  [TIMING INFORMATION]")
    print(f"    Current age: {basic_info.current_age}")
    print(f"    OAS start age: {start_age}")
    print(f"    Years until OAS starts: {start_age} - {basic_info.current_age} = {start_year} years")
    if start_year > 0:
        print(f"    OAS will start in year: {start_calendar_year} (in {start_year} years)")
    else:
        print(f"    OAS starts now (current year: {start_calendar_year})")
    
    result = {
        'base_amount': oas_annual,  # Store annual amount
        'base_monthly': oas_at_65_monthly,  # Store calculated monthly at 65 (for reference)
        'final_monthly': oas_final_monthly,  # Store user-provided monthly at start_age
        'start_age': start_age,
        'adjusted_amount': oas_annual,  # Annual adjusted amount
        'adjustment_factor': adjustment_factor,
        'adjustment_type': adjustment_type,
        'start_year': start_year,  # Years until start (not calendar year)
        'start_calendar_year': start_calendar_year  # Actual calendar year
    }
    
    print(f"\n[OUTPUT RESULTS]")
    print(f"  base_amount (annual): ${result['base_amount']:,.2f}/year")
    print(f"  base_monthly (calculated at 65): ${result['base_monthly']:,.2f}/month")
    print(f"  final_monthly (at start age {start_age}): ${result['final_monthly']:,.2f}/month")
    print(f"  start_age: {result['start_age']} years old")
    print(f"  adjusted_amount (annual): ${result['adjusted_amount']:,.2f}/year")
    print(f"  adjustment_factor: {result['adjustment_factor']:.4f}")
    print(f"  adjustment_type: {result['adjustment_type']}")
    print(f"  start_year: {result['start_year']} years from now")
    print(f"  start_calendar_year: {result['start_calendar_year']}")
    
    return result


# ============================================================================
# 2. PENSION CALCULATIONS WITH INDEXING
# ============================================================================

def calculate_pension_with_indexing(basic_info: BasicInformation) -> Dict[str, Any]:
    """
    Calculate pension amounts with indexing rules applied.
    
    BUSINESS RULES (6.1.3):
        A) Base annual pension:
           pension_base_annual = pension_monthly * 12
        
        B) Pension indexing (after pension starts only):
           if age < pension_start_age:
               pension_annual[age] = 0
           if age == pension_start_age:
               pension_annual[age] = pension_base_annual
           if age > pension_start_age:
               years_since_start = age - pension_start_age
               pension_annual[age] = pension_base_annual * (1 + pension_index_rate) ^ years_since_start
    
    RETURNS: Dictionary with pension calculation details
    """
    print("-----")
    print("pension indexing")
    
    
    # INPUT DATA
    print("\n[INPUT DATA]")
    work_pension = basic_info.work_pensions.first()  # Get first work pension (supports multiple now)
    print(f"  work_pensions count: {basic_info.work_pensions.count()}")
    if work_pension:
        print(f"  has_pension (flag): {work_pension.has_pension}")
        print(f"  monthly_pension_amount (cents): {work_pension.monthly_pension_amount}")
        print(f"  pension_start_age: {work_pension.pension_start_age}")
    print(f"  current_age: {basic_info.current_age}")
    print(f"  Default indexing rate: {DEFAULT_PENSION_INDEXING_RATE * 100:.2f}%")
    
    if not work_pension or not work_pension.has_pension:
        print(f"\n[PROCESSING]")
        print(f"  No pension data available, returning zeros")
        result = {
            'has_pension': False,
            'base_amount': 0.0,
            'indexing_rate': 0.0,
            'start_age': 0,
            'indexed_amounts': {}
        }
        print(f"\n[OUTPUT RESULTS]")
        print(f"  has_pension: {result['has_pension']}")
        print("-"*8)
        return result
    
    pension = work_pension  # Use the work_pension we already retrieved
    monthly_amount_cents = float(pension.monthly_pension_amount) if pension.monthly_pension_amount else 0.0
    monthly_amount_dollars = monthly_amount_cents / 100
    indexing_rate = DEFAULT_PENSION_INDEXING_RATE
    start_age = pension.pension_start_age if pension.pension_start_age else 65
    
    # A) Base annual pension
    print(f"\n[A) BASE ANNUAL PENSION]")
    print(f"  Monthly pension (cents): {monthly_amount_cents:,.2f}")
    print(f"  Monthly pension (dollars): ${monthly_amount_dollars:,.2f}")
    print(f"  Formula: pension_base_annual = pension_monthly × 12")
    pension_base_annual = monthly_amount_dollars * 12
    print(f"  pension_base_annual = ${monthly_amount_dollars:,.2f} × 12 = ${pension_base_annual:,.2f}/year")
    print(f"  Pension start age: {start_age}")
    print(f"  Indexing rate: {indexing_rate * 100:.2f}% per year")
    
    # B) Pension indexing (after pension starts only)
    print(f"\n[B) PENSION INDEXING CALCULATIONS]")
    print(f"  Calculating pension amounts by age:")
    print(f"  Rules:")
    print(f"    - if age < pension_start_age: pension_annual[age] = 0")
    print(f"    - if age == pension_start_age: pension_annual[age] = pension_base_annual")
    print(f"    - if age > pension_start_age: pension_annual[age] = pension_base_annual × (1 + rate)^years_since_start")
    
    # Calculate indexed amounts by age (from current age to plan_until_age)
    current_age = basic_info.current_age
    plan_until_age = basic_info.plan_until_age if basic_info.plan_until_age else 90
    indexed_amounts = {}  # Keyed by age
    
    print(f"\n  [CALCULATIONS BY AGE]")
    print(f"  Calculating pension amounts from age {current_age} to age {plan_until_age}")
    for age in range(current_age, plan_until_age + 1):  # Calculate through plan_until_age
        if age < start_age:
            # Rule: if age < pension_start_age: pension_annual[age] = 0
            pension_annual = 0.0
            indexed_amounts[age] = pension_annual
            if age <= start_age + 2:  # Print ages around start
                print(f"    Age {age}: {age} < {start_age} → pension_annual = $0.00")
                
        elif age == start_age:
            # Rule: if age == pension_start_age: pension_annual[age] = pension_base_annual
            pension_annual = pension_base_annual
            indexed_amounts[age] = pension_annual
            print(f"    Age {age}: {age} == {start_age} → pension_annual = ${pension_annual:,.2f}")
            
        else:
            # Rule: if age > pension_start_age:
            # pension_annual[age] = pension_base_annual * (1 + pension_index_rate) ^ years_since_start
            years_since_start = age - start_age
            pension_annual = pension_base_annual * ((1 + indexing_rate) ** years_since_start)
            indexed_amounts[age] = pension_annual
            if years_since_start <= 5 or years_since_start % 5 == 0:  # Print first 5 and every 5th year
                print(f"    Age {age}: {age} > {start_age}, years_since_start = {years_since_start}")
                print(f"      pension_annual = ${pension_base_annual:,.2f} × (1 + {indexing_rate:.4f})^{years_since_start}")
                print(f"      pension_annual = ${pension_base_annual:,.2f} × {(1 + indexing_rate) ** years_since_start:.4f} = ${pension_annual:,.2f}")
    
    # Also create year_offset indexed amounts for backward compatibility
    year_offset_amounts = {}
    start_year = max(0, start_age - current_age)
    current_year = datetime.now().year
    start_calendar_year = current_year + start_year if start_year > 0 else current_year
    
    for year_offset in range(0, 31):  # Up to 30 years of retirement
        age = current_age + year_offset
        if age in indexed_amounts:
            year_offset_amounts[year_offset] = indexed_amounts[age]
    
    print(f"\n  [TIMING INFORMATION]")
    print(f"    Current age: {current_age}")
    print(f"    Pension start age: {start_age}")
    print(f"    Years until pension starts: {start_age} - {current_age} = {start_year} years")
    if start_year > 0:
        print(f"    Pension will start in year: {start_calendar_year} (in {start_year} years)")
    else:
        print(f"    Pension starts now (current year: {start_calendar_year})")
    
    result = {
        'has_pension': True,
        'base_amount': pension_base_annual,
        'indexing_rate': indexing_rate,
        'start_age': start_age,
        'start_year': start_year,  # Years until start (not calendar year)
        'start_calendar_year': start_calendar_year,  # Actual calendar year
        'indexed_amounts': year_offset_amounts,  # By year offset for backward compatibility
        'indexed_amounts_by_age': indexed_amounts  # By actual age (new)
    }
    
    print(f"\n[OUTPUT RESULTS]")
    print(f"  has_pension: {result['has_pension']}")
    print(f"  base_amount (pension_base_annual): ${result['base_amount']:,.2f}/year")
    print(f"  indexing_rate: {result['indexing_rate'] * 100:.2f}%")
    print(f"  start_age: {result['start_age']} years old")
    print(f"  start_year: {result['start_year']} years from now")
    print(f"  start_calendar_year: {result['start_calendar_year']} (actual calendar year)")
    print(f"  indexed_amounts (by year offset): {len(result['indexed_amounts'])} years calculated")
    print(f"  indexed_amounts_by_age: {len(result['indexed_amounts_by_age'])} ages calculated")
    print("-"*8)
    
    return result


# ============================================================================
# 3. INFLATION ASSUMPTION PROCESSING
# ============================================================================

def process_inflation_assumptions(basic_info: BasicInformation) -> Dict[str, Any]:
    """
    Process and setup global inflation assumptions.
    
    RETURNS: Dictionary with inflation configuration
    """
    
    print("-----")
    print("inflation assumptions")

    
    # INPUT DATA
    print("\n[INPUT DATA]")
    print(f"  inflation_rate (percentage): {basic_info.inflation_rate}")
    print(f"  DEFAULT_INFLATION_RATE: {DEFAULT_INFLATION_RATE * 100:.2f}%")
    
    inflation_rate_percent = float(basic_info.inflation_rate) if basic_info.inflation_rate else None
    inflation_rate = float(basic_info.inflation_rate) / 100 if basic_info.inflation_rate else DEFAULT_INFLATION_RATE
    
    print(f"\n[PROCESSING]")
    if inflation_rate_percent is not None:
        print(f"  User-provided inflation rate: {inflation_rate_percent:.2f}%")
        print(f"  Converted to decimal: {inflation_rate_percent}% ÷ 100 = {inflation_rate:.4f}")
    else:
        print(f"  No user-provided rate, using default: {DEFAULT_INFLATION_RATE * 100:.2f}%")
        print(f"  Annual rate (decimal): {inflation_rate:.4f}")
    
    monthly_rate = ((1 + inflation_rate) ** (1/12)) - 1
    compounding_factor = 1 + inflation_rate
    
    print(f"\n  [CALCULATIONS]")
    print(f"    Annual rate (decimal): {inflation_rate:.4f} = {inflation_rate * 100:.2f}%")
    print(f"    Monthly rate formula: (1 + annual_rate)^(1/12) - 1")
    print(f"    Monthly rate: (1 + {inflation_rate:.4f})^(1/12) - 1 = {monthly_rate:.6f} = {monthly_rate * 100:.4f}%")
    print(f"    Compounding factor: 1 + {inflation_rate:.4f} = {compounding_factor:.4f}")
    
    result = {
        'annual_rate': inflation_rate,
        'monthly_rate': monthly_rate,
        'compounding_factor': compounding_factor
    }
    
    print(f"\n[OUTPUT RESULTS]")
    print(f"  annual_rate: {result['annual_rate']:.4f} = {result['annual_rate'] * 100:.2f}%")
    print(f"  monthly_rate: {result['monthly_rate']:.6f} = {result['monthly_rate'] * 100:.4f}%")
    print(f"  compounding_factor: {result['compounding_factor']:.4f}")
    print("-"*8)
    
    return result


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
        result = base_amount * ((1 + monthly_rate) ** periods)
        print(f"      [INFLATION CALC] Monthly: ${base_amount:,.2f} × (1 + {monthly_rate:.6f})^{periods} = ${result:,.2f}")
        return result
    else:
        result = base_amount * ((1 + inflation_rate) ** years)
        if years > 0:
            print(f"      [INFLATION CALC] Annual: ${base_amount:,.2f} × (1 + {inflation_rate:.4f})^{years} = ${result:,.2f}")
        return result


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
    
    print(f"      Account Profile: {profile} → Expected Return: {expected_return * 100:.2f}%")
    
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
    print("\n" + "-"*8)
    print("WEIGHTED PORTFOLIO RETURN CALCULATION")
    print("-"*8)
    
    # INPUT DATA
    print("\n[INPUT DATA]")
    print(f"  Number of accounts: {len(accounts)}")
    for i, acc in enumerate(accounts, 1):
        print(f"  Account {i}:")
        print(f"    Type: {acc.account_type}")
        print(f"    Balance (cents): {acc.balance}")
        print(f"    Monthly contribution (cents): {acc.monthly_contribution}")
        print(f"    Investment profile: {acc.investment_profile}")
    
    # Calculate total balance
    total_balance = sum(float(acc.balance) for acc in accounts)
    print(f"\n  Total balance (cents): {total_balance:,.2f}")
    print(f"  Total balance (dollars): ${total_balance / 100:,.2f}")
    
    print(f"\n[PROCESSING]")
    
    if total_balance > 0:
        # Weight by balances (convert from cents to dollars)
        print(f"  [METHOD: Weight by Balances]")
        print(f"  Formula: Σ(balance × return) / total_balance")
        print(f"\n  Calculations per account:")
        
        weighted_sum = 0
        for acc in accounts:
            balance_dollars = float(acc.balance) / 100
            profile_data = get_account_return_profile(acc)
            expected_return = profile_data['expected_return']
            weighted_value = balance_dollars * expected_return
            weighted_sum += weighted_value
            weight_pct = (balance_dollars / (total_balance / 100)) * 100 if total_balance > 0 else 0
            print(f"    {acc.account_type}: ${balance_dollars:,.2f} × {expected_return * 100:.2f}% = ${weighted_value:,.2f} (weight: {weight_pct:.2f}%)")
        
        weighted_return = weighted_sum / (total_balance / 100)
        print(f"\n  Weighted return = ${weighted_sum:,.2f} / ${total_balance / 100:,.2f} = {weighted_return:.4f} = {weighted_return * 100:.2f}%")
        
        # Calculate contribution weights for reference (convert from cents to dollars)
        total_contribution = sum((float(acc.monthly_contribution) / 100) for acc in accounts if acc.monthly_contribution)
        contribution_weights = {}
        for acc in accounts:
            if total_contribution > 0 and acc.monthly_contribution:
                weight = (float(acc.monthly_contribution) / 100) / total_contribution
                acc_type = acc.account_type.upper() if acc.account_type else 'NON_REG'
                contribution_weights[acc_type] = weight
        
        result = {
            'weighted_return': weighted_return,
            'total_balance': total_balance,
            'weighting_method': 'balance',
            'contribution_weights': contribution_weights,
            'account_count': len(accounts)
        }
        
    else:
        # Weight by contributions (convert from cents to dollars)
        total_contribution = sum((float(acc.monthly_contribution) / 100) for acc in accounts if acc.monthly_contribution)
        print(f"  Total balance is 0, trying contribution weighting")
        print(f"  Total contribution (dollars/month): ${total_contribution:,.2f}")
        
        if total_contribution > 0:
            print(f"  [METHOD: Weight by Contributions]")
            print(f"  Formula: Σ(contribution × return) / total_contribution")
            print(f"\n  Calculations per account:")
            
            weighted_sum = 0
            for acc in accounts:
                if acc.monthly_contribution:
                    contrib_dollars = float(acc.monthly_contribution) / 100
                    profile_data = get_account_return_profile(acc)
                    expected_return = profile_data['expected_return']
                    weighted_value = contrib_dollars * expected_return
                    weighted_sum += weighted_value
                    weight_pct = (contrib_dollars / total_contribution) * 100
                    print(f"    {acc.account_type}: ${contrib_dollars:,.2f}/month × {expected_return * 100:.2f}% = ${weighted_value:,.2f}/month (weight: {weight_pct:.2f}%)")
            
            weighted_return = weighted_sum / total_contribution
            print(f"\n  Weighted return = ${weighted_sum:,.2f} / ${total_contribution:,.2f} = {weighted_return:.4f} = {weighted_return * 100:.2f}%")
            
            contribution_weights = {(acc.account_type.upper() if acc.account_type else 'NON_REG'): (float(acc.monthly_contribution) / 100)/total_contribution for acc in accounts if acc.monthly_contribution}
            
            result = {
                'weighted_return': weighted_return,
                'total_balance': total_balance,
                'weighting_method': 'contribution',
                'contribution_weights': contribution_weights,
                'account_count': len(accounts)
            }
        else:
            # Default to balanced profile
            print(f"  [METHOD: Default (no balance or contributions)]")
            print(f"  Using default balanced profile: 5%")
            result = {
                'weighted_return': 0.05,
                'total_balance': 0.0,
                'weighting_method': 'default',
                'contribution_weights': {},
                'account_count': len(accounts)
            }
    
    print(f"\n[OUTPUT RESULTS]")
    print(f"  weighted_return: {result['weighted_return']:.4f} = {result['weighted_return'] * 100:.2f}%")
    print(f"  total_balance: ${result['total_balance'] / 100:,.2f}")
    print(f"  weighting_method: {result['weighting_method']}")
    print(f"  account_count: {result['account_count']}")
    print("-"*8)
    
    return result


def process_return_after_retirement(basic_info: BasicInformation) -> Dict[str, Any]:
    """
    Process return assumptions for the retirement phase.
    """
    print("\n" + "-"*8)
    print("POST-RETIREMENT RETURN PROCESSING")
    print("-"*8)
    
    # INPUT DATA
    print("\n[INPUT DATA]")
    print(f"  return_after_work_optional (percentage): {basic_info.return_after_work_optional}")
    print(f"  DEFAULT_RETURN_AFTER_RETIREMENT: {DEFAULT_RETURN_AFTER_RETIREMENT * 100:.2f}%")
    
    return_rate_percent = float(basic_info.return_after_work_optional) if basic_info.return_after_work_optional else None
    return_rate = float(basic_info.return_after_work_optional) / 100 if basic_info.return_after_work_optional else DEFAULT_RETURN_AFTER_RETIREMENT
    
    print(f"\n[PROCESSING]")
    if return_rate_percent is not None:
        print(f"  User-provided return rate: {return_rate_percent:.2f}%")
        print(f"  Converted to decimal: {return_rate_percent}% ÷ 100 = {return_rate:.4f}")
    else:
        print(f"  No user-provided rate, using default: {DEFAULT_RETURN_AFTER_RETIREMENT * 100:.2f}%")
        print(f"  Annual return (decimal): {return_rate:.4f}")
    
    monthly_return = ((1 + return_rate) ** (1/12)) - 1
    
    print(f"\n  [CALCULATIONS]")
    print(f"    Annual return (decimal): {return_rate:.4f} = {return_rate * 100:.2f}%")
    print(f"    Monthly return formula: (1 + annual_return)^(1/12) - 1")
    print(f"    Monthly return: (1 + {return_rate:.4f})^(1/12) - 1 = {monthly_return:.6f} = {monthly_return * 100:.4f}%")
    print(f"    Is conservative (< 5%): {return_rate < 0.05}")
    print(f"    Is growth (>= 7%): {return_rate >= 0.07}")
    
    result = {
        'annual_return': return_rate,
        'monthly_return': monthly_return,
        'is_conservative': return_rate < 0.05,
        'is_growth': return_rate >= 0.07
    }
    
    print(f"\n[OUTPUT RESULTS]")
    print(f"  annual_return: {result['annual_return']:.4f} = {result['annual_return'] * 100:.2f}%")
    print(f"  monthly_return: {result['monthly_return']:.6f} = {result['monthly_return'] * 100:.4f}%")
    print(f"  is_conservative: {result['is_conservative']}")
    print(f"  is_growth: {result['is_growth']}")
    print("-"*8)
    
    return result


# ============================================================================
# 5. WITHDRAWAL STRATEGY CONFIGURATION
# ============================================================================

def configure_withdrawal_strategy(basic_info: BasicInformation) -> Dict[str, Any]:
    """
    Load and configure withdrawal strategy settings.
    
    RETURNS: Complete withdrawal strategy configuration
    """
    print(f"\n[PROCESSING]")
    requested_strategy = basic_info.withdrawal_strategy.lower() if basic_info.withdrawal_strategy else None
    strategy = requested_strategy if requested_strategy else 'optimized'
    
    print(f"  Requested strategy: {requested_strategy if requested_strategy else 'None (using default)'}")
    print(f"  Selected strategy: {strategy}")
    
    withdrawal_order = WITHDRAWAL_STRATEGIES.get(strategy, WITHDRAWAL_STRATEGIES['optimized'])
    print(f"  Withdrawal order: {' → '.join(withdrawal_order)}")
    
    # Get withdrawal rate (as decimal) - default 4%
    withdrawal_rate = 0.04
    print(f"  Withdrawal rate: {withdrawal_rate * 100:.2f}% (default)")
    
    # Get withdrawal limits if specified
    floor_amount = 0.0
    ceiling_amount = None
    
    # Additional strategy parameters
    dynamic_adjustment = False
    guardrail_threshold = 0.2  # 20% threshold
    
    result = {
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
    
    return result


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
    print("\n[INPUT DATA]")
    events = basic_info.life_events.all()
    print(f"  Number of life events: {len(list(events))}")
    print(f"  Current age: {basic_info.current_age}")
    
    processed_events = []
    
    # Get events from basic_info
    events = basic_info.life_events.all()
    
    print(f"\n[PROCESSING]")
    print(f"  Processing each life event:")
    
    for i, event in enumerate(events, 1):
        print(f"\n    Event {i}:")
        print(f"      Name: {event.name}")
        print(f"      Type: {event.event_type}")
        print(f"      Amount (cents): {event.amount}")
        print(f"      Frequency: {event.frequency}")
        print(f"      Start age: {event.start_age}")
        print(f"      End age: {event.end_age}")
        print(f"      Account: {event.account}")
        # Calculate year of effect relative to current age
        year_of_effect = event.start_age - basic_info.current_age
        print(f"      Year of effect: {event.start_age} - {basic_info.current_age} = {year_of_effect}")
        
        # Determine event type
        event_type = 'expenses' if event.event_type == 'expenses' else 'contribution'
        print(f"      Event type: {event_type}")
        
        # Process event data
        amount_cents = float(event.amount) if event.amount else 0.0
        amount_dollars = amount_cents / 100
        print(f"      Amount: {amount_cents:,.2f} cents = ${amount_dollars:,.2f}")
        
        # Calculate duration based on frequency type
        if event.frequency == 'one_time':
            # One-time events happen once at start_age, duration is 1 year
            duration_years = 1
            print(f"      Frequency: one_time → Duration: 1 year (happens once at age {event.start_age})")
        elif event.frequency == 'annually':
            # Annual events happen every year from start_age to end_age (inclusive)
            if event.end_age > event.start_age:
                duration_years = event.end_age - event.start_age + 1  # Inclusive: ages 38-49 = 12 years
            else:
                duration_years = 1
            print(f"      Frequency: annually → Duration: {duration_years} years (happens at ages {event.start_age} to {event.end_age})")
        elif event.frequency == 'monthly':
            # Monthly events happen every month from start_age to end_age
            if event.end_age > event.start_age:
                duration_years = event.end_age - event.start_age  # Span in years (e.g., 38-49 = 12 years)
            else:
                duration_years = 1
            print(f"      Frequency: monthly → Duration: {duration_years} years (happens every month from age {event.start_age} to {event.end_age})")
        else:
            # Default: treat as one-time if frequency is unknown
            duration_years = 1
            print(f"      Frequency: {event.frequency} (unknown) → Duration: 1 year (default)")
        
        is_recurring = event.frequency != 'one_time'
        print(f"      Is recurring: {is_recurring}")
        
        processed_event = {
            'id': event.id,
            'year_of_effect': max(0, year_of_effect),
            'amount': amount_dollars,
            'type': event_type,
            'account_affected': event.account.upper() if event.account else 'NON_REG',
            'description': event.name if event.name else 'Life Event',
            'is_recurring': is_recurring,
            'duration_years': duration_years,
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
            # Use default or get inflation rate directly (avoid duplicate processing prints)
            inflation_rate = float(basic_info.inflation_rate) / 100 if basic_info.inflation_rate else DEFAULT_INFLATION_RATE
            print(f"      Applying inflation adjustment for {processed_event['year_of_effect']} years at {inflation_rate * 100:.2f}%...")
            processed_event['future_value'] = apply_inflation_to_amount(
                processed_event['amount'],
                inflation_rate,
                processed_event['year_of_effect']
            )
            print(f"      Future value: ${processed_event['future_value']:,.2f}")
        else:
            processed_event['future_value'] = processed_event['amount']
            print(f"      No inflation adjustment (current year): ${processed_event['future_value']:,.2f}")
        
        processed_events.append(processed_event)
    
    # Sort events by year of effect
    processed_events.sort(key=lambda x: x['year_of_effect'])
    print(f"\n  Sorted {len(processed_events)} events by year of effect")
    
    print(f"\n[OUTPUT RESULTS]")
    print(f"  Total processed events: {len(processed_events)}")
    if processed_events:
        print(f"  Event timeline:")
        for event in processed_events[:10]:  # Show first 10
            print(f"    Year {event['year_of_effect']}: {event['description']} - ${event['future_value']:,.2f} ({event['type']})")
        if len(processed_events) > 10:
            print(f"    ... and {len(processed_events) - 10} more events")
    
    return processed_events
    
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
    print("\n" + "-"*8)
    print("ACCOUNT DATA PREPARATION")
    print("-"*8)
    
    # INPUT DATA
    print("\n[INPUT DATA]")
    print(f"  Number of accounts: {len(accounts)}")
    for i, acc in enumerate(accounts, 1):
        print(f"  Account {i}:")
        print(f"    ID: {acc.id}")
        print(f"    Type: {acc.account_type}")
        print(f"    Balance (cents): {acc.balance}")
        print(f"    Monthly contribution (cents): {acc.monthly_contribution}")
        print(f"    Investment profile: {acc.investment_profile}")
    
    # Initialize account structures
    account_balances = {'TFSA': 0.0, 'RRSP': 0.0, 'NON_REG': 0.0}
    account_contributions = {'TFSA': 0.0, 'RRSP': 0.0, 'NON_REG': 0.0}
    account_returns = {'TFSA': 0.05, 'RRSP': 0.05, 'NON_REG': 0.05}
    account_profiles = {'TFSA': 'balanced', 'RRSP': 'balanced', 'NON_REG': 'balanced'}
    
    # Track individual accounts
    individual_accounts = []
    
    print(f"\n[PROCESSING]")
    print(f"  Processing each account:")
    
    # Populate from accounts
    for acc in accounts:
        acc_type = acc.account_type.upper() if acc.account_type else 'NON_REG'
        if acc_type in ['TFSA', 'RRSP', 'NON_REG', 'NON_REGISTERED']:
            if acc_type == 'NON_REGISTERED':
                acc_type = 'NON_REG'
            
            # Basic account data (convert from cents to dollars)
            balance_cents = float(acc.balance)
            balance_dollars = balance_cents / 100
            account_balances[acc_type] = balance_dollars
            
            monthly_contrib_cents = float(acc.monthly_contribution) if acc.monthly_contribution else 0.0
            monthly_contrib_dollars = monthly_contrib_cents / 100
            annual_contrib = monthly_contrib_dollars * 12
            account_contributions[acc_type] = annual_contrib
            
            print(f"\n    {acc_type} Account:")
            print(f"      Balance: {balance_cents:,.2f} cents = ${balance_dollars:,.2f}")
            print(f"      Monthly contribution: {monthly_contrib_cents:,.2f} cents = ${monthly_contrib_dollars:,.2f}")
            print(f"      Annual contribution: ${monthly_contrib_dollars:,.2f} × 12 = ${annual_contrib:,.2f}")
            
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
    
    print(f"\n  [TOTALS]")
    print(f"    Total balance across all accounts: ${total_balance:,.2f}")
    print(f"    Total annual contribution: ${total_annual_contribution:,.2f}")
    
    # Calculate allocation percentages
    allocation_percentages = {}
    if total_balance > 0:
        print(f"\n  [ALLOCATION PERCENTAGES]")
        for acc_type, balance in account_balances.items():
            allocation_percentages[acc_type] = (balance / total_balance) * 100
            print(f"    {acc_type}: ${balance:,.2f} / ${total_balance:,.2f} × 100 = {allocation_percentages[acc_type]:.2f}%")
    
    result = {
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
    
    print(f"\n[OUTPUT RESULTS]")
    print(f"  account_balances: {result['account_balances']}")
    print(f"  account_contributions: {result['account_contributions']}")
    print(f"  account_returns: {dict((k, f'{v*100:.2f}%') for k, v in result['account_returns'].items())}")
    print(f"  total_balance: ${result['total_balance']:,.2f}")
    print(f"  total_annual_contribution: ${result['total_annual_contribution']:,.2f}")
    print(f"  account_count: {result['account_count']}")
    print("-"*8)
    
    return result


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
    print("Pre-processing entry point")
    # input data
    print(f"  Client ID: {basic_info.client_id}")
    print(f"  User ID: {basic_info.user_id}")
    print(f"  Current Age: {basic_info.current_age}")
    print(f"  Work Optional Age: {basic_info.work_optional_age}")
    print(f"  Plan Until Age: {basic_info.plan_until_age}")
    print(f"  Yearly Income Goal (cents): {basic_info.yearly_income_for_ideal_lifestyle}")
    print(f"  Number of Accounts: {len(accounts)}")
    print(f"  Number of Life Events: {len(list(basic_info.life_events.all())) if hasattr(basic_info, 'life_events') else 0}")
    
    # Calculate time periods
    print("step 1: time period")
    print("-----")
    current_year = datetime.now().year
    print(f"  Current year: {current_year}")
    
    work_optional_age = basic_info.work_optional_age if basic_info.work_optional_age else basic_info.current_age + 30
    print(f"  Work optional age: {work_optional_age}")
    
    plan_until_age = basic_info.plan_until_age if basic_info.plan_until_age else 90
    print(f"  Plan until age: {plan_until_age}")
    
    years_to_retirement = max(0, work_optional_age - basic_info.current_age)
    print(f"  Years to retirement: {work_optional_age} - {basic_info.current_age} = {years_to_retirement}")
    
    years_in_retirement = max(0, plan_until_age - work_optional_age)
    print(f"  Years in retirement: {plan_until_age} - {work_optional_age} = {years_in_retirement}")
    
    total_years = years_to_retirement + years_in_retirement
    print(f"  Total years in plays: {total_years} years")
    
    # 1. Process government benefits
    print("-----")
    print("step 2: governement benefits")
    print("-----")
    cpp_data = calculate_cpp_adjustment(basic_info)
    oas_data = calculate_oas_adjustment(basic_info)
    
    # 2. Process pension with indexing
    print("-----")
    print("step 3: pension processing")
    
    pension_data = calculate_pension_with_indexing(basic_info)
    
    # 3. Process inflation assumptions
    # print("-----")
    # print("step 4: inflation assumptions")
    inflation_data = process_inflation_assumptions(basic_info)
    
    # 4. Process return assumptions
    # print("-----")
    # print("step 5: return assumptions")
    weighted_return_data = calculate_weighted_portfolio_return(accounts)
    post_retirement_return_data = process_return_after_retirement(basic_info)
    
    # 5. Configure withdrawal strategy
    # print("-----")
    # print("step 6: withdrawal strategy configuration")
    # print(f"\n[INPUT DATA]")
    # print(f"  withdrawal_strategy: {basic_info.withdrawal_strategy}")
    withdrawal_config = configure_withdrawal_strategy(basic_info)
    # print(f"\n[OUTPUT RESULTS]")
    # print(f"  strategy_name: {withdrawal_config['strategy_name']}")
    # print(f"  withdrawal_order: {withdrawal_config['withdrawal_order']}")
    # print(f"  withdrawal_rate: {withdrawal_config['withdrawal_rate'] * 100:.2f}%")
    # print(f"  description: {withdrawal_config['description']}")
    # print("-"*8)
    
    # 6. Preprocess life events
    print("-----")
    print("step 7: life events preprocessing")
    if events is None:
        events_data = preprocess_life_events(basic_info)
    else:
        # Use provided events
        events_data = events
        print(f"\n[PROCESSING]")
        print(f"  Using provided events list: {len(events_data)} events")
    
    events_by_year = categorize_events_by_year(events_data)
    # print(f"\n[OUTPUT RESULTS]")
    # print(f"  Total events processed: {len(events_data)}")
    # print(f"  Events by year: {len(events_by_year)} years with events")
    # print("-"*8)
    
    # 7. Prepare account data
    # print("-----")
    # print("step 8: account data preparation")
    account_data = prepare_account_data(accounts)
    
    # 8. Calculate base income needs (inflation adjusted)
    # print("-----")
    # print("step 9: retirement income needs calculation")
    yearly_income_goal_cents = float(basic_info.yearly_income_for_ideal_lifestyle) if basic_info.yearly_income_for_ideal_lifestyle else 0.0
    yearly_income_goal = yearly_income_goal_cents / 100
    
    # print(f"\n[INPUT DATA]")
    # print(f"  yearly_income_for_ideal_lifestyle (cents): {yearly_income_goal_cents:,.2f}")
    # print(f"  yearly_income_goal (dollars): ${yearly_income_goal:,.2f}")
    # print(f"  inflation_rate: {inflation_data['annual_rate'] * 100:.2f}%")
    # print(f"  years_to_retirement: {years_to_retirement}")
    # print(f"  years_in_retirement: {years_in_retirement}")
    
    # Calculate income needs for each retirement year
    # print(f"\n[PROCESSING]")
    # print(f"  Calculating inflated income needs for each retirement year:")
    # print(f"  Formula: Base Income × (1 + inflation_rate)^(years_to_retirement + year)")
    retirement_income_needs = {}
    for year in range(min(years_in_retirement + 1, 10)):  # Print first 10 years
        total_years = years_to_retirement + year
        inflated_amount = apply_inflation_to_amount(
            yearly_income_goal,
            inflation_data['annual_rate'],
            total_years
        )
        retirement_income_needs[year] = inflated_amount
    # Calculate remaining years silently
    for year in range(10, years_in_retirement + 1):
        total_years = years_to_retirement + year
        inflated_amount = apply_inflation_to_amount(
            yearly_income_goal,
            inflation_data['annual_rate'],
            total_years
        )
        retirement_income_needs[year] = inflated_amount
    
    # print(f"\n[OUTPUT RESULTS]")
    # print(f"  Calculated income needs for {len(retirement_income_needs)} retirement years")
    if len(retirement_income_needs) > 0:
        print(f"  Year 0 (first retirement year): ${retirement_income_needs[0]:,.2f}")
        if len(retirement_income_needs) > 1:
            print(f"  Year {len(retirement_income_needs) - 1} (last retirement year): ${retirement_income_needs[len(retirement_income_needs) - 1]:,.2f}")
    
    # 9. Compile all data
    # print("-----")
    # print("step 10: compiling preprocessed data")
    # print(f"\n[COMPILING]")
    # print(f"  Combining all processed data into final structure...")
    
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
    # print(f"\n  Generating summary statistics...")
    preprocessed_data['summary'] = generate_preprocessing_summary(preprocessed_data)
    
    # print(f"\n[FINAL PREPROCESSED DATA SUMMARY]")
    # print(f"  Time Periods:")
    # print(f"    Current age: {preprocessed_data['current_age']}")
    # print(f"    Retirement age: {preprocessed_data['retirement_age']}")
    # print(f"    Years to retirement: {preprocessed_data['years_to_retirement']}")
    # print(f"    Years in retirement: {preprocessed_data['years_in_retirement']}")
    # print(f"  Government Benefits:")
    # print(f"    CPP (adjusted): ${preprocessed_data['cpp_adjusted']:,.2f}/year")
    # print(f"    OAS (adjusted): ${preprocessed_data['oas_adjusted']:,.2f}/year")
    # print(f"    Pension: ${preprocessed_data['pension_amount']:,.2f}/year")
    # print(f"  Assumptions:")
    # print(f"    Inflation rate: {preprocessed_data['inflation_rate'] * 100:.2f}%")
    # print(f"    Accumulation return: {preprocessed_data['accumulation_returns']['weighted_return'] * 100:.2f}%")
    # print(f"    Retirement return: {preprocessed_data['return_after_retirement'] * 100:.2f}%")
    # print(f"  Accounts:")
    # print(f"    Total balance: ${preprocessed_data['account_data']['total_balance']:,.2f}")
    # print(f"    Total annual contributions: ${preprocessed_data['account_data']['total_annual_contribution']:,.2f}")
    # print(f"  Income Goals:")
    # print(f"    Base income goal: ${preprocessed_data['yearly_income_goal']:,.2f}/year")
    # print(f"    First retirement year need: ${preprocessed_data['retirement_income_needs'][0]:,.2f}/year" if preprocessed_data['retirement_income_needs'] else "    No retirement income needs calculated")
    
    # print("-----")
    # print("preprocessing complete")
    # print("-----")
    
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
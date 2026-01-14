"""
GAP ANALYSIS
===========

This module performs gap analysis by comparing projected savings vs. needed savings
to determine if the retirement plan is on track.

The Gap Analysis identifies:
- Extra savings (surplus) or shortfall
- Whether the plan is on track
- If money runs out before life expectancy

INPUTS: Projected savings, savings needed, withdrawal breakdown
OUTPUTS: Gap analysis results (extra savings, on-track status, run-out age)
"""

from typing import List, Dict, Any, Optional


def calculate_extra_savings(
    projected_savings: float,
    savings_needed: float
) -> float:
    """
    Calculate extra savings (surplus) or shortfall.
    
    INPUTS:
        projected_savings: float - Projected savings at retirement
        savings_needed: float - Savings needed at retirement
    
    OUTPUTS:
        float - Extra savings (positive) or shortfall (negative)
        
    EXAMPLE:
        Projected: $800,000, Needed: $650,000
        Result: $150,000 (extra savings)
        
        Projected: $500,000, Needed: $650,000
        Result: -$150,000 (shortfall)
    """
    return projected_savings - savings_needed


def determine_on_track_status(
    extra_savings: float,
    run_out_age: Optional[int],
    life_expectancy: int
) -> bool:
    """
    Determine if the retirement plan is on track.
    
    INPUTS:
        extra_savings: float - Extra savings (positive) or shortfall (negative)
        run_out_age: int or None - Age when money runs out, or None if it lasts
        life_expectancy: int - Expected age of death
    
    OUTPUTS:
        bool - True if on track, False if not on track
        
    BUSINESS RULES:
        - On track if extra_savings >= 0 AND money lasts to life expectancy
        - Not on track if extra_savings < 0 OR money runs out early
    """
    # Not on track if there's a shortfall
    if extra_savings < 0:
        return False
    
    # Not on track if money runs out before life expectancy
    if run_out_age is not None and run_out_age < life_expectancy:
        return False
    
    # On track otherwise
    return True


def find_run_out_age_from_breakdown(
    yearly_breakdown: List[Dict[str, Any]],
    retirement_age: int
) -> Optional[int]:
    """
    Find the age at which money runs out from yearly breakdown.
    
    INPUTS:
        yearly_breakdown: List[Dict] - Complete year-by-year breakdown
            Each dict should have 'age' and 'ending_balance' keys
        retirement_age: int - Age at retirement
    
    OUTPUTS:
        int or None - Age when money runs out, or None if money lasts
        
    NOTE:
        Only checks retirement phase (age >= retirement_age)
    """
    for year_data in yearly_breakdown:
        age = year_data.get('age')
        ending_balance = year_data.get('ending_balance', 0)
        
        if age is not None and ending_balance <= 0 and age >= retirement_age:
            return age
    
    return None


def perform_gap_analysis(
    projected_savings: float,
    savings_needed: float,
    yearly_breakdown: List[Dict[str, Any]],
    retirement_age: int,
    life_expectancy: int
) -> Dict[str, Any]:
    """
    Perform comprehensive gap analysis.
    
    INPUTS:
        projected_savings: float - Projected savings at retirement
        savings_needed: float - Savings needed at retirement
        yearly_breakdown: List[Dict] - Complete year-by-year breakdown
        retirement_age: int - Age at retirement
        life_expectancy: int - Expected age of death
    
    OUTPUTS:
        Dict containing:
        {
            'extra_savings': float,        # Surplus (positive) or shortfall (negative)
            'is_on_track': bool,           # True if plan is on track
            'run_out_age': int or None,    # Age when money runs out, or None
            'shortfall_amount': float,     # Shortfall amount (0 if no shortfall)
            'surplus_amount': float        # Surplus amount (0 if no surplus)
        }
    """
    print("\n" + "-"*8)
    print("GAP ANALYSIS")
    print("-"*8)
    
    print("\n[INPUT DATA]")
    print(f"  Projected savings at retirement: ${projected_savings:,.2f}")
    print(f"  Savings needed at retirement: ${savings_needed:,.2f}")
    print(f"  Retirement age: {retirement_age}")
    print(f"  Life expectancy: {life_expectancy}")
    print(f"  Years in breakdown: {len(yearly_breakdown)}")
    
    print(f"\n[PROCESSING]")
    print(f"  Step 1: Calculate Extra Savings")
    # Calculate extra savings
    extra_savings = calculate_extra_savings(projected_savings, savings_needed)
    print(f"    Extra Savings = Projected Savings - Savings Needed")
    print(f"    Extra Savings = ${projected_savings:,.2f} - ${savings_needed:,.2f} = ${extra_savings:,.2f}")
    
    print(f"\n  Step 2: Find Run-Out Age")
    # Find run-out age
    run_out_age = find_run_out_age_from_breakdown(yearly_breakdown, retirement_age)
    if run_out_age:
        print(f"    Run-out age found: {run_out_age}")
    else:
        print(f"    No run-out age - money lasts through retirement")
    
    print(f"\n  Step 3: Determine On-Track Status")
    # Determine on-track status
    is_on_track = determine_on_track_status(extra_savings, run_out_age, life_expectancy)
    print(f"    Extra savings >= 0: {extra_savings >= 0}")
    if run_out_age:
        print(f"    Run-out age < life expectancy: {run_out_age < life_expectancy}")
    else:
        print(f"    Money lasts (no run-out age)")
    print(f"    Is on track: {is_on_track}")
    
    print(f"\n  Step 4: Calculate Shortfall and Surplus")
    # Calculate shortfall and surplus
    shortfall_amount = abs(extra_savings) if extra_savings < 0 else 0.0
    surplus_amount = extra_savings if extra_savings > 0 else 0.0
    print(f"    Shortfall amount: ${shortfall_amount:,.2f}")
    print(f"    Surplus amount: ${surplus_amount:,.2f}")
    
    result = {
        'extra_savings': round(extra_savings, 2),
        'is_on_track': is_on_track,
        'run_out_age': run_out_age,
        'shortfall_amount': round(shortfall_amount, 2),
        'surplus_amount': round(surplus_amount, 2),
    }
    
    print(f"\n[OUTPUT RESULTS]")
    print(f"  extra_savings: ${result['extra_savings']:,.2f}")
    print(f"  is_on_track: {result['is_on_track']}")
    print(f"  run_out_age: {result['run_out_age']}")
    print(f"  shortfall_amount: ${result['shortfall_amount']:,.2f}")
    print(f"  surplus_amount: ${result['surplus_amount']:,.2f}")
    print("-"*8)
    
    return result


def calculate_additional_monthly_needed(
    shortfall_amount: float,
    years_to_retirement: int,
    expected_return: float
) -> float:
    """
    Calculate additional monthly contribution needed to cover shortfall.
    
    INPUTS:
        shortfall_amount: float - Shortfall amount at retirement
        years_to_retirement: int - Years until retirement
        expected_return: float - Expected annual return as decimal
    
    OUTPUTS:
        float - Additional monthly contribution needed
        
    FORMULA:
        Uses Future Value of Annuity formula in reverse:
        PMT = FV × r / [(1 + r)^n - 1]
        where:
            FV = shortfall_amount
            r = monthly return = (1 + annual_return)^(1/12) - 1
            n = months to retirement = years_to_retirement × 12
        
    NOTE:
        This is a simplified calculation. More complex scenarios may require
        iterative calculations.
    """
    print("\n" + "-"*8)
    print("ADDITIONAL MONTHLY CONTRIBUTION CALCULATION")
    print("-"*8)
    
    print("\n[INPUT DATA]")
    print(f"  Shortfall amount: ${shortfall_amount:,.2f}")
    print(f"  Years to retirement: {years_to_retirement}")
    print(f"  Expected annual return: {expected_return*100:.2f}%")
    
    if shortfall_amount <= 0 or years_to_retirement <= 0:
        print(f"\n[OUTPUT RESULTS]")
        print(f"  No shortfall or invalid years - no additional monthly needed")
        return 0.0
    
    print(f"\n[PROCESSING]")
    # Convert annual return to monthly
    monthly_return = (1 + expected_return) ** (1/12) - 1
    months_to_retirement = years_to_retirement * 12
    
    print(f"  Convert annual return to monthly:")
    print(f"    Monthly return = (1 + {expected_return:.4f})^(1/12) - 1 = {monthly_return:.6f} = {monthly_return*100:.4f}%")
    print(f"    Months to retirement = {years_to_retirement} × 12 = {months_to_retirement}")
    
    # Calculate monthly payment needed
    if monthly_return == 0:
        # If no return, simple division
        print(f"\n  Monthly return = 0, using simple calculation:")
        monthly_payment = shortfall_amount / months_to_retirement
        print(f"    Monthly payment = ${shortfall_amount:,.2f} / {months_to_retirement} = ${monthly_payment:,.2f}")
    else:
        # Future Value of Annuity formula (solving for PMT)
        print(f"\n  Using Future Value of Annuity formula (solving for PMT):")
        print(f"    PMT = FV / FV_factor")
        print(f"    FV_factor = [(1 + r)^n - 1] / r")
        print(f"    where r = {monthly_return:.6f}, n = {months_to_retirement}")
        
        fv_factor = ((1 + monthly_return) ** months_to_retirement - 1) / monthly_return
        monthly_payment = shortfall_amount / fv_factor
        
        print(f"    (1 + r)^n = (1 + {monthly_return:.6f})^{months_to_retirement} = {(1 + monthly_return) ** months_to_retirement:.6f}")
        print(f"    FV_factor = [{(1 + monthly_return) ** months_to_retirement:.6f} - 1] / {monthly_return:.6f} = {fv_factor:.6f}")
        print(f"    Monthly payment = ${shortfall_amount:,.2f} / {fv_factor:.6f} = ${monthly_payment:,.2f}")
    
    print(f"\n[OUTPUT RESULTS]")
    print(f"  Additional monthly contribution needed: ${monthly_payment:,.2f}")
    print("-"*8)
    
    return monthly_payment


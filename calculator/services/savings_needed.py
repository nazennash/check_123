"""
SAVINGS NEEDED CALCULATION
===========================

This module calculates how much savings are needed at retirement to fund
the income shortfall (income need minus government benefits/pension).

Uses Present Value of Growing Annuity formula to account for inflation
and investment returns during retirement.

INPUTS: Income goals, government benefits, inflation, returns, years
OUTPUTS: Target savings amount needed at retirement
"""

from typing import Dict, Any
from api.models import BasicInformation
from .preprocessing import apply_inflation_to_amount


def calculate_annual_shortfall(
    yearly_income_goal: float,
    inflation_rate: float,
    years_to_retirement: int,
    basic_info: BasicInformation,
    preprocessed_data: Dict[str, Any]
) -> float:
    """
    Calculate the annual income shortfall at retirement (what needs to come from savings).
    
    INPUTS:
        yearly_income_goal: float - Income goal in today's dollars
        inflation_rate: float - Annual inflation rate as decimal (e.g., 0.025 for 2.5%)
        years_to_retirement: int - Years until retirement
        basic_info: BasicInformation object containing:
            - cpp_start_age, cpp_amount_at_age
            - oas_start_age, oas_amount_at_OAS_age
            - has_work_pension (with pension data)
        preprocessed_data: Dict with cpp_adjusted, oas_adjusted, pension_amount
    
    OUTPUTS:
        float - Annual shortfall amount at retirement (in future dollars)
        Returns 0 if government benefits cover everything
        
    PROCESS:
        1. Inflate income goal to retirement year
        2. Calculate guaranteed income (CPP, OAS, Pension)
        3. Calculate shortfall = inflated income - guaranteed income
    """
    print(f"\n[PROCESSING]")
    print(f"  Step 1: Calculate Inflated Income Need at Retirement")
    print(f"    Base income goal: ${yearly_income_goal:,.2f}/year")
    print(f"    Inflation rate: {inflation_rate*100:.2f}%")
    print(f"    Years to retirement: {years_to_retirement}")
    
    # Step 1: Calculate Inflated Income Need at Retirement
    inflated_income_need = apply_inflation_to_amount(
        base_amount=yearly_income_goal,
        inflation_rate=inflation_rate,
        years=years_to_retirement
    )
    print(f"    Inflated income need: ${yearly_income_goal:,.2f} × (1 + {inflation_rate:.4f})^{years_to_retirement} = ${inflated_income_need:,.2f}/year")
    
    # Step 2: Calculate Guaranteed Income at Retirement
    print(f"\n  Step 2: Calculate Guaranteed Income at Retirement")
    cpp_annual = preprocessed_data.get('cpp_adjusted', 0.0)
    oas_annual = preprocessed_data.get('oas_adjusted', 0.0)
    pension_annual = preprocessed_data.get('pension_amount', 0.0)
    
    print(f"    CPP: ${cpp_annual:,.2f}/year")
    print(f"    OAS: ${oas_annual:,.2f}/year")
    print(f"    Pension: ${pension_annual:,.2f}/year")
    
    total_guaranteed_income = cpp_annual + oas_annual + pension_annual
    print(f"    Total guaranteed income: ${total_guaranteed_income:,.2f}/year")
    
    # Step 3: Calculate Shortfall
    print(f"\n  Step 3: Calculate Shortfall")
    annual_shortfall = max(0.0, inflated_income_need - total_guaranteed_income)
    print(f"    Shortfall = Inflated Income - Guaranteed Income")
    print(f"    Shortfall = ${inflated_income_need:,.2f} - ${total_guaranteed_income:,.2f} = ${annual_shortfall:,.2f}/year")
    
    return annual_shortfall


def calculate_savings_needed_pv(
    annual_income_need: float,
    inflation_rate: float,
    return_rate: float,
    years_in_retirement: int,
    years_to_retirement: int,
    basic_info: BasicInformation,
    preprocessed_data: Dict[str, Any]
) -> float:
    """
    Calculate how much savings needed at retirement to fund the income shortfall.
    
    Uses Present Value of Growing Annuity formula to account for:
    - Income needs growing with inflation
    - Investment returns during retirement
    - Number of years in retirement
    
    INPUTS:
        annual_income_need: float - Income goal in today's dollars
        inflation_rate: float - Annual inflation rate as decimal (e.g., 0.025 for 2.5%)
        return_rate: float - Post-retirement return rate as decimal (e.g., 0.04 for 4%)
        years_in_retirement: int - Years from retirement to life expectancy
        years_to_retirement: int - Years until retirement
        plan: RetirementPlan object for calculating guaranteed income
    
    OUTPUTS:
        float - Present value of savings needed at retirement
        
    FORMULA:
        PV of Growing Annuity:
        PV = PMT × [1 - ((1+g)/(1+r))^n] / (r - g)
        where:
            PMT = annual shortfall
            g = inflation rate
            r = return rate
            n = years in retirement
        
        Real Return = (1 + r) / (1 + g) - 1
        
        If real return ≈ 0: PV = PMT × n (simple calculation)
        Otherwise: PV = PMT × [1 - (1/(1+real_return)^n)] / real_return
    
    EXAMPLE:
        Income need: $50,000/year
        Inflation: 2.5%, Return: 4%, Years: 30
        Shortfall: $30,000/year (after $20k in benefits)
        Result: ~$650,000 needed at retirement
    """
    print("\n" + "="*80)
    print("SAVINGS NEEDED CALCULATION (PRESENT VALUE)")
    print("="*80)
    
    print("\n[INPUT DATA]")
    print(f"  Annual income need (today's dollars): ${annual_income_need:,.2f}")
    print(f"  Inflation rate: {inflation_rate*100:.2f}%")
    print(f"  Return rate (post-retirement): {return_rate*100:.2f}%")
    print(f"  Years in retirement: {years_in_retirement}")
    print(f"  Years to retirement: {years_to_retirement}")
    
    # Calculate annual shortfall at retirement
    annual_shortfall = calculate_annual_shortfall(
        yearly_income_goal=annual_income_need,
        inflation_rate=inflation_rate,
        years_to_retirement=years_to_retirement,
        basic_info=basic_info,
        preprocessed_data=preprocessed_data
    )
    
    # If no shortfall, no savings needed
    if annual_shortfall <= 0:
        print(f"\n[OUTPUT RESULTS]")
        print(f"  No shortfall - government benefits cover everything")
        print(f"  Savings needed: $0.00")
        return 0.0  # Government benefits cover everything
    
    print(f"\n[PROCESSING]")
    print(f"  Annual shortfall at retirement: ${annual_shortfall:,.2f}/year")
    
    # Calculate real return (return adjusted for inflation)
    # Real return accounts for the fact that both income and returns are affected by inflation
    real_return = (1 + return_rate) / (1 + inflation_rate) - 1
    print(f"\n  Calculate Real Return:")
    print(f"    Real Return = (1 + return_rate) / (1 + inflation_rate) - 1")
    print(f"    Real Return = (1 + {return_rate:.4f}) / (1 + {inflation_rate:.4f}) - 1")
    print(f"    Real Return = {real_return:.6f} = {real_return*100:.4f}%")
    
    # Handle edge case when real return is approximately zero
    if abs(real_return) < 0.0001:
        # When real return ≈ 0, use simple calculation
        print(f"\n  Real return ≈ 0, using simple calculation:")
        pv = annual_shortfall * years_in_retirement
        print(f"    PV = Annual Shortfall × Years in Retirement")
        print(f"    PV = ${annual_shortfall:,.2f} × {years_in_retirement} = ${pv:,.2f}")
    else:
        # Present Value of Growing Annuity formula
        # PV = PMT × [1 - (1/(1+real_return)^n)] / real_return
        print(f"\n  Using Present Value of Growing Annuity formula:")
        print(f"    PV = PMT × [1 - (1/(1+real_return)^n)] / real_return")
        print(f"    where PMT = ${annual_shortfall:,.2f}, n = {years_in_retirement}, real_return = {real_return:.6f}")
        
        discount_factor = (1 + real_return) ** years_in_retirement
        numerator = 1 - (1 / discount_factor)
        pv = annual_shortfall * numerator / real_return
        
        print(f"    (1 + real_return)^n = (1 + {real_return:.6f})^{years_in_retirement} = {discount_factor:.6f}")
        print(f"    1 - (1/discount_factor) = 1 - (1/{discount_factor:.6f}) = {numerator:.6f}")
        print(f"    PV = ${annual_shortfall:,.2f} × {numerator:.6f} / {real_return:.6f} = ${pv:,.2f}")
    
    print(f"\n[OUTPUT RESULTS]")
    print(f"  Savings needed at retirement: ${pv:,.2f}")
    print("="*80)
    
    return pv


def calculate_savings_needed(
    basic_info: BasicInformation,
    preprocessed_data: Dict[str, Any]
) -> float:
    """
    Comprehensive function to calculate savings needed using preprocessed data.
    
    INPUTS:
        basic_info: BasicInformation object containing user inputs
        preprocessed_data: Dict from preprocessing layer containing:
            - 'inflation_rate': float
            - 'return_after_retirement': float
            - 'years_to_retirement': int
            - 'years_in_retirement': int
    
    OUTPUTS:
        float - Savings needed at retirement
    """
    print("\n[INPUT DATA]")
    years_to_retirement = preprocessed_data['years_to_retirement']
    years_in_retirement = preprocessed_data['years_in_retirement']
    inflation_rate = preprocessed_data['inflation_rate']
    return_after_retirement = preprocessed_data['return_after_retirement']
    yearly_income_goal_cents = float(basic_info.yearly_income_for_ideal_lifestyle) if basic_info.yearly_income_for_ideal_lifestyle else 0.0
    yearly_income_goal = yearly_income_goal_cents / 100
    
    print(f"  Yearly income goal (cents): {yearly_income_goal_cents:,.2f}")
    print(f"  Yearly income goal (dollars): ${yearly_income_goal:,.2f}")
    print(f"  Inflation rate: {inflation_rate*100:.2f}%")
    print(f"  Return after retirement: {return_after_retirement*100:.2f}%")
    print(f"  Years to retirement: {years_to_retirement}")
    print(f"  Years in retirement: {years_in_retirement}")
    
    savings_needed = calculate_savings_needed_pv(
        annual_income_need=yearly_income_goal,
        inflation_rate=inflation_rate,
        return_rate=return_after_retirement,
        years_in_retirement=years_in_retirement,
        years_to_retirement=years_to_retirement,
        basic_info=basic_info,
        preprocessed_data=preprocessed_data
    )
    
    return savings_needed


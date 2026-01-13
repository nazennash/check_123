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
from ..models import RetirementPlan
from .preprocessing import (
    calculate_cpp_at_start,
    calculate_oas_at_start,
    apply_inflation_to_amount,
)


def calculate_annual_shortfall(
    yearly_income_goal: float,
    inflation_rate: float,
    years_to_retirement: int,
    plan: RetirementPlan
) -> float:
    """
    Calculate the annual income shortfall at retirement (what needs to come from savings).
    
    INPUTS:
        yearly_income_goal: float - Income goal in today's dollars
        inflation_rate: float - Annual inflation rate as decimal (e.g., 0.025 for 2.5%)
        years_to_retirement: int - Years until retirement
        plan: RetirementPlan object containing:
            - cpp_start_age, cpp_amount
            - oas_start_age, oas_amount
            - has_pension, pension_amount
    
    OUTPUTS:
        float - Annual shortfall amount at retirement (in future dollars)
        Returns 0 if government benefits cover everything
        
    PROCESS:
        1. Inflate income goal to retirement year
        2. Calculate guaranteed income (CPP, OAS, Pension)
        3. Calculate shortfall = inflated income - guaranteed income
    """
    # Step 1: Calculate Inflated Income Need at Retirement
    inflated_income_need = apply_inflation_to_amount(
        base_amount=yearly_income_goal,
        inflation_rate=inflation_rate,
        years=years_to_retirement
    )
    
    # Step 2: Calculate Guaranteed Income at Retirement
    cpp_annual = calculate_cpp_at_start(plan)
    oas_annual = calculate_oas_at_start(plan)
    pension_annual = float(plan.pension_amount) if plan.has_pension else 0.0
    
    total_guaranteed_income = cpp_annual + oas_annual + pension_annual
    
    # Step 3: Calculate Shortfall
    annual_shortfall = max(0.0, inflated_income_need - total_guaranteed_income)
    
    return annual_shortfall


def calculate_savings_needed_pv(
    annual_income_need: float,
    inflation_rate: float,
    return_rate: float,
    years_in_retirement: int,
    years_to_retirement: int,
    plan: RetirementPlan
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
    # Calculate annual shortfall at retirement
    annual_shortfall = calculate_annual_shortfall(
        yearly_income_goal=annual_income_need,
        inflation_rate=inflation_rate,
        years_to_retirement=years_to_retirement,
        plan=plan
    )
    
    # If no shortfall, no savings needed
    if annual_shortfall <= 0:
        return 0.0  # Government benefits cover everything
    
    # Calculate real return (return adjusted for inflation)
    # Real return accounts for the fact that both income and returns are affected by inflation
    real_return = (1 + return_rate) / (1 + inflation_rate) - 1
    
    # Handle edge case when real return is approximately zero
    if abs(real_return) < 0.0001:
        # When real return ≈ 0, use simple calculation
        pv = annual_shortfall * years_in_retirement
    else:
        # Present Value of Growing Annuity formula
        # PV = PMT × [1 - (1/(1+real_return)^n)] / real_return
        pv = annual_shortfall * (1 - (1 / ((1 + real_return) ** years_in_retirement))) / real_return
    
    return pv


def calculate_savings_needed(
    plan: RetirementPlan,
    preprocessed_data: Dict[str, Any]
) -> float:
    """
    Comprehensive function to calculate savings needed using preprocessed data.
    
    INPUTS:
        plan: RetirementPlan object containing user inputs
        preprocessed_data: Dict from preprocessing layer containing:
            - 'inflation_rate': float
            - 'return_after_retirement': float
            - 'years_to_retirement': int
            - 'years_in_retirement': int
    
    OUTPUTS:
        float - Savings needed at retirement
    """
    years_to_retirement = preprocessed_data['years_to_retirement']
    years_in_retirement = preprocessed_data['years_in_retirement']
    inflation_rate = preprocessed_data['inflation_rate']
    return_after_retirement = preprocessed_data['return_after_retirement']
    
    return calculate_savings_needed_pv(
        annual_income_need=float(plan.yearly_income_goal),
        inflation_rate=inflation_rate,
        return_rate=return_after_retirement,
        years_in_retirement=years_in_retirement,
        years_to_retirement=years_to_retirement,
        plan=plan
    )


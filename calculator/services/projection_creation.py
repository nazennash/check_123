"""
PROJECTION CREATION
==================

This module handles creating and saving Projection objects to the database
with all calculated results from the retirement planning process.

The Projection Creation module consolidates all results from:
- Accumulation Engine
- Withdrawal Engine
- Savings Needed Calculation
- Gap Analysis
- Monte Carlo Simulation

INPUTS: All calculation results from previous steps
OUTPUTS: Saved Projection object in database
"""

from decimal import Decimal
from typing import List, Dict, Any
from ..models import RetirementPlan, Projection
from .monte_carlo import run_monte_carlo_simulation


def create_projection(
    plan: RetirementPlan,
    projected_savings: float,
    savings_needed: float,
    extra_savings: float,
    is_on_track: bool,
    yearly_breakdown: List[Dict[str, Any]],
    monte_carlo_results: Dict[str, Any],
    run_out_age: int = None
) -> Projection:
    """
    Create and save a Projection object with all calculation results.
    
    INPUTS:
        plan: RetirementPlan object - The retirement plan this projection belongs to
        projected_savings: float - Projected savings at retirement
        savings_needed: float - Savings needed at retirement
        extra_savings: float - Extra savings (positive) or shortfall (negative)
        is_on_track: bool - Whether the plan is on track
        yearly_breakdown: List[Dict] - Complete year-by-year breakdown
        monte_carlo_results: Dict - Results from Monte Carlo simulation
        run_out_age: int or None - Age when money runs out (if applicable)
    
    OUTPUTS:
        Projection object - Saved projection record
        
    NOTE:
        This function creates a new projection. If you want to update an existing
        one, use update_projection() instead.
    """
    projection = Projection.objects.create(
        retirement_plan=plan,
        retirement_age=plan.work_optional_age,
        projected_savings=Decimal(str(round(projected_savings, 2))),
        savings_needed=Decimal(str(round(savings_needed, 2))),
        extra_savings=Decimal(str(round(extra_savings, 2))),
        is_on_track=is_on_track,
        success_probability=Decimal(str(round(monte_carlo_results['success_probability'], 1))),
        percentile_10=Decimal(str(round(monte_carlo_results['percentile_10'], 2))),
        percentile_25=Decimal(str(round(monte_carlo_results['percentile_25'], 2))),
        percentile_50=Decimal(str(round(monte_carlo_results['percentile_50'], 2))),
        percentile_75=Decimal(str(round(monte_carlo_results['percentile_75'], 2))),
        percentile_90=Decimal(str(round(monte_carlo_results['percentile_90'], 2))),
        yearly_breakdown=yearly_breakdown,
        monte_carlo_data=monte_carlo_results,
    )
    
    return projection


def update_projection(
    projection: Projection,
    projected_savings: float,
    savings_needed: float,
    extra_savings: float,
    is_on_track: bool,
    yearly_breakdown: List[Dict[str, Any]],
    monte_carlo_results: Dict[str, Any],
    run_out_age: int = None
) -> Projection:
    """
    Update an existing Projection object with new calculation results.
    
    INPUTS:
        projection: Projection object - Existing projection to update
        projected_savings: float - Projected savings at retirement
        savings_needed: float - Savings needed at retirement
        extra_savings: float - Extra savings (positive) or shortfall (negative)
        is_on_track: bool - Whether the plan is on track
        yearly_breakdown: List[Dict] - Complete year-by-year breakdown
        monte_carlo_results: Dict - Results from Monte Carlo simulation
        run_out_age: int or None - Age when money runs out (if applicable)
    
    OUTPUTS:
        Projection object - Updated projection record
    """
    projection.retirement_age = projection.retirement_plan.work_optional_age
    projection.projected_savings = Decimal(str(round(projected_savings, 2)))
    projection.savings_needed = Decimal(str(round(savings_needed, 2)))
    projection.extra_savings = Decimal(str(round(extra_savings, 2)))
    projection.is_on_track = is_on_track
    projection.success_probability = Decimal(str(round(monte_carlo_results['success_probability'], 1)))
    projection.percentile_10 = Decimal(str(round(monte_carlo_results['percentile_10'], 2)))
    projection.percentile_25 = Decimal(str(round(monte_carlo_results['percentile_25'], 2)))
    projection.percentile_50 = Decimal(str(round(monte_carlo_results['percentile_50'], 2)))
    projection.percentile_75 = Decimal(str(round(monte_carlo_results['percentile_75'], 2)))
    projection.percentile_90 = Decimal(str(round(monte_carlo_results['percentile_90'], 2)))
    projection.yearly_breakdown = yearly_breakdown
    projection.monte_carlo_data = monte_carlo_results
    projection.save()
    
    return projection


def create_or_update_projection(
    plan: RetirementPlan,
    projected_savings: float,
    savings_needed: float,
    extra_savings: float,
    is_on_track: bool,
    yearly_breakdown: List[Dict[str, Any]],
    monte_carlo_results: Dict[str, Any],
    run_out_age: int = None,
    force_recalculate: bool = False
) -> Projection:
    """
    Create a new projection or update existing one.
    
    INPUTS:
        plan: RetirementPlan object - The retirement plan
        projected_savings: float - Projected savings at retirement
        savings_needed: float - Savings needed at retirement
        extra_savings: float - Extra savings (positive) or shortfall (negative)
        is_on_track: bool - Whether the plan is on track
        yearly_breakdown: List[Dict] - Complete year-by-year breakdown
        monte_carlo_results: Dict - Results from Monte Carlo simulation
        run_out_age: int or None - Age when money runs out (if applicable)
        force_recalculate: bool - If True, delete old projections and create new
    
    OUTPUTS:
        Projection object - Created or updated projection record
        
    PROCESS:
        1. If force_recalculate, delete all existing projections
        2. Get existing projection (if any)
        3. Update existing or create new
    """
    # Delete old projections if forcing recalculate
    if force_recalculate:
        plan.projections.all().delete()
        existing_projection = None
    else:
        existing_projection = plan.projections.first()
    
    # Update existing or create new
    if existing_projection:
        return update_projection(
            projection=existing_projection,
            projected_savings=projected_savings,
            savings_needed=savings_needed,
            extra_savings=extra_savings,
            is_on_track=is_on_track,
            yearly_breakdown=yearly_breakdown,
            monte_carlo_results=monte_carlo_results,
            run_out_age=run_out_age
        )
    else:
        return create_projection(
            plan=plan,
            projected_savings=projected_savings,
            savings_needed=savings_needed,
            extra_savings=extra_savings,
            is_on_track=is_on_track,
            yearly_breakdown=yearly_breakdown,
            monte_carlo_results=monte_carlo_results,
            run_out_age=run_out_age
        )


def consolidate_projection_data(
    accumulation_breakdown: List[Dict[str, Any]],
    withdrawal_breakdown: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Consolidate accumulation and withdrawal breakdowns into single yearly breakdown.
    
    INPUTS:
        accumulation_breakdown: List[Dict] - Year-by-year accumulation data
        withdrawal_breakdown: List[Dict] - Year-by-year withdrawal data
    
    OUTPUTS:
        List[Dict] - Complete year-by-year breakdown combining both phases
    """
    return accumulation_breakdown + withdrawal_breakdown


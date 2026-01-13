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
from api.models import BasicInformation
from calculator.models import Projection
from .monte_carlo import run_monte_carlo_simulation


def create_projection(
    basic_info: BasicInformation,
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
        basic_info: BasicInformation object - The retirement plan this projection belongs to
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
    retirement_age = basic_info.work_optional_age if basic_info.work_optional_age else basic_info.current_age + 30
    projection = Projection.objects.create(
        basic_information=basic_info,
        retirement_age=retirement_age,
        projected_savings=Decimal(str(round(projected_savings, 2))),
        savings_needed=Decimal(str(round(savings_needed, 2))),
        extra_savings=Decimal(str(round(extra_savings, 2))),
        is_on_track=is_on_track,
        success_probability=Decimal(str(round(monte_carlo_results.get('success_probability', 0.0), 1))) if monte_carlo_results.get('success_probability') else None,
        percentile_10=Decimal(str(round(monte_carlo_results.get('percentile_10', 0.0), 2))) if monte_carlo_results.get('percentile_10') is not None else None,
        percentile_25=Decimal(str(round(monte_carlo_results.get('percentile_25', 0.0), 2))) if monte_carlo_results.get('percentile_25') is not None else None,
        percentile_50=Decimal(str(round(monte_carlo_results.get('percentile_50', 0.0), 2))) if monte_carlo_results.get('percentile_50') is not None else None,
        percentile_75=Decimal(str(round(monte_carlo_results.get('percentile_75', 0.0), 2))) if monte_carlo_results.get('percentile_75') is not None else None,
        percentile_90=Decimal(str(round(monte_carlo_results.get('percentile_90', 0.0), 2))) if monte_carlo_results.get('percentile_90') is not None else None,
        run_out_age=run_out_age,
        yearly_breakdown=yearly_breakdown,
        monte_carlo_data=monte_carlo_results,
    )
    
    return projection


def update_projection(
    projection: Projection,
    basic_info: BasicInformation,
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
        basic_info: BasicInformation object - The retirement plan
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
    retirement_age = basic_info.work_optional_age if basic_info.work_optional_age else basic_info.current_age + 30
    projection.retirement_age = retirement_age
    projection.projected_savings = Decimal(str(round(projected_savings, 2)))
    projection.savings_needed = Decimal(str(round(savings_needed, 2)))
    projection.extra_savings = Decimal(str(round(extra_savings, 2)))
    projection.is_on_track = is_on_track
    projection.success_probability = Decimal(str(round(monte_carlo_results.get('success_probability', 0.0), 1))) if monte_carlo_results.get('success_probability') else None
    projection.percentile_10 = Decimal(str(round(monte_carlo_results.get('percentile_10', 0.0), 2))) if monte_carlo_results.get('percentile_10') is not None else None
    projection.percentile_25 = Decimal(str(round(monte_carlo_results.get('percentile_25', 0.0), 2))) if monte_carlo_results.get('percentile_25') is not None else None
    projection.percentile_50 = Decimal(str(round(monte_carlo_results.get('percentile_50', 0.0), 2))) if monte_carlo_results.get('percentile_50') is not None else None
    projection.percentile_75 = Decimal(str(round(monte_carlo_results.get('percentile_75', 0.0), 2))) if monte_carlo_results.get('percentile_75') is not None else None
    projection.percentile_90 = Decimal(str(round(monte_carlo_results.get('percentile_90', 0.0), 2))) if monte_carlo_results.get('percentile_90') is not None else None
    projection.run_out_age = run_out_age
    projection.yearly_breakdown = yearly_breakdown
    projection.monte_carlo_data = monte_carlo_results
    projection.save()
    
    return projection


def create_or_update_projection(
    basic_info: BasicInformation,
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
        basic_info: BasicInformation object - The retirement plan
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
        basic_info.projections.all().delete()
        existing_projection = None
    else:
        existing_projection = basic_info.projections.first()
    
    # Update existing or create new
    if existing_projection:
        return update_projection(
            projection=existing_projection,
            basic_info=basic_info,
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
            basic_info=basic_info,
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


# Calculator Services Walkthrough

This document provides a comprehensive walkthrough of all code in the `calculator/services` directory, explaining the architecture, purpose, and interconnections of each module.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Flow](#architecture-flow)
3. [Module Details](#module-details)
   - [orchestrator.py](#orchestratorpy)
   - [preprocessing.py](#preprocessingpy)
   - [accumulation_engine.py](#accumulation_enginepy)
   - [withdrawal_engine.py](#withdrawal_enginepy)
   - [savings_needed.py](#savings_neededpy)
   - [gap_analysis.py](#gap_analysispy)
   - [monte_carlo.py](#monte_carlopy)
   - [monte_carlo_enhanced.py](#monte_carlo_enhancedpy)
   - [projection_creation.py](#projection_creationpy)
   - [utils.py](#utilspy)
4. [Data Flow](#data-flow)
5. [Key Concepts](#key-concepts)

---

## Overview

The `calculator/services` directory contains the core business logic for retirement planning calculations. The system is organized into specialized modules that handle different aspects of retirement planning:

- **Orchestration**: Coordinates the entire calculation process
- **Preprocessing**: Prepares and validates input data
- **Accumulation Phase**: Simulates savings growth until retirement
- **Withdrawal Phase**: Simulates retirement withdrawals
- **Analysis**: Gap analysis and Monte Carlo simulations
- **Persistence**: Saves results to the database

---

## Architecture Flow

```
User Input (BasicInformation)
    ↓
ORCHESTRATOR (main entry point)
    ↓
┌─────────────────────────────────────────┐
│ 1. PREPROCESSING                        │
│    - Validates inputs                   │
│    - Adjusts CPP/OAS amounts            │
│    - Prepares account data              │
│    - Calculates assumptions             │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 2. ACCUMULATION ENGINE                  │
│    - Simulates year-by-year growth      │
│    - Applies contributions              │
│    - Handles life events                │
│    - Projects to retirement age         │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 3. SAVINGS NEEDED CALCULATION           │
│    - Calculates target savings          │
│    - Uses PV of Growing Annuity         │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 4. WITHDRAWAL ENGINE                    │
│    - Simulates retirement withdrawals   │
│    - Applies withdrawal strategy        │
│    - Tracks account balances            │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 5. GAP ANALYSIS                         │
│    - Compares projected vs needed       │
│    - Determines on-track status         │
│    - Finds run-out age                  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 6. MONTE CARLO SIMULATION               │
│    - Runs multiple scenarios            │
│    - Calculates success probability     │
│    - Generates percentiles              │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ 7. PROJECTION CREATION                  │
│    - Consolidates all results           │
│    - Saves to database                  │
└─────────────────────────────────────────┘
    ↓
Results (Projection object)
```

---

## Module Details

### orchestrator.py

**Purpose**: Main entry point that orchestrates the entire retirement calculation process.

**Key Function**:
- `run_retirement_calculation(basic_info, force_recalculate=False)`: Main orchestrator function

**Responsibilities**:
1. Calls preprocessing to prepare data
2. Runs accumulation phase
3. Calculates savings needed
4. Runs withdrawal phase
5. Performs gap analysis
6. Runs Monte Carlo simulation
7. Creates/updates projection
8. Returns comprehensive results

**Input**: `BasicInformation` object
**Output**: Dictionary with all calculation results

**Key Steps** (12 steps total):
1. Preprocessing
2. Accumulation Phase
3. Get Projected Savings at Retirement
4. Get Account Balances at Retirement
5. Calculate Savings Needed
6. Withdrawal Phase
7. Find Run-Out Age
8. Consolidate Yearly Breakdown
9. Gap Analysis
10. Monte Carlo Simulation
11. Calculate Additional Monthly Needed
12. Create or Update Projection

---

### preprocessing.py

**Purpose**: Comprehensive preprocessing layer that prepares all assumptions and data before calculations begin.

**Key Functions**:
- `preprocess_retirement_plan(basic_info, accounts)`: Main preprocessing function
- `calculate_cpp_adjustment(basic_info)`: Adjusts CPP for early/late start
- `calculate_oas_adjustment(basic_info)`: Adjusts OAS for late start
- `calculate_pension_with_indexing(basic_info)`: Handles pension indexing
- `prepare_account_data(accounts)`: Prepares account structures
- `calculate_weighted_portfolio_return(accounts)`: Calculates weighted returns

**Key Sections**:

1. **CPP/OAS Adjustment Processing**
   - CPP: Early start (before 65) reduces by 0.6% per month (max 36%)
   - CPP: Late start (after 65) increases by 0.7% per month (max 42%)
   - OAS: Cannot start before 65, late start increases by 0.6% per month (max 36%)

2. **Pension Calculations**
   - Handles pension indexing at 1.5% annually
   - Pre-calculates indexed amounts for 30 years

3. **Inflation Processing**
   - Processes inflation assumptions
   - Applies inflation to amounts over time

4. **Return Assumptions**
   - Profile returns: Conservative (2%), Balanced (5%), Growth (10%)
   - Calculates weighted portfolio returns
   - Processes post-retirement return assumptions

5. **Withdrawal Strategy Configuration**
   - Strategies: optimized, rrsp, non_registered, tfsa
   - Defines withdrawal order for each strategy

6. **Account Data Preparation**
   - Organizes accounts by type (TFSA, RRSP, NON_REG)
   - Converts balances from cents to dollars
   - Calculates annual contributions

**Output**: Comprehensive dictionary with all processed assumptions

---

### accumulation_engine.py

**Purpose**: Simulates the accumulation phase (current age to retirement age).

**Key Functions**:
- `run_accumulation_phase(basic_info, accounts, years_to_retirement, preprocessed_data)`: Main function
- `simulate_accumulation_year(...)`: Simulates a single year
- `get_projected_savings_at_retirement(breakdown, years_to_retirement)`: Extracts projected savings
- `get_account_balances_at_retirement(breakdown, years_to_retirement)`: Extracts account balances

**Process** (per year):
1. Record starting balances
2. Apply life events (income/expenses)
3. Add monthly contributions (converted to annual)
4. Apply investment growth based on profile returns
5. Calculate ending balances

**Output**: List of year-by-year accumulation data

**Data Structure** (per year):
```python
{
    'age': int,
    'year': int,
    'phase': 'accumulation',
    'starting_balance': float,
    'tfsa': float,
    'rrsp': float,
    'non_reg': float,
    'total_contributions': float,
    'portfolio_growth': float,
    'life_event': float,
    'ending_balance': float,
    'tfsa_ending': float,
    'rrsp_ending': float,
    'non_reg_ending': float
}
```

---

### withdrawal_engine.py

**Purpose**: Simulates the withdrawal phase (retirement age to life expectancy).

**Key Functions**:
- `run_withdrawal_phase(basic_info, account_balances_at_retirement, ...)`: Main function
- `simulate_withdrawal_year(...)`: Simulates a single retirement year
- `find_run_out_age(withdrawal_breakdown)`: Finds when money runs out

**Process** (per year):
1. Calculate inflated income need
2. Calculate guaranteed income (CPP, OAS, Pension)
3. Calculate withdrawal needed from portfolio
4. Apply withdrawal strategy (which accounts to withdraw from)
5. Apply life events
6. Apply growth to remaining balances

**Withdrawal Strategies**:
- **optimized**: NON_REG → RRSP → TFSA (preserves TFSA)
- **rrsp**: RRSP → NON_REG → TFSA
- **non_registered**: NON_REG → TFSA → RRSP
- **tfsa**: TFSA → NON_REG → RRSP

**Output**: List of year-by-year withdrawal data

**Data Structure** (per year):
```python
{
    'age': int,
    'year': int,
    'phase': 'retirement',
    'starting_balance': float,
    'work_optional_income': float,
    'pension': float,
    'cpp': float,
    'oas': float,
    'total_guaranteed_income': float,
    'withdrawal_needed': float,
    'portfolio_growth': float,
    'ending_balance': float,
    'tfsa_ending': float,
    'rrsp_ending': float,
    'non_reg_ending': float
}
```

---

### savings_needed.py

**Purpose**: Calculates how much savings are needed at retirement to fund income shortfall.

**Key Functions**:
- `calculate_savings_needed(basic_info, preprocessed_data)`: Main function
- `calculate_savings_needed_pv(...)`: Uses Present Value formula
- `calculate_annual_shortfall(...)`: Calculates income shortfall

**Formula**: Present Value of Growing Annuity
```
PV = PMT × [1 - ((1+g)/(1+r))^n] / (r - g)
where:
    PMT = annual shortfall
    g = inflation rate
    r = return rate
    n = years in retirement
```

**Process**:
1. Calculate inflated income need at retirement
2. Calculate guaranteed income (CPP + OAS + Pension)
3. Calculate annual shortfall
4. Use PV formula to calculate savings needed

**Output**: Float representing savings needed at retirement

---

### gap_analysis.py

**Purpose**: Performs gap analysis by comparing projected savings vs. needed savings.

**Key Functions**:
- `perform_gap_analysis(...)`: Main function
- `calculate_extra_savings(projected_savings, savings_needed)`: Calculates surplus/shortfall
- `determine_on_track_status(...)`: Determines if plan is on track
- `calculate_additional_monthly_needed(...)`: Calculates additional monthly contribution

**Business Rules**:
- **On Track**: `extra_savings >= 0` AND money lasts to life expectancy
- **Not On Track**: `extra_savings < 0` OR money runs out early

**Output**: Dictionary with gap analysis results
```python
{
    'extra_savings': float,      # Surplus (positive) or shortfall (negative)
    'is_on_track': bool,
    'run_out_age': int or None,
    'shortfall_amount': float,
    'surplus_amount': float
}
```

---

### monte_carlo.py

**Purpose**: Runs Monte Carlo simulation to assess retirement plan success probability.

**Key Function**:
- `run_monte_carlo_simulation(...)`: Runs simulation with default parameters

**Process**:
1. Runs multiple simulations (default 1000)
2. For each simulation:
   - Applies random returns (normal distribution)
   - Simulates withdrawal phase
   - Tracks ending balance
3. Calculates success probability (% of scenarios where money lasts)
4. Calculates percentiles (10th, 25th, 50th, 75th, 90th)

**Output**: Dictionary with simulation results
```python
{
    'success_probability': float,
    'percentile_10': float,
    'percentile_25': float,
    'percentile_50': float,
    'percentile_75': float,
    'percentile_90': float,
    'simulation_results': List[float]
}
```

---

### monte_carlo_enhanced.py

**Purpose**: Enhanced Monte Carlo simulation with time series data (tracks portfolio values at each age).

**Key Function**:
- `run_monte_carlo_with_time_series(...)`: Enhanced simulation with time series

**Differences from monte_carlo.py**:
- Tracks portfolio values at each age (not just final balance)
- Includes accumulation phase in simulation
- Returns time series data for percentile projections over time
- Used by the Monte Carlo API endpoint

**Output**: Dictionary with time series
```python
{
    'success_probability': float,
    'percentile_10': float,
    'percentile_25': float,
    'percentile_50': float,
    'percentile_75': float,
    'percentile_90': float,
    'time_series': {
        'ages': List[int],
        'percentile_10': List[float],
        'percentile_25': List[float],
        'percentile_50': List[float],
        'percentile_75': List[float],
        'percentile_90': List[float]
    }
}
```

---

### projection_creation.py

**Purpose**: Creates and saves Projection objects to the database with all calculation results.

**Key Functions**:
- `create_or_update_projection(...)`: Main function (creates or updates)
- `create_projection(...)`: Creates new projection
- `update_projection(...)`: Updates existing projection
- `consolidate_projection_data(...)`: Combines accumulation + withdrawal breakdowns

**Responsibilities**:
- Consolidates all results from previous steps
- Converts floats to Decimal for database storage
- Handles projection updates vs. creation
- Stores yearly breakdown, Monte Carlo results, percentiles

**Output**: Projection object (Django model instance)

---

### utils.py

**Purpose**: Utility functions used by multiple modules.

**Key Functions**:
- `calculate_life_event_impact(...)`: Calculates impact of life events for a given age
- `apply_withdrawal_strategy(...)`: Applies withdrawal strategy (modifies balances in place)
- `calculate_inflated_income_need(...)`: Calculates inflated income need

**Usage**:
- Used by accumulation_engine.py and withdrawal_engine.py
- Handles common calculations and transformations

---

## Data Flow

### Input Data Structure
```python
BasicInformation {
    - current_age: int
    - work_optional_age: int
    - plan_until_age: int
    - yearly_income_for_ideal_lifestyle: Decimal
    - inflation_rate: Decimal
    - return_after_work_optional: Decimal
    - withdrawal_strategy: str
    - cpp_start_age, cpp_amount_at_age
    - oas_start_age, oas_amount_at_OAS_age
    - has_work_pension: WorkPension object
    - investment_accounts: List[InvestmentAccount]
    - life_events: List[LifeEvent]
}
```

### Preprocessed Data Structure
```python
{
    'years_to_retirement': int,
    'years_in_retirement': int,
    'retirement_age': int,
    'inflation_rate': float,
    'cpp_adjusted': float,
    'oas_adjusted': float,
    'pension_amount': float,
    'return_after_retirement': float,
    'account_data': {
        'account_balances': Dict[str, float],
        'account_contributions': Dict[str, float],
        'account_returns': Dict[str, float]
    },
    # ... many more fields
}
```

### Yearly Breakdown Structure
```python
List[Dict] where each dict represents one year:
{
    'age': int,
    'year': int,
    'phase': 'accumulation' or 'retirement',
    'starting_balance': float,
    'ending_balance': float,
    'tfsa': float,
    'rrsp': float,
    'non_reg': float,
    # ... phase-specific fields
}
```

### Final Output Structure
```python
{
    'projection': Projection object,
    'projected_savings': float,
    'savings_needed': float,
    'extra_savings': float,
    'is_on_track': bool,
    'run_out_age': int or None,
    'success_probability': float,
    'yearly_breakdown': List[Dict],
    'monte_carlo_results': Dict,
    'gap_analysis': Dict
}
```

---

## Key Concepts

### 1. **Two-Phase Model**
- **Accumulation Phase**: Current age → Retirement age (savings growth)
- **Withdrawal Phase**: Retirement age → Life expectancy (retirement withdrawals)

### 2. **Account Types**
- **TFSA**: Tax-Free Savings Account (growth is tax-free)
- **RRSP**: Registered Retirement Savings Plan (tax-deferred)
- **NON_REG**: Non-Registered Account (taxable)

### 3. **Withdrawal Strategies**
Different strategies determine the order of account withdrawals:
- **Optimized**: Preserves TFSA (tax-free growth)
- **RRSP First**: Reduces mandatory withdrawals later
- **Non-Registered First**: Defers RRSP taxation
- **TFSA First**: Maximum flexibility

### 4. **Inflation Adjustment**
- All future values are adjusted for inflation
- Income needs grow with inflation during retirement
- Uses compound inflation: `future_value = base_value × (1 + rate)^years`

### 5. **Monte Carlo Simulation**
- Runs multiple scenarios with random returns
- Uses normal distribution for returns
- Calculates success probability (chance money lasts)
- Provides percentile projections

### 6. **Government Benefits**
- **CPP**: Canada Pension Plan (adjustable for early/late start)
- **OAS**: Old Age Security (cannot start before 65)
- **Pension**: Work pension (indexed annually)

### 7. **Life Events**
- One-time or recurring events
- Can be income or expenses
- Applied to specific account types
- Inflated to future values

### 8. **Investment Profiles**
- **Conservative**: 2% expected return
- **Balanced**: 5% expected return
- **Growth**: 10% expected return
- Used to calculate weighted portfolio returns

---

## Summary

The calculator services directory implements a comprehensive retirement planning system that:

1. **Preprocesses** all inputs and assumptions
2. **Simulates** accumulation phase (savings growth)
3. **Calculates** savings needed at retirement
4. **Simulates** withdrawal phase (retirement withdrawals)
5. **Analyzes** gaps and success probability
6. **Saves** results to database

The modular architecture allows each component to focus on a specific aspect of retirement planning while the orchestrator coordinates the entire process.


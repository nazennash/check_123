import random
from typing import List, Dict, Any, Optional


def run_monte_carlo_simulation(
    accumulation_breakdown: List[Dict[str, Any]],
    withdrawal_breakdown: List[Dict[str, Any]],
    years_to_retirement: int,
    years_in_retirement: int,
    expected_return: float,
    return_volatility: float = 0.15,
    num_simulations: int = 1000,
    include_time_series: bool = False,
    contributions_at_beginning: bool = True
) -> Dict[str, Any]:
    """
    Run Monte Carlo simulation to assess retirement plan success probability.
    
    This function can run in two modes:
    1. Basic mode (include_time_series=False): Only tracks final balances
    2. Enhanced mode (include_time_series=True): Tracks portfolio values at each age
    
    TIMING ASSUMPTION:
    - If contributions_at_beginning=True: Contributions/withdrawals happen at START of year
    - If contributions_at_beginning=False: Contributions/withdrawals happen at END of year
    
    INPUTS:
        accumulation_breakdown: List[Dict] - Year-by-year accumulation data
        withdrawal_breakdown: List[Dict] - Year-by-year withdrawal data
        years_to_retirement: int - Years until retirement
        years_in_retirement: int - Years in retirement
        expected_return: float - Expected annual return as decimal
        return_volatility: float - Standard deviation of returns (default 15%)
        num_simulations: int - Number of Monte Carlo runs (default 1000)
        include_time_series: bool - If True, track portfolio values at each age
        contributions_at_beginning: bool - If True, contributions/withdrawals at start of year
    
    OUTPUTS:
        Dict containing:
        {
            'success_probability': float,  # % of scenarios where money lasts
            'percentile_10': float,         # 10th percentile ending balance
            'percentile_25': float,         # 25th percentile ending balance
            'percentile_50': float,         # 50th percentile (median)
            'percentile_75': float,         # 75th percentile ending balance
            'percentile_90': float,         # 90th percentile ending balance
            'simulation_results': List[float]  # All ending balances (if not time_series)
            'time_series': {                 # Only if include_time_series=True
                'ages': List[int],
                'percentile_10': List[float],
                'percentile_25': List[float],
                'percentile_50': List[float],
                'percentile_75': List[float],
                'percentile_90': List[float]
            }
        }
    """
    print("\n" + "-"*8)
    if include_time_series:
        print("MONTE CARLO SIMULATION (WITH TIME SERIES)")
    else:
        print("MONTE CARLO SIMULATION")
    print("-"*8)
    
    print("\n[INPUT DATA]")
    print(f"  Years to retirement: {years_to_retirement}")
    print(f"  Years in retirement: {years_in_retirement}")
    print(f"  Expected return: {expected_return*100:.2f}%")
    print(f"  Return volatility: {return_volatility*100:.2f}%")
    print(f"  Number of simulations: {num_simulations}")
    print(f"  Include time series: {include_time_series}")
    print(f"  Timing: {'Beginning' if contributions_at_beginning else 'End'} of year")
    print(f"  Accumulation breakdown years: {len(accumulation_breakdown)}")
    print(f"  Withdrawal breakdown years: {len(withdrawal_breakdown)}")
    
    # Validate input lengths match year parameters
    if len(accumulation_breakdown) != years_to_retirement:
        print(f"  WARNING: accumulation_breakdown length ({len(accumulation_breakdown)}) "
              f"doesn't match years_to_retirement ({years_to_retirement})")
    
    if len(withdrawal_breakdown) != years_in_retirement:
        print(f"  WARNING: withdrawal_breakdown length ({len(withdrawal_breakdown)}) "
              f"doesn't match years_in_retirement ({years_in_retirement})")
    
    if not accumulation_breakdown or not withdrawal_breakdown:
        print(f"\n[OUTPUT RESULTS]")
        print(f"  No breakdown data - returning zeros")
        result = {
            'success_probability': 0.0,
            'percentile_10': 0.0,
            'percentile_25': 0.0,
            'percentile_50': 0.0,
            'percentile_75': 0.0,
            'percentile_90': 0.0,
        }
        if include_time_series:
            result['time_series'] = {
                'ages': [],
                'percentile_10': [],
                'percentile_25': [],
                'percentile_50': [],
                'percentile_75': [],
                'percentile_90': []
            }
        else:
            result['simulation_results'] = []
        return result
    
    starting_balance = accumulation_breakdown[0]['starting_balance'] if accumulation_breakdown else 0.0
    retirement_balance = accumulation_breakdown[-1]['ending_balance'] if accumulation_breakdown else 0.0
    
    print(f"\n[PROCESSING]")
    print(f"  Starting balance: ${starting_balance:,.2f}")
    print(f"  Retirement balance: ${retirement_balance:,.2f}")
    print(f"  Running {num_simulations} simulations...")
    
    if include_time_series:
        print(f"  Mode: Enhanced (tracking portfolio value at each age)")
        print(f"  Each simulation:")
        print(f"    1. Simulate accumulation phase (with contributions and life events)")
        print(f"    2. Simulate withdrawal phase (with withdrawals and life events)")
        print(f"    3. Track balance at each age")
    else:
        print(f"  Mode: Basic (tracking final balances only)")
        print(f"  Each simulation:")
        print(f"    1. Start with retirement balance")
        print(f"    2. For each withdrawal year:")
        print(f"       - Check if bankrupt")
        if contributions_at_beginning:
            print(f"       - Subtract withdrawal, add life event (beginning of year)")
            print(f"       - Apply random return to remaining balance")
        else:
            print(f"       - Apply random return to current balance")
            print(f"       - Subtract withdrawal, add life event (end of year)")
        print(f"    3. Track ending balance")
    
    # Store all simulation paths (for time series) or just ending balances
    all_simulation_paths = [] if include_time_series else None
    ending_balances = []
    successful_scenarios = 0
    
    for sim_num in range(num_simulations):
        if include_time_series:
            # Enhanced mode: Simulate both accumulation and withdrawal phases
            balance = starting_balance
            path = []
            
            # Simulate accumulation phase
            for year_data in accumulation_breakdown:
                age = year_data.get('age', 0)
                contributions = year_data.get('total_contributions', 0.0)
                life_event = year_data.get('life_event', 0.0)
                
                # Apply contributions and life events based on timing
                if contributions_at_beginning:
                    balance = balance + contributions + life_event
                    balance = max(0.0, balance)
                
                # Apply random return (no artificial capping)
                random_return = random.gauss(expected_return, return_volatility)
                balance = balance * (1 + random_return)
                balance = max(0.0, balance)
                
                if not contributions_at_beginning:
                    balance = balance + contributions + life_event
                    balance = max(0.0, balance)
                
                path.append({
                    'age': age,
                    'balance': balance
                })
            
            # Continue with withdrawal phase
            for year_data in withdrawal_breakdown:
                age = year_data.get('age', 0)
                withdrawal = year_data.get('withdrawal_needed', 0.0)
                life_event = year_data.get('life_event', 0.0)
                
                # Check if bankrupt before processing this year
                if balance <= 0:
                    # Track bankrupt state for this age
                    path.append({
                        'age': age,
                        'balance': 0.0
                    })
                    continue
                
                # Apply withdrawal and life events based on timing
                if contributions_at_beginning:
                    balance = balance - withdrawal + life_event
                    balance = max(0.0, balance)
                
                # Apply random return
                random_return = random.gauss(expected_return, return_volatility)
                balance = balance * (1 + random_return)
                balance = max(0.0, balance)
                
                if not contributions_at_beginning:
                    balance = balance - withdrawal + life_event
                    balance = max(0.0, balance)
                
                path.append({
                    'age': age,
                    'balance': balance
                })
            
            all_simulation_paths.append(path)
            final_balance = path[-1]['balance'] if path else 0.0
        else:
            # Basic mode: Only simulate withdrawal phase
            balance = retirement_balance
            
            for year_data in withdrawal_breakdown:
                # Check for bankruptcy
                if balance <= 0:
                    break
                
                withdrawal = year_data.get('withdrawal_needed', 0.0)
                life_event = year_data.get('life_event', 0.0)
                
                # Apply based on timing assumption
                if contributions_at_beginning:
                    balance = balance - withdrawal + life_event
                    balance = max(0.0, balance)
                
                # Apply random return
                random_return = random.gauss(expected_return, return_volatility)
                balance = balance * (1 + random_return)
                balance = max(0.0, balance)
                
                if not contributions_at_beginning:
                    balance = balance - withdrawal + life_event
                    balance = max(0.0, balance)
            
            final_balance = balance
        
        ending_balances.append(final_balance)
        if final_balance > 0:
            successful_scenarios += 1
        
        if (sim_num + 1) % 1000 == 0 and num_simulations > 1000:
            print(f"    Completed {sim_num + 1} simulations...")
    
    print(f"  Simulations complete")
    print(f"  Successful scenarios: {successful_scenarios} / {num_simulations}")
    
    # Calculate percentiles for final balances
    ending_balances.sort()
    
    def percentile(data: List[float], p: float) -> float:
        """Calculate percentile using linear interpolation."""
        if not data:
            return 0.0
        n = len(data)
        k = (n - 1) * p
        f = int(k)
        c = k - f
        if f + 1 < n:
            return data[f] + c * (data[f + 1] - data[f])
        return data[f]
    
    print(f"\n  Calculating percentiles...")
    success_probability = (successful_scenarios / num_simulations) * 100
    percentile_10 = percentile(ending_balances, 0.10)
    percentile_25 = percentile(ending_balances, 0.25)
    percentile_50 = percentile(ending_balances, 0.50)
    percentile_75 = percentile(ending_balances, 0.75)
    percentile_90 = percentile(ending_balances, 0.90)
    
    print(f"    Success probability: {success_probability:.2f}%")
    print(f"    10th percentile: ${percentile_10:,.2f}")
    print(f"    25th percentile: ${percentile_25:,.2f}")
    print(f"    50th percentile (median): ${percentile_50:,.2f}")
    print(f"    75th percentile: ${percentile_75:,.2f}")
    print(f"    90th percentile: ${percentile_90:,.2f}")
    
    # Build result dictionary
    result = {
        'success_probability': round(success_probability, 2),
        'percentile_10': round(percentile_10, 2),
        'percentile_25': round(percentile_25, 2),
        'percentile_50': round(percentile_50, 2),
        'percentile_75': round(percentile_75, 2),
        'percentile_90': round(percentile_90, 2),
    }
    
    if include_time_series:
        # Calculate percentile projections over time
        print(f"\n  Calculating time series percentiles (portfolio value at each age)...")
        
        # Find all unique ages across all paths
        all_ages = set()
        for path in all_simulation_paths:
            for point in path:
                all_ages.add(point['age'])
        
        ages = sorted(all_ages)
        
        # Initialize lists for each age
        age_balance_map = {age: [] for age in ages}
        
        # Collect balances for each age
        for path in all_simulation_paths:
            # Create a dictionary of age->balance for this simulation
            sim_balances = {point['age']: point['balance'] for point in path}
            
            # Fill in missing ages with last known balance or 0
            last_balance = 0.0
            for age in ages:
                if age in sim_balances:
                    last_balance = sim_balances[age]
                age_balance_map[age].append(last_balance)
        
        # Calculate percentiles for each age
        percentile_10_series = []
        percentile_25_series = []
        percentile_50_series = []
        percentile_75_series = []
        percentile_90_series = []
        
        for age in ages:
            balances = sorted(age_balance_map[age])
            percentile_10_series.append(percentile(balances, 0.10))
            percentile_25_series.append(percentile(balances, 0.25))
            percentile_50_series.append(percentile(balances, 0.50))
            percentile_75_series.append(percentile(balances, 0.75))
            percentile_90_series.append(percentile(balances, 0.90))
        
        print(f"    Calculated percentiles for {len(ages)} ages")
        print(f"    Age range: {ages[0]} to {ages[-1]}")
        
        result['time_series'] = {
            'ages': ages,
            'percentile_10': [round(b, 2) for b in percentile_10_series],
            'percentile_25': [round(b, 2) for b in percentile_25_series],
            'percentile_50': [round(b, 2) for b in percentile_50_series],
            'percentile_75': [round(b, 2) for b in percentile_75_series],
            'percentile_90': [round(b, 2) for b in percentile_90_series]
        }
    else:
        result['simulation_results'] = ending_balances[:100]  # Limit to first 100 for storage
    
    print(f"\n[OUTPUT RESULTS]")
    print(f"  success_probability: {result['success_probability']:.2f}%")
    print(f"  percentile_10: ${result['percentile_10']:,.2f}")
    print(f"  percentile_25: ${result['percentile_25']:,.2f}")
    print(f"  percentile_50: ${result['percentile_50']:,.2f}")
    print(f"  percentile_75: ${result['percentile_75']:,.2f}")
    print(f"  percentile_90: ${result['percentile_90']:,.2f}")
    if include_time_series:
        print(f"  time_series: {len(result['time_series']['ages'])} ages with percentile data")
    print("-"*8)
    
    return result


def run_monte_carlo_with_time_series(
    accumulation_breakdown: List[Dict[str, Any]],
    withdrawal_breakdown: List[Dict[str, Any]],
    years_to_retirement: int,
    years_in_retirement: int,
    expected_return: float,
    return_volatility: float = 0.15,
    num_simulations: int = 1000,
    contributions_at_beginning: bool = True
) -> Dict[str, Any]:
    """
    Alias for run_monte_carlo_simulation with include_time_series=True.
    Maintained for backward compatibility.
    """
    return run_monte_carlo_simulation(
        accumulation_breakdown=accumulation_breakdown,
        withdrawal_breakdown=withdrawal_breakdown,
        years_to_retirement=years_to_retirement,
        years_in_retirement=years_in_retirement,
        expected_return=expected_return,
        return_volatility=return_volatility,
        num_simulations=num_simulations,
        include_time_series=True,
        contributions_at_beginning=contributions_at_beginning
    )
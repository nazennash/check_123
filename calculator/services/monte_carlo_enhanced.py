import random
from typing import List, Dict, Any
from decimal import Decimal


def run_monte_carlo_with_time_series(
    accumulation_breakdown: List[Dict[str, Any]],
    withdrawal_breakdown: List[Dict[str, Any]],
    years_to_retirement: int,
    years_in_retirement: int,
    expected_return: float,
    return_volatility: float = 0.15,
    num_simulations: int = 1000
) -> Dict[str, Any]:
    """
    Run Monte Carlo simulation with time series data for percentile projections over time.
    
    This enhanced version tracks portfolio values at each age, not just final balances.
    
    INPUTS:
        accumulation_breakdown: List[Dict] - Year-by-year accumulation data
        withdrawal_breakdown: List[Dict] - Year-by-year withdrawal data
        years_to_retirement: int - Years until retirement
        years_in_retirement: int - Years in retirement
        expected_return: float - Expected annual return as decimal
        return_volatility: float - Standard deviation of returns (default 15%)
        num_simulations: int - Number of Monte Carlo runs (default 1000)
    
    OUTPUTS:
        Dict containing:
        {
            'success_probability': float,
            'percentile_10': float,  # Final balance at retirement
            'percentile_25': float,
            'percentile_50': float,
            'percentile_75': float,
            'percentile_90': float,
            'time_series': {
                'ages': List[int],
                'percentile_10': List[float],  # Portfolio value at each age
                'percentile_25': List[float],
                'percentile_50': List[float],
                'percentile_75': List[float],
                'percentile_90': List[float]
            }
        }
    """
    print("\n" + "="*80)
    print("MONTE CARLO SIMULATION (ENHANCED WITH TIME SERIES)")
    print("="*80)
    
    print("\n[INPUT DATA]")
    print(f"  Years to retirement: {years_to_retirement}")
    print(f"  Years in retirement: {years_in_retirement}")
    print(f"  Expected return: {expected_return*100:.2f}%")
    print(f"  Return volatility: {return_volatility*100:.2f}%")
    print(f"  Number of simulations: {num_simulations}")
    print(f"  Accumulation breakdown years: {len(accumulation_breakdown)}")
    print(f"  Withdrawal breakdown years: {len(withdrawal_breakdown)}")
    
    if not accumulation_breakdown or not withdrawal_breakdown:
        print(f"\n[OUTPUT RESULTS]")
        print(f"  No breakdown data - returning zeros")
        return {
            'success_probability': 0.0,
            'percentile_10': 0.0,
            'percentile_25': 0.0,
            'percentile_50': 0.0,
            'percentile_75': 0.0,
            'percentile_90': 0.0,
            'time_series': {
                'ages': [],
                'percentile_10': [],
                'percentile_25': [],
                'percentile_50': [],
                'percentile_75': [],
                'percentile_90': []
            }
        }
    
    starting_balance = accumulation_breakdown[0]['starting_balance'] if accumulation_breakdown else 0.0
    retirement_balance = accumulation_breakdown[-1]['ending_balance'] if accumulation_breakdown else 0.0
    
    print(f"\n[PROCESSING]")
    print(f"  Starting balance: ${starting_balance:,.2f}")
    print(f"  Retirement balance: ${retirement_balance:,.2f}")
    print(f"  Running {num_simulations} simulations with time series tracking...")
    print(f"  Each simulation tracks portfolio value at each age (not just final balance)")
    
    # Get ages from breakdown
    all_ages = []
    for year_data in accumulation_breakdown:
        all_ages.append(year_data.get('age', 0))
    for year_data in withdrawal_breakdown:
        all_ages.append(year_data.get('age', 0))
    
    # Store all simulation paths (portfolio value at each age)
    all_simulation_paths = []
    ending_balances = []
    successful_scenarios = 0
    
    for sim_num in range(num_simulations):
        # Start with accumulation phase
        balance = starting_balance
        path = []
        
        # Simulate accumulation phase
        for year_data in accumulation_breakdown:
            age = year_data.get('age', 0)
            contributions = year_data.get('total_contributions', 0.0)
            life_event = year_data.get('life_event', 0.0)
            
            # Apply contributions and life events
            balance = balance + contributions + life_event
            
            # Apply random return
            random_return = random.gauss(expected_return, return_volatility)
            random_return = max(-0.5, min(0.5, random_return))
            balance = balance * (1 + random_return)
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
            
            # Apply withdrawal and life events
            balance = balance - withdrawal + life_event
            balance = max(0.0, balance)
            
            # Apply random return
            random_return = random.gauss(expected_return, return_volatility)
            random_return = max(-0.5, min(0.5, random_return))
            balance = balance * (1 + random_return)
            balance = max(0.0, balance)
            
            path.append({
                'age': age,
                'balance': balance
            })
            
            if balance <= 0:
                break
        
        all_simulation_paths.append(path)
        final_balance = path[-1]['balance'] if path else 0.0
        ending_balances.append(final_balance)
        
        if final_balance > 0:
            successful_scenarios += 1
        
        if (sim_num + 1) % 1000 == 0:
            print(f"    Completed {sim_num + 1} simulations...")
    
    print(f"  Simulations complete")
    print(f"  Successful scenarios: {successful_scenarios} / {num_simulations}")
    
    # Calculate percentiles for final balances
    ending_balances.sort()
    
    def percentile(data: List[float], p: float) -> float:
        if not data:
            return 0.0
        k = (len(data) - 1) * p
        f = int(k)
        c = k - f
        if f + 1 < len(data):
            return data[f] + c * (data[f + 1] - data[f])
        return data[f]
    
    success_probability = (successful_scenarios / num_simulations) * 100
    
    print(f"\n  Calculating percentiles for final balances...")
    percentile_10_final = percentile(ending_balances, 0.10)
    percentile_25_final = percentile(ending_balances, 0.25)
    percentile_50_final = percentile(ending_balances, 0.50)
    percentile_75_final = percentile(ending_balances, 0.75)
    percentile_90_final = percentile(ending_balances, 0.90)
    
    print(f"    Success probability: {success_probability:.2f}%")
    print(f"    10th percentile: ${percentile_10_final:,.2f}")
    print(f"    50th percentile (median): ${percentile_50_final:,.2f}")
    print(f"    90th percentile: ${percentile_90_final:,.2f}")
    
    # Calculate percentile projections over time
    print(f"\n  Calculating time series percentiles (portfolio value at each age)...")
    # Group balances by age
    age_balance_map = {}
    for path in all_simulation_paths:
        for point in path:
            age = point['age']
            balance = point['balance']
            if age not in age_balance_map:
                age_balance_map[age] = []
            age_balance_map[age].append(balance)
    
    # Calculate percentiles for each age
    ages = sorted(age_balance_map.keys())
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
    
    result = {
        'success_probability': round(success_probability, 2),
        'percentile_10': round(percentile_10_final, 2),
        'percentile_25': round(percentile_25_final, 2),
        'percentile_50': round(percentile_50_final, 2),
        'percentile_75': round(percentile_75_final, 2),
        'percentile_90': round(percentile_90_final, 2),
        'time_series': {
            'ages': ages,
            'percentile_10': [round(b, 2) for b in percentile_10_series],
            'percentile_25': [round(b, 2) for b in percentile_25_series],
            'percentile_50': [round(b, 2) for b in percentile_50_series],
            'percentile_75': [round(b, 2) for b in percentile_75_series],
            'percentile_90': [round(b, 2) for b in percentile_90_series]
        }
    }
    
    print(f"\n[OUTPUT RESULTS]")
    print(f"  success_probability: {result['success_probability']:.2f}%")
    print(f"  percentile_10: ${result['percentile_10']:,.2f}")
    print(f"  percentile_25: ${result['percentile_25']:,.2f}")
    print(f"  percentile_50: ${result['percentile_50']:,.2f}")
    print(f"  percentile_75: ${result['percentile_75']:,.2f}")
    print(f"  percentile_90: ${result['percentile_90']:,.2f}")
    print(f"  time_series: {len(result['time_series']['ages'])} ages with percentile data")
    print("="*80)
    
    return result


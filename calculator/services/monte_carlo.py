import random
from typing import List, Dict, Any
import statistics


def run_monte_carlo_simulation(
    accumulation_breakdown: List[Dict[str, Any]],
    withdrawal_breakdown: List[Dict[str, Any]],
    years_to_retirement: int,
    years_in_retirement: int,
    expected_return: float,
    return_volatility: float = 0.15,
    num_simulations: int = 1000
) -> Dict[str, Any]:
    """
    Run Monte Carlo simulation to assess retirement plan success probability.
    
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
            'success_probability': float,  # % of scenarios where money lasts
            'percentile_10': float,         # 10th percentile ending balance
            'percentile_25': float,         # 25th percentile ending balance
            'percentile_50': float,         # 50th percentile (median)
            'percentile_75': float,         # 75th percentile ending balance
            'percentile_90': float,         # 90th percentile ending balance
            'simulation_results': List[float]  # All ending balances
        }
    """
    print("\n" + "="*80)
    print("MONTE CARLO SIMULATION")
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
            'simulation_results': []
        }
    
    starting_balance = accumulation_breakdown[0]['starting_balance'] if accumulation_breakdown else 0.0
    retirement_balance = accumulation_breakdown[-1]['ending_balance'] if accumulation_breakdown else 0.0
    
    print(f"\n[PROCESSING]")
    print(f"  Starting balance: ${starting_balance:,.2f}")
    print(f"  Retirement balance: ${retirement_balance:,.2f}")
    print(f"  Running {num_simulations} simulations...")
    print(f"  Each simulation:")
    print(f"    1. Start with retirement balance")
    print(f"    2. For each withdrawal year:")
    print(f"       - Generate random return (normal distribution: mean={expected_return*100:.2f}%, std={return_volatility*100:.2f}%)")
    print(f"       - Apply return: balance = balance × (1 + random_return)")
    print(f"       - Subtract withdrawal: balance = balance - withdrawal")
    print(f"    3. Track ending balance")
    
    ending_balances = []
    successful_scenarios = 0
    
    for sim_num in range(num_simulations):
        balance = retirement_balance
        
        for year_data in withdrawal_breakdown:
            withdrawal = year_data.get('withdrawal_needed', 0.0)
            
            random_return = random.gauss(expected_return, return_volatility)
            random_return = max(-0.5, min(0.5, random_return))
            
            balance = balance * (1 + random_return) - withdrawal
            balance = max(0.0, balance)
            
            if balance <= 0:
                break
        
        ending_balances.append(balance)
        if balance > 0:
            successful_scenarios += 1
        
        if (sim_num + 1) % 1000 == 0:
            print(f"    Completed {sim_num + 1} simulations...")
    
    print(f"  Simulations complete")
    print(f"  Successful scenarios: {successful_scenarios} / {num_simulations}")
    
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
    
    result = {
        'success_probability': round(success_probability, 2),
        'percentile_10': round(percentile_10, 2),
        'percentile_25': round(percentile_25, 2),
        'percentile_50': round(percentile_50, 2),
        'percentile_75': round(percentile_75, 2),
        'percentile_90': round(percentile_90, 2),
        'simulation_results': ending_balances[:100]
    }
    
    print(f"\n[OUTPUT RESULTS]")
    print(f"  success_probability: {result['success_probability']:.2f}%")
    print(f"  percentile_10: ${result['percentile_10']:,.2f}")
    print(f"  percentile_25: ${result['percentile_25']:,.2f}")
    print(f"  percentile_50: ${result['percentile_50']:,.2f}")
    print(f"  percentile_75: ${result['percentile_75']:,.2f}")
    print(f"  percentile_90: ${result['percentile_90']:,.2f}")
    print("="*80)
    
    return result


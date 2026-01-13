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
    if not accumulation_breakdown or not withdrawal_breakdown:
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
    
    ending_balances = []
    successful_scenarios = 0
    
    for _ in range(num_simulations):
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
    
    return {
        'success_probability': round(success_probability, 2),
        'percentile_10': round(percentile(ending_balances, 0.10), 2),
        'percentile_25': round(percentile(ending_balances, 0.25), 2),
        'percentile_50': round(percentile(ending_balances, 0.50), 2),
        'percentile_75': round(percentile(ending_balances, 0.75), 2),
        'percentile_90': round(percentile(ending_balances, 0.90), 2),
        'simulation_results': ending_balances[:100]
    }


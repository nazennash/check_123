# Monte Carlo API Documentation

## Endpoint

**POST /api/monte-carlo/<client_id>/**

Runs a new Monte Carlo simulation with custom configuration parameters.

**GET /api/monte-carlo/<client_id>/**

Returns existing Monte Carlo simulation results (if available).

## Request Body (POST)

All parameters are required and should be sent directly in the request body (not nested):

```json
{
  "num_simulations": 10000,
  "market_volatility": "historical",
  "expected_annual_return": 5.5,
  "standard_deviation": 15.0,
  "inflation_rate": 2.5,
  "sequence_of_returns_risk": "enabled"
}
```

### Parameter Details

1. **num_simulations** (integer, required)
   - Allowed values: `5000`, `10000`, or `25000` only
   - Number of Monte Carlo simulation runs

2. **market_volatility** (string, required)
   - Allowed values: `"conservative"`, `"high_volatility"`, or `"historical"` only
   - Maps to volatility:
     - `conservative`: 10% volatility
     - `high_volatility`: 20% volatility
     - `historical`: 15% volatility (default)

3. **expected_annual_return** (float, required)
   - Any number (percentage, e.g., 5.5 for 5.5%)
   - Expected annual return for the portfolio

4. **standard_deviation** (float, required)
   - Any number (percentage, e.g., 15.0 for 15%)
   - Standard deviation/volatility of returns
   - Note: If `market_volatility` is provided, this can override the default volatility

5. **inflation_rate** (float, required)
   - Any number (percentage, e.g., 2.5 for 2.5%)
   - Annual inflation rate

6. **sequence_of_returns_risk** (string, required)
   - Allowed values: `"enabled"` or `"disabled"` only
   - Whether to account for sequence of returns risk

## Response Structure

```json
{
  "client_id": 12345,
  "projection_id": 1,
  "retirement_goal": 1000000.00,
  "retirement_age": 65,
  "current_age": 35,
  "success_probability": 90.0,
  "configuration": {
    "num_simulations": 10000,
    "market_volatility": "historical",
    "expected_annual_return": 5.5,
    "standard_deviation": 15.0,
    "inflation_rate": 2.5,
    "sequence_of_returns_risk": "enabled",
    "volatility_model": "normal_distribution"
  },
  "percentiles_at_retirement": {
    "percentile_10": 894000.00,
    "percentile_25": 1200000.00,
    "percentile_50": 1500000.00,
    "percentile_75": 1800000.00,
    "percentile_90": 2200000.00
  },
  "time_series": {
    "ages": [35, 36, 37, ...],
    "percentile_10": [200000, 210000, ...],
    "percentile_25": [200000, 215000, ...],
    "percentile_50": [200000, 220000, ...],
    "percentile_75": [200000, 225000, ...],
    "percentile_90": [200000, 230000, ...]
  },
  "insights": [...],
  "chart_data": {...}
}
```

## Usage Examples

### POST Request (Run New Simulation)

```bash
curl -X POST http://localhost:8000/api/monte-carlo/12345/ \
  -H "Content-Type: application/json" \
  -d '{
    "num_simulations": 10000,
    "market_volatility": "historical",
    "expected_annual_return": 5.5,
    "standard_deviation": 15.0,
    "inflation_rate": 2.5,
    "sequence_of_returns_risk": "enabled"
  }'
```

### GET Request (Retrieve Existing Results)

```bash
curl -X GET http://localhost:8000/api/monte-carlo/12345/
```

## Error Responses

### 400 Bad Request
- Missing required parameter
- Invalid value for `num_simulations` (not 5000, 10000, or 25000)
- Invalid value for `market_volatility` (not conservative, high_volatility, or historical)
- Invalid value for `sequence_of_returns_risk` (not enabled or disabled)

### 404 Not Found
- Client ID not found
- No projection found (need to run calculation first)

## Notes

- The simulation uses the enhanced Monte Carlo function that tracks portfolio values at each age
- Results are saved to the projection and can be retrieved with GET
- The time series data provides percentile projections over time for chart visualization
- All percentage values in the request should be sent as numbers (e.g., 5.5 for 5.5%, not 0.055)


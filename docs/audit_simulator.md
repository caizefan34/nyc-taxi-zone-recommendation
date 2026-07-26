# Dynamic Simulator Deep Audit

## State Components

| Component | Exists | Location |
|-----------|--------|----------|
| DriverState | ✅ | src/simulator/v2/state.py (10 fields: revenue, fuel, trips, idle, location, etc.) |
| ZoneState | ✅ | src/simulator/v2/state.py (9 fields: demand, supply, trips, traffic, weather, etc.) |
| EnvironmentState | ✅ | src/simulator/v2/state.py (drivers dict, zones dict, time, total_taxis, total_trips) |

## Action Space

| Action | Implementation | Status |
|--------|---------------|--------|
| move | Strategy fn returns target zone (1..263) | ✅ Strategy = Callable[[datetime, int, EnvironmentState], int] |
| stay | Driver returns current location zone | ✅ Used as baseline in benchmarks |

## Reward Components

| Component | Implementation | Status |
|-----------|---------------|--------|
| Income / Fare | reward.py::income(fare) | ✅ |
| Fuel Cost | reward.py::fuel_cost(distance) | ✅ $0.65/mile |
| Travel Time Cost | reward.py::travel_time_cost(minutes) | ✅ $0.30/min |
| Competition Penalty | reward.py::competition_penalty(n_drivers) | ✅ $0.50 * max(0, n-1) |
| Risk Penalty | reward.py::risk_penalty(pickup_prob) | ✅ 2.0 * (1 - prob) |

## Supply-Demand Feedback (Critical Check)

Tested: `compute_pickup_probability(100.0, 1) = 0.7143 > (100.0, 10) = 0.5965 > (100.0, 50) = 0.5349`

| Step | Effect | Verified |
|------|--------|----------|
| More drivers → zone supply increases | ✅ | DynamicSimulator._build_initial_state sets supply |
| Higher supply → pickup probability decreases | ✅ | dynamics.py::compute_pickup_probability() has competition logic |
| Lower pickup prob → fewer trips → lower reward | ✅ | Engine.run() uses prob in Bernoulli trial |
| Competition penalty directly reduces reward | ✅ | reward.py::competition_penalty() |
| Demand responds to traffic/weather/holidays | ✅ | dynamics.py::compute_effective_demand() |
| Trip inventory depletes over time | ✅ | zs.trips_remaining decremented on success |

**Verdict:** NOT fixed demand + agent movement. Real supply-demand feedback loop is present.

**Score: 10/10**

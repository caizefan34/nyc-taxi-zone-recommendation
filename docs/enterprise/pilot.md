# Enterprise / Research Pilot

The open-source project provides the research and engineering foundation for urban mobility decision intelligence.

## For Organizations Interested In

- **Fleet optimization** — Dynamic repositioning recommendations for taxi, ride-hail, delivery, or autonomous fleets
- **Mobility forecasting** — Spatiotemporal demand prediction with leakage-safe temporal splits
- **Controlled pilot deployment** — Private deployment with shadow evaluation before going live
- **Custom city integration** — Adapt the platform to new cities beyond NYC
- **Decision-aware research** — Study the gap between forecast accuracy and decision quality

## Current Platform Status

| Capability | Status |
|---|---|
| Demand forecasting (LightGBM, XGBoost, Ensemble) | Research-grade |
| Zone recommendation (Two-Step, DQN) | Research-grade |
| Multi-agent simulation | Research-grade |
| REST API (FastAPI) | Prototype |
| Docker deployment | Available |
| Shadow evaluation | Framework ready |
| A/B testing | Framework ready |
| Cross-city abstraction | Framework ready |
| Real-time data integration | Not available |
| Production monitoring | Not available |
| Fleet dispatch integration | Not available |

## Getting Started

1. **Clone and install**
   ```bash
   git clone https://github.com/caizefan34/urban-mobility-ai.git
   cd urban-mobility-ai
   pip install -e ".[dev]"
   ```

2. **Run the API**
   ```bash
   uvicorn src.api.main:app --host 0.0.0.0 --port 8000
   ```

3. **Try the demo**
   ```bash
   docker compose up
   ```

4. **Review the architecture**
   See [architecture](../architecture.md)

## Pilot Documentation

- [Pilot Overview](pilot.md) — What a pilot deployment looks like
- [Deployment Guide](deployment.md) — Private deployment instructions
- [Data Requirements](data_requirements.md) — What data you need
- [Security Considerations](security.md) — Security and privacy notes
- [Evaluation Protocol](evaluation_protocol.md) — How to evaluate in production

## Important Caveats

- This is a **research prototype**, not a production dispatch system
- All benchmark results are **simulation-based**, not production evidence
- No real-world A/B tests have been conducted
- The platform has **not been deployed** with a real fleet

We are interested in research collaborations and controlled pilot studies.

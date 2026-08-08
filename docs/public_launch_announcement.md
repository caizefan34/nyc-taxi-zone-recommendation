# Public Launch Announcement

> **Status**: Announcement prepared. Not yet published.

---

## Dynamic Urban Mobility Decision System v2.1 — Public Launch

We are excited to announce the public launch of the **Dynamic Urban Mobility Decision System**, an open-source benchmark platform for AI-driven taxi repositioning research.

### The Problem

NYC taxi drivers spend 30-50% of their shift cruising without passengers. Where should they go next? This is fundamentally a **sequential decision problem under uncertainty** — the kind ML excels at solving.

### What We Built

A fully open-source pipeline:

- **Leakage-safe demand forecasting** (LightGBM/XGBoost + GraphSAGE/GAT)
- **Multi-agent simulator** with finite demand and explicit competition
- **MDP-based planning + DQN policies** (Two-Step Horizon: NDCG@3 0.9565)
- **Reproducible benchmark** (328 tests, all metrics checked in)

### Try It Now

- **Live Demo**: https://caizefan34.github.io/urban-mobility-ai/web/
- **Documentation**: https://caizefan34.github.io/urban-mobility-ai/docs/
- **Repository**: https://github.com/caizefan34/urban-mobility-ai

### Reproduce Everything

```bash
git clone https://github.com/caizefan34/urban-mobility-ai.git
cd urban-mobility-ai
python scripts/verify_reproduction.py
```

### Contribute

- Submit your model to our [public leaderboard](docs/leaderboard.md)
- Report issues or suggest features
- Share feedback via our [feedback template](docs/external_feedback_template.md)

### Important Limitations

- All results are **simulator outcomes** — not production revenue
- Models are NYC-specific; cross-city validation is planned
- This is a **research platform**, not a production system

### Contact

- GitHub: https://github.com/caizefan34/urban-mobility-ai
- Email: caizefan@sjtu.edu.cn

---

*MIT License. Built for reproducible research.*

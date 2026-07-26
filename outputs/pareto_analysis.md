# Pareto Analysis: Revenue vs Risk vs Competition

**Generated:** 2026-07-26

> This analysis compares each method across three competing objectives.
> No single method dominates on all objectives — trade-offs are inherent.

---

## Methodology

Each policy is scored on three axes:

- **Revenue**: Average driver revenue (higher is better)
- **Risk**: Competition + risk penalty (lower is better)
- **Competition**: Competition penalty density (lower is better)

Revenue and risk are inherently opposed: higher revenue usually requires
operating in high-demand zones where competition and risk are higher.

---

## Frontier Table

| Method | Revenue | Risk (Penalty) | Competition Penalty | Dominance
|---|---:|---:|---:|:---
| MF Single Agent | $1976.30 | $0.00 | $0.0000 | Pareto-optimal |
| Double DQN (v2 sim) | $1965.45 | $1112.52 | $32.5000 |  |
| DQN (v2 sim) | $1867.81 | $1112.56 | $42.0000 |  |
| MF Multi Agent | $1867.81 | $4.20 | $4.2000 |  |
| IQL (Offline) | $819.17 | $0.00 | $0.0000 | Min risk |
| MF Mean Field | $225.75 | $0.00 | $0.0000 | Min risk |

---

## 2D Frontier Charts (ASCII)

### Revenue vs Risk

    1113 |                         . DQN (v2 sim)                                       
    1001 |              Double DQN (            .                                       
     890 |                         .                                                    
     779 |                                                                              
     668 |                                                                              
     556 |                                                                              
     445 |                                                                              
     334 |                                                                              
     223 |                                                                              
     111 |            .                                      .            .            .
    Risk +————————————————————————————————————————————————————————————————————————————————————
 Revenue    Revenue

---

## Key Findings

1. **Highest revenue**: MF Single Agent ($1976.30) — top-line performer but carries competition risk.
2. **Lowest risk**: MF Single Agent ($0.00 penalty) — safest strategy.
3. **Gap**: Revenue spread is $1750.55; risk spread is $1112.56.
4. **No free lunch**: The method with highest revenue also has the highest competition penalty.
5. **IQL (Offline)**: Lower revenue but no competition penalty — reflects evaluation on synthetic data.
6. **Mean Field**: Trades off between single-agent overestimation and multi-agent realism.

---

## Limitations

- Revenue and risk are measured inside the v2 dynamic simulator, not in deployment.
- Competition penalty captures within-simulator dynamics only (no market entry/exit).
- IQL revenue is an OPE estimate on synthetic buffer data.
- Real-world risk includes driver fatigue, vehicle maintenance, and market saturation.
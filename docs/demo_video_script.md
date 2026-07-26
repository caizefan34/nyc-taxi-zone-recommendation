# Research Demo Video Script

> **Status**: Script prepared. Video not yet recorded.
> **Target**: 3-minute research demo for conference submissions and project page.

---

## Script

### 0:00–0:30 | Problem Introduction

**[Visual: NYC taxi heatmap, animated trip density over 24 hours]**

"Every day, New York City's 13,000 yellow taxis navigate 263 zones. Drivers spend 30 to 50 percent of their shift cruising without passengers. That's millions of dollars in lost revenue and unnecessary congestion."

**[Visual: Heatmap fades to show a single taxi icon moving between zones]**

"The question is simple: where should a driver go next? The answer requires predicting future demand, accounting for competition, and planning across multiple time steps — all in real time."

---

### 0:30–1:00 | System Architecture

**[Visual: Animated architecture diagram showing pipeline flow]**

"We built the Dynamic Urban Mobility Decision System — an open-source benchmark platform with four integrated layers."

**[Visual: Each layer highlights as described]**

"Layer 1: A leakage-safe data pipeline processing over 100 million NYC taxi trips with strict chronological splits."

"Layer 2: Demand forecasting using LightGBM and XGBoost ensembles with graph neural network spatial features — achieving MAE of 1.49."

"Layer 3: A multi-agent simulator where drivers compete for a finite pool of passengers — enabling counterfactual analysis."

"Layer 4: Policy optimization with MDP-based planning and deep reinforcement learning."

---

### 1:00–2:00 | Interactive Demo

**[Visual: Screen recording of web demo]**

"Here's our interactive web demo — no installation required. Select any hour and day to see real-time demand predictions across all 263 zones."

**[Visual: Click on a zone, show recommendations]**

"Click any zone to see top-3 relocation recommendations with expected revenue and travel time. The two-step horizon planner looks ahead to optimize not just the next fare, but the one after."

**[Visual: Switch to benchmark comparison view]**

"You can also compare different strategies side by side — Hot Zone, Single-Step, Two-Step, and DQN — with hourly revenue breakdowns."

---

### 2:00–2:30 | Benchmark & Results

**[Visual: Results table with animated bars]**

"Our benchmark is fully reproducible. Every metric is checked into the repository. Run 'make all' to recreate every number."

"Key results: The Two-Step Horizon planner achieves NDCG at 3 of 0.9565 and delivers 139 dollars more daily revenue per driver compared to the Hot Zone baseline."

"All results are validated with paired statistical tests and multiple random seeds."

---

### 2:30–3:00 | Limitations & Future

**[Visual: "Limitations" section with honest disclaimers]**

"We're transparent about limitations. These are simulator outcomes, not production revenue. The models are NYC-specific and haven't been validated in other cities."

**[Visual: Future roadmap with checkboxes]**

"Future work includes cross-city validation, real driver feedback studies, and an online pilot deployment. We're also preparing a Hugging Face Space for one-click access."

"Our goal: make urban mobility AI research reproducible, comparable, and accessible to everyone."

**[Visual: GitHub URL + Live Demo URL + Star animation]**

"Check out the repository, try the live demo, and if this work is useful to your research, please cite and star the project."

---

## Production Notes

- **Style**: Professional but accessible; minimal jargon
- **Pacing**: Steady 150 words/minute; pause on key results
- **Visuals**: Dark theme matching project website; clean animations
- **Audio**: Clear voiceover with subtle background music (optional)
- **Captions**: Include English captions for accessibility

## Required Assets

- [ ] NYC taxi heatmap animation (0:00–0:30)
- [ ] Architecture diagram animation (0:30–1:00)
- [ ] Web demo screen recording (1:00–2:00)
- [ ] Results visualization (2:00–2:30)
- [ ] Limitations/roadmap slides (2:30–3:00)
- [ ] Voiceover recording
- [ ] Background music (optional, royalty-free)

## Platforms

Suitable for:
- Conference supplementary material
- Project GitHub Page (embedded)
- YouTube / Vimeo
- Social media promotion (shortened version)

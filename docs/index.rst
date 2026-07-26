NYC Taxi Zone Recommendation
============================

.. raw:: html

   <section class="showcase-hero">
     <div class="showcase-copy">
       <span class="eyebrow">REPRODUCIBLE SPATIAL AI RESEARCH</span>
       <h1>Where should an NYC taxi driver<br>reposition next?</h1>
       <p class="lead">A research-grade testbed combining leakage-safe forecasting, OD graph learning, finite-demand multi-agent simulation, and DQN baselines across 263 taxi zones.</p>
       <div class="hero-actions">
         <a class="button primary" href="https://github.com/caizefan34/nyc-taxi-zone-recommendation">View on GitHub</a>
         <a class="button secondary" href="combined_benchmark.html">Explore the benchmark</a>
       </div>
     </div>
   </section>

   <section class="metric-grid" aria-label="Project highlights">
     <article class="metric-card"><span>Forecast demand MAE</span><strong>1.4868</strong><small>from 1.7273 historical baseline</small></article>
     <article class="metric-card"><span>DQN revenue lift</span><strong>+$53.74</strong><small>per driver in the finite-demand simulator</small></article>
     <article class="metric-card"><span>Research surface</span><strong>263 zones</strong><small>forecasting, graphs, planning, and RL</small></article>
     <article class="metric-card"><span>Verification</span><strong>113 tests</strong><small>with full local data and reproducibility checks</small></article>
   </section>

Why this project is useful
--------------------------

Most taxi recommendation demos stop at a high offline score. This project asks the harder questions: does the metric align with simulated revenue, what happens when drivers compete for finite demand, and are improvements statistically supported?

.. raw:: html

   <section class="feature-grid">
     <article><h3>Forecast the market</h3><p>LightGBM and XGBoost use causal lag, rolling, calendar, and travel-neighborhood features.</p><a href="forecasting.html">Forecasting pipeline →</a></article>
     <article><h3>Model competition</h3><p>Every trip is consumable, simultaneous drivers compete, and saturation is measured explicitly.</p><a href="multi_agent_simulator.html">Multi-agent simulator →</a></article>
     <article><h3>Learn repositioning policies</h3><p>A Gymnasium environment supports reproducible DQN and Double-DQN baselines with masked actions.</p><a href="rl_baselines.html">RL baselines →</a></article>
     <article><h3>Audit scientific claims</h3><p>Paired bootstrap intervals, effect sizes, ablations, leakage checks, and negative results stay visible.</p><a href="combined_benchmark.html">Combined evidence →</a></article>
   </section>

The headline lesson
-------------------

Better prediction is not automatically a better policy. Forecasting reduces demand MAE, but the forecast-enhanced heuristic does not improve the legacy rollout. DQN improves finite-demand simulator revenue, while Double DQN does not. GraphSAGE improves the point estimate slightly, but its confidence interval crosses zero.

Quick start
-----------

.. code-block:: bash

   git clone https://github.com/caizefan34/nyc-taxi-zone-recommendation.git
   cd nyc-taxi-zone-recommendation
   python -m pip install -e ".[dev,forecasting,graph,rl]"
   python -m pytest tests -q

Explore the documentation
-------------------------

.. toctree::
   :maxdepth: 2
   :caption: Research & Methods

   problem_statement
   methodology
   combined_benchmark
   forecasting
   graph_learning
   multi_agent_simulator
   rl_baselines
   ablation_study

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/data_loader
   api/config
   api/improved_strategy
   api/mdp_solver

Project status
--------------

This repository is an educational research prototype, not a production dispatch system. Simulator outcomes are reported as simulator outcomes—not causal deployment revenue estimates.

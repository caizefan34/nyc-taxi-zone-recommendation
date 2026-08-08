===========================================
NYC Taxi Zone Recommendation
===========================================

.. image:: https://img.shields.io/badge/python-3.10%2B-blue
   :target: https://www.python.org/downloads/
.. image:: https://img.shields.io/badge/license-MIT-green
   :target: https://github.com/caizefan34/urban-mobility-ai/blob/master/LICENSE
.. image:: https://img.shields.io/github/actions/workflow/status/caizefan34/urban-mobility-ai/ci.yml?branch=master&label=tests
   :target: https://github.com/caizefan34/urban-mobility-ai/actions

**An open-source benchmark platform for AI-driven urban mobility decision making**
— combining spatiotemporal forecasting, multi-agent simulation, and offline reinforcement
learning with reproducible evaluation.

.. raw:: html

   <div style="margin: 20px 0;">
     <a href="https://github.com/caizefan34/urban-mobility-ai" style="display:inline-block;padding:10px 20px;background:#2ea44f;color:white;border-radius:6px;text-decoration:none;margin-right:10px;">⭐ GitHub</a>
     <a href="demo_gallery.html" style="display:inline-block;padding:10px 20px;background:#3178c6;color:white;border-radius:6px;text-decoration:none;margin-right:10px;">🎬 Demo Gallery</a>
     <a href="https://github.com/caizefan34/urban-mobility-ai/blob/master/ROADMAP.md" style="display:inline-block;padding:10px 20px;background:#6f42c1;color:white;border-radius:6px;text-decoration:none;">🗺 Roadmap</a>
   </div>

----

Why this project?
=================

Taxi drivers waste 30–60% of their shift searching for passengers. In NYC alone,
this means millions in lost revenue annually. This project provides a reproducible,
research-grade platform for testing and comparing AI-driven repositioning strategies.

Key results at a glance
=======================

+---------------------+------------+-----------+-------------+
| Strategy            | NDCG@3     | Hit@3     | Daily fare  |
+=====================+============+===========+=============+
| Hot Zone            | 0.7846     | 0.5842    | $431.21     |
+---------------------+------------+-----------+-------------+
| Single-Step         | 0.9024     | 0.8804    | $548.77     |
+---------------------+------------+-----------+-------------+
| Two-Step (default)  | **0.9565** | **0.9714**| **$570.61** |
+---------------------+------------+-----------+-------------+

Two-Step vs Single-Step: +$21.84/day, paired bootstrap 95% CI [$5.00, $39.53].

Architecture
============

.. image:: https://raw.githubusercontent.com/caizefan34/urban-mobility-ai/master/assets/social-preview.svg

**Pipeline:** Raw TLC trips → Data cleaning → Demand forecasting → Multi-agent simulator → Policy optimization → Benchmark evaluation

**Policies:** Hot Zone · Single-Step · Two-Step Horizon · DQN · Double DQN

**Forecasting:** LightGBM, XGBoost, GraphSAGE, GAT

**Simulation:** Single-driver reference rollout + finite-demand multi-agent competition

.. toctree::
   :maxdepth: 2
   :caption: 📖 Documentation

   problem_statement
   methodology
   forecasting
   graph_learning
   multi_agent_simulator
   rl_baselines
   combined_benchmark
   ablation_study

.. toctree::
   :maxdepth: 2
   :caption: 🔧 API Reference

   api/data_loader
   api/config
   api/improved_strategy
   api/mdp_solver

Important boundaries
====================

- **Simulator results are not production revenue estimates.** The rollout and multi-agent simulators omit congestion, airport queues, and market feedback. See :doc:`methodology`.
- **This is not offline RL.** NYC TLC data lacks logging-policy propensities. The Q-learning extension is online Q-learning inside an estimated simulator. See :doc:`rl_baselines`.
- **Exposure risk:** Two-Step strategy has 70.33% airport exposure. This saturation risk is absent from single-driver simulators.

Reproducibility
===============

All results are reproducible. Reference metrics are checked into the repository.
Run the full pipeline:

.. code-block:: bash

   git clone https://github.com/caizefan34/urban-mobility-ai.git
   cd urban-mobility-ai
   pip install -e ".[dev,forecasting,graph,rl]"
   make all

Citation
========

.. code-block:: bibtex

   @software{cai2025nyc_taxi_recommendation,
     author = {Zefan Cai},
     title  = {NYC Taxi Zone Recommendation: An Open-Source Benchmark Platform for AI-Driven Urban Mobility},
     year   = {2025},
     url    = {https://github.com/caizefan34/urban-mobility-ai}
   }

.. toctree::
   :hidden:

   demo_gallery

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

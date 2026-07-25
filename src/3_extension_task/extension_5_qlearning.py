# -*- coding: utf-8 -*-
"""Extension 5: Q-learning for Taxi Zone Recommendation.

Direction 5: Reinforcement Learning Strategy.
Trains a Q-learning agent on historical taxi trip data to recommend zones.
"""
from __future__ import annotations
import csv, json, math, os, random, sys
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np
import pyarrow.parquet as pq

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ZONE_COUNT = 263; SLOT_COUNT = 48; WEEK_SLOT_COUNT = 7 * SLOT_COUNT
STATISTICS_PATH = PROJECT_ROOT / "data/processed/zone_time_statistics.parquet"
TRAIN_PATH = PROJECT_ROOT / "data/processed/train_cleaned.parquet"
TRAVEL_TIME_PATH = PROJECT_ROOT / "data/processed/travel_time_matrix_dijkstra.csv"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

# Hyperparameters
GAMMA = 0.9        # discount factor
ALPHA = 0.1        # learning rate
EPSILON = 0.3      # exploration rate
EPSILON_DECAY = 0.995
EPSILON_MIN = 0.01
NUM_EPISODES = 5000
MAX_STEPS = 50     # max steps per episode
CANDIDATE_K = 50   # top K candidate actions


def load_statistics():
    demand = [[[0.0]*ZONE_COUNT for _ in range(SLOT_COUNT)] for _ in range(7)]
    mf = [[[0.0]*ZONE_COUNT for _ in range(SLOT_COUNT)] for _ in range(7)]
    for row in pq.read_table(STATISTICS_PATH, columns=["pickup_location_id","weekday","time_slot","pickup_count","mean_fare_amount"]).to_pylist():
        loc = int(row["pickup_location_id"]) - 1
        wd = int(row["weekday"]); ts = int(row["time_slot"])
        if 0 <= loc < ZONE_COUNT:
            demand[wd][ts][loc] = float(row["pickup_count"])
            rf = row["mean_fare_amount"]
            if rf is not None and np.isfinite(float(rf)):
                mf[wd][ts][loc] = max(0.0, float(rf))
    return demand, mf

def load_travel_time():
    with TRAVEL_TIME_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f); next(reader)
        return [[float(v) for v in row[1:]] for row in reader]

def load_transition_probs():
    trans = [[0.0]*ZONE_COUNT for _ in range(ZONE_COUNT)]
    counts = [0]*ZONE_COUNT
    for row in pq.read_table(TRAIN_PATH, columns=["PULocationID","DOLocationID"]).to_pylist():
        pu = int(row["PULocationID"]) - 1; do = int(row["DOLocationID"]) - 1
        if 0 <= pu < ZONE_COUNT and 0 <= do < ZONE_COUNT:
            trans[pu][do] += 1.0; counts[pu] += 1
    for pu in range(ZONE_COUNT):
        if counts[pu] > 0:
            for do in range(ZONE_COUNT):
                trans[pu][do] /= counts[pu]
    return trans, counts

def load_mean_trip_duration():
    means = [10.0]*ZONE_COUNT; sums = [0.0]*ZONE_COUNT; counts = [0]*ZONE_COUNT
    for row in pq.read_table(TRAIN_PATH, columns=["PULocationID","trip_duration"]).to_pylist():
        pu = int(row["PULocationID"]) - 1; dur = float(row["trip_duration"])
        if 0 <= pu < ZONE_COUNT and dur > 0:
            sums[pu] += dur; counts[pu] += 1
    for pu in range(ZONE_COUNT):
        if counts[pu] > 0: means[pu] = sums[pu] / counts[pu]
    return means


class QLearningAgent:
    def __init__(self, demand, mf, tt, trans, mean_dur):
        self.demand = demand; self.mf = mf; self.tt = tt; self.trans = trans; self.mean_dur = mean_dur
        self.n_states = WEEK_SLOT_COUNT * ZONE_COUNT
        self.n_actions = CANDIDATE_K + 1
        self.q_table = {}  # sparse dict: state -> list of action values
        self.action_cache = {}  # state -> list of (action_zone, action_idx)
        pass  # candidates computed on demand

    def _state_id(self, zone, weekday, slot):
        return (weekday * SLOT_COUNT + slot) * ZONE_COUNT + zone

    def _get_candidates(self, state):
        if state in self.action_cache:
            return self.action_cache[state]
        zone = state % ZONE_COUNT
        w_slot = state // ZONE_COUNT
        wd = w_slot // SLOT_COUNT; slot = w_slot % SLOT_COUNT
        scores = [self.demand[wd][slot][z] * self.mf[wd][slot][z] / (self.tt[zone][z] + 1.0) if np.isfinite(self.tt[zone][z]) else 0.0 for z in range(ZONE_COUNT)]
        ordered = sorted(range(ZONE_COUNT), key=lambda z: (-scores[z], z))[:CANDIDATE_K]
        if zone not in ordered:
            ordered = [zone] + ordered[:CANDIDATE_K-1]
        candidates = [(z, i) for i, z in enumerate(ordered)]
        self.action_cache[state] = candidates
        if state not in self.q_table:
            self.q_table[state] = [0.0] * len(candidates)
        return candidates

    def _action_idx(self, state, zone):
        candidates = self._get_candidates(state)
        for z, idx in candidates:
            if z == zone: return idx
        return 0

    def _expected_reward(self, zone, wd, slot):
        d = self.demand[wd][slot][zone]
        if d <= 0: return 0.0
        p = d / (d + 240.0)
        expected_fare = self.mf[wd][slot][zone]
        return p * expected_fare

    def _next_state(self, zone, action_zone, wd, slot, state):
        """Simulate one step and return next state and reward."""
        origin = zone
        target = action_zone
        move_minutes = 0.0 if origin == target else self.tt[origin][target]
        if not np.isfinite(move_minutes) or move_minutes < 0:
            return state, 0.0, True  # unreachable
        move_slots = int(np.floor(move_minutes / 30.0 + 0.5))
        arrival = (state + move_slots) % WEEK_SLOT_COUNT
        arr_wd = arrival // SLOT_COUNT; arr_slot = arrival % SLOT_COUNT
        d = self.demand[arr_wd][arr_slot][target]
        p = d / (d + 240.0) if d > 0 else 0.0
        if random.random() < p:  # success
            fare = self.mf[arr_wd][arr_slot][target]
            dur = self.mean_dur[target]
            dur_slots = int(np.floor(dur / 30.0 + 0.5))
            next_state = (arrival + 1 + dur_slots) % WEEK_SLOT_COUNT
            # Sample dropoff zone from transition probs
            dropoff = target
            if sum(self.trans[target]) > 0:
                r = random.random(); cum = 0.0
                for do in range(ZONE_COUNT):
                    cum += self.trans[target][do]
                    if r <= cum: dropoff = do; break
            next_state = next_state * ZONE_COUNT + dropoff
            return next_state, fare, False
        else:  # failure
            next_state = (arrival + 1) % WEEK_SLOT_COUNT * ZONE_COUNT + target
            return next_state, 0.0, False

    def choose_action(self, state, epsilon):
        candidates = self._get_candidates(state)
        if state not in self.q_table:
            self.q_table[state] = [0.0] * len(candidates)
        if random.random() < epsilon:
            return random.choice(candidates)
        q_values = self.q_table[state]
        best_idx = max(range(len(q_values)), key=lambda i: (q_values[i], -candidates[i][0]))
        return candidates[best_idx]

    def update(self, state, action_idx, reward, next_state):
        if state not in self.q_table:
            candidates = self._get_candidates(state)
            self.q_table[state] = [0.0] * len(candidates)
        if next_state not in self.q_table:
            next_candidates = self._get_candidates(next_state)
            self.q_table[next_state] = [0.0] * len(next_candidates)
        q_current = self.q_table[state][action_idx]
        q_next = max(self.q_table[next_state]) if self.q_table[next_state] else 0.0
        td_target = reward + GAMMA * q_next
        self.q_table[state][action_idx] += ALPHA * (td_target - q_current)

    def recommend(self, dt, loc):
        """Unified recommend interface for eval tools."""
        target = dt.replace(minute=(dt.minute//30)*30, second=0, microsecond=0) + timedelta(minutes=30)
        slot = target.hour * 2 + target.minute // 30; wd = target.weekday()
        state = self._state_id(loc - 1, wd, slot)
        candidates = self._get_candidates(state)
        if state not in self.q_table:
            self.q_table[state] = [0.0] * len(candidates)
        q_values = self.q_table[state]
        ordered = sorted(range(len(candidates)), key=lambda i: (-q_values[i], candidates[i][0]))
        top3_zones = [candidates[i][0] + 1 for i in ordered[:3]]
        return top3_zones[:3]


def train_agent(agent, episodes=5000):
    print(f"Training Q-learning agent for {episodes} episodes...")
    epsilon = EPSILON
    total_rewards = []
    for ep in range(episodes):
        zone = random.randint(0, ZONE_COUNT - 1)
        wd = random.randint(0, 6)
        slot = random.randint(0, SLOT_COUNT - 1)
        state = agent._state_id(zone, wd, slot)
        ep_reward = 0.0
        for step in range(MAX_STEPS):
            action_zone, action_idx = agent.choose_action(state, epsilon)
            next_state, reward, done = agent._next_state(zone, action_zone, wd, slot, state // ZONE_COUNT)
            agent.update(state, action_idx, reward, next_state)
            state = next_state
            zone = state % ZONE_COUNT
            w_slot = state // ZONE_COUNT
            wd = w_slot // SLOT_COUNT; slot = w_slot % SLOT_COUNT
            ep_reward += reward
            if done: break
        total_rewards.append(ep_reward)
        epsilon = max(EPSILON_MIN, epsilon * EPSILON_DECAY)
        if (ep + 1) % 500 == 0:
            avg_r = np.mean(total_rewards[-500:])
            print(f"  Episode {ep+1}/{episodes}, Avg Reward: {avg_r:.2f}, Epsilon: {epsilon:.3f}, Q-table size: {len(agent.q_table)}")
    return total_rewards


def evaluate_agent(agent, n_episodes=100):
    print(f"\nEvaluating agent over {n_episodes} episodes...")
    total_rewards = []
    for ep in range(n_episodes):
        zone = random.randint(0, ZONE_COUNT - 1)
        wd = random.randint(0, 6)
        slot = random.randint(0, SLOT_COUNT - 1)
        state = agent._state_id(zone, wd, slot)
        ep_reward = 0.0
        for step in range(MAX_STEPS):
            action_zone, _ = agent.choose_action(state, 0.0)  # greedy
            next_state, reward, done = agent._next_state(zone, action_zone, wd, slot, state // ZONE_COUNT)
            state = next_state
            zone = state % ZONE_COUNT
            w_slot = state // ZONE_COUNT
            wd = w_slot // SLOT_COUNT; slot = w_slot % SLOT_COUNT
            ep_reward += reward
            if done: break
        total_rewards.append(ep_reward)
    return {
        "avg_reward": float(np.mean(total_rewards)),
        "std_reward": float(np.std(total_rewards)),
        "episodes": n_episodes,
        "q_table_size": len(agent.q_table),
    }


# OLD evaluate_baseline removed
    """Evaluate Baseline 2 (greedy single-step) as comparison."""
    total_rewards = []
    for ep in range(n_episodes):
        zone = random.randint(0, ZONE_COUNT - 1)
        wd = random.randint(0, 6)
        slot = random.randint(0, SLOT_COUNT - 1)
        state = wd * SLOT_COUNT + slot
        ep_reward = 0.0
        for step in range(MAX_STEPS):
            scores = [demand[wd][slot][z] * mf[wd][slot][z] / (tt[zone][z] + 1.0) if np.isfinite(tt[zone][z]) else 0.0 for z in range(ZONE_COUNT)]
            best_zone = max(range(ZONE_COUNT), key=lambda z: (scores[z], -z))
            move_min = 0.0 if zone == best_zone else tt[zone][best_zone]
            if not np.isfinite(move_min) or move_min < 0: break
            move_slots = int(np.floor(move_min / 30.0 + 0.5))
            arrival = (state + move_slots) % WEEK_SLOT_COUNT
            arr_wd = arrival // SLOT_COUNT; arr_slot = arrival % SLOT_COUNT
            d = demand[arr_wd][arr_slot][best_zone]
            if random.random() < d / (d + 240.0) if d > 0 else 0.0:
                ep_reward += mf[arr_wd][arr_slot][best_zone]
                dur = 10.0
                dur_slots = int(np.floor(dur / 30.0 + 0.5))
                state = (arrival + 1 + dur_slots) % WEEK_SLOT_COUNT
                zone = best_zone
            else:
                state = (arrival + 1) % WEEK_SLOT_COUNT
                zone = best_zone
            wd = state // SLOT_COUNT; slot = state % SLOT_COUNT
        total_rewards.append(ep_reward)
    return {
        "avg_reward": float(np.mean(total_rewards)),
        "std_reward": float(np.std(total_rewards)),
        "episodes": n_episodes,
    }


def _evaluate_baseline(agent, n_episodes=100):
    total_rewards = []
    for ep in range(n_episodes):
        zone = random.randint(0, ZONE_COUNT - 1)
        wd = random.randint(0, 6)
        slot = random.randint(0, SLOT_COUNT - 1)
        state = wd * SLOT_COUNT + slot
        ep_reward = 0.0
        for step in range(MAX_STEPS):
            times = agent.tt[zone]
            scores = [agent.demand[wd][slot][z] * agent.mf[wd][slot][z] / (times[z] + 1.0) if np.isfinite(times[z]) else 0.0 for z in range(ZONE_COUNT)]
            best_zone = max(range(ZONE_COUNT), key=lambda z: (scores[z], -z))
            move_min = 0.0 if zone == best_zone else agent.tt[zone][best_zone]
            if not np.isfinite(move_min) or move_min < 0: break
            move_slots = int(np.floor(move_min / 30.0 + 0.5))
            arrival = (state + move_slots) % WEEK_SLOT_COUNT
            arr_wd = arrival // SLOT_COUNT; arr_slot = arrival % SLOT_COUNT
            d = agent.demand[arr_wd][arr_slot][best_zone]
            p = d / (d + 240.0) if d > 0 else 0.0
            if random.random() < p:
                fare = agent.mf[arr_wd][arr_slot][best_zone]
                dur = agent.mean_dur[best_zone]
                dur_slots = int(np.floor(dur / 30.0 + 0.5))
                state = (arrival + 1 + dur_slots) % WEEK_SLOT_COUNT
                if sum(agent.trans[best_zone]) > 0:
                    r = random.random(); cum = 0.0
                    for do in range(ZONE_COUNT):
                        cum += agent.trans[best_zone][do]
                        if r <= cum: zone = do; break
                else:
                    zone = best_zone
                ep_reward += fare
            else:
                state = (arrival + 1) % WEEK_SLOT_COUNT
                zone = best_zone
            wd = state // SLOT_COUNT; slot = state % SLOT_COUNT
        total_rewards.append(ep_reward)
    return {
        'avg_reward': float(np.mean(total_rewards)),
        'std_reward': float(np.std(total_rewards)),
        'episodes': n_episodes,
    }

def main():
    print("=" * 60)
    print("  Direction 5: Q-learning for Taxi Zone Recommendation")
    print("=" * 60)
    print("\nLoading data...")
    demand, mf = load_statistics()
    tt = load_travel_time()
    trans, _ = load_transition_probs()
    mean_dur = load_mean_trip_duration()
    print(f"  Demand stats: {len(demand)}x{len(demand[0])}x{len(demand[0][0])}")
    print(f"  Travel time: {len(tt)}x{len(tt[0])}")

    # Create agent
    agent = QLearningAgent(demand, mf, tt, trans, mean_dur)

    # Train
    train_rewards = train_agent(agent, episodes=NUM_EPISODES)

    # Evaluate
    rl_result = evaluate_agent(agent, n_episodes=200)
    print(f"\nQ-learning results: {json.dumps(rl_result, indent=2)}")

    # Baseline comparison
    bl_result = _evaluate_baseline(agent, n_episodes=200)
    print(f"\nBaseline 2 results: {json.dumps(bl_result, indent=2)}")

    # Save results
    result = {
        "algorithm": "Q-learning",
        "hyperparameters": {
            "gamma": GAMMA, "alpha": ALPHA, "epsilon_start": EPSILON, "epsilon_decay": EPSILON_DECAY, "epsilon_min": EPSILON_MIN, "episodes": NUM_EPISODES, "max_steps": MAX_STEPS, "candidate_k": CANDIDATE_K,
        },
        "q_learning_evaluation": rl_result,
        "baseline_2_comparison": bl_result,
        "improvement_pct": round((rl_result["avg_reward"] - bl_result["avg_reward"]) / bl_result["avg_reward"] * 100, 2) if bl_result["avg_reward"] > 0 else 0,
        "training_rewards_summary": {
            "mean": float(np.mean(train_rewards)),
            "std": float(np.std(train_rewards)),
            "last_500_mean": float(np.mean(train_rewards[-500:])),
        },
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / "extension_qlearning_results.json"
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"\nResults saved to {output_path}")


if __name__ == "__main__":
    main()
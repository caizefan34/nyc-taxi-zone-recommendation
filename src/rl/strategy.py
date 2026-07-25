"""Fast Top-3 strategy adapter for trained Q-networks."""
from __future__ import annotations

from datetime import datetime, timedelta

import numpy as np
import torch

from .dqn import DQNAgent
from .env import ObservationEncoder


class DQNStrategy:
    """Precompute weekly zone recommendations from a trained candidate-reranking network."""

    def __init__(
        self,
        agent: DQNAgent,
        encoder: ObservationEncoder,
        *,
        batch_size: int = 2048,
    ) -> None:
        if encoder.candidate_count < 3:
            raise ValueError("candidate_count must be at least 3 for Top-3 recommendations")
        self.agent = agent
        self.encoder = encoder
        self.rankings = self._precompute(batch_size=batch_size)

    def _precompute(self, *, batch_size: int) -> np.ndarray:
        zone_count = self.encoder.zone_count
        rankings = np.empty((336, zone_count, 3), dtype=np.int16)
        base = datetime(2023, 1, 2)
        observations = []
        candidates = []
        masks = []
        states = []

        def flush() -> None:
            if not observations:
                return
            values = np.asarray(observations, dtype=np.float32)
            with torch.no_grad():
                q_values = self.agent.online(
                    torch.as_tensor(values, device=self.agent.device)
                ).cpu().numpy()
            for row, (state, origin) in enumerate(states):
                valid = np.flatnonzero(masks[row])
                ordered_actions = valid[np.lexsort((valid, -q_values[row, valid]))]
                ranked_zones = (candidates[row][ordered_actions] + 1).tolist()
                for fallback_zone in (origin + 1, *range(1, zone_count + 1)):
                    if fallback_zone not in ranked_zones:
                        ranked_zones.append(fallback_zone)
                    if len(ranked_zones) == 3:
                        break
                rankings[state, origin] = ranked_zones[:3]
            observations.clear()
            candidates.clear()
            masks.clear()
            states.clear()

        for state in range(336):
            value = base + timedelta(minutes=state * 30)
            for origin in range(zone_count):
                observation, candidate_zones, action_mask = self.encoder.encode(value, origin + 1)
                observations.append(observation)
                candidates.append(candidate_zones)
                masks.append(action_mask)
                states.append((state, origin))
                if len(observations) >= batch_size:
                    flush()
        flush()
        return rankings

    def recommend(self, current_datetime: datetime, current_location_id: int) -> list[int]:
        if not isinstance(current_datetime, datetime):
            raise TypeError("current_datetime must be a datetime")
        if not 1 <= current_location_id <= self.encoder.zone_count:
            raise ValueError(f"current_location_id must be in 1..{self.encoder.zone_count}")
        state = self.encoder.state_index(current_datetime)
        return self.rankings[state, current_location_id - 1].astype(int).tolist()

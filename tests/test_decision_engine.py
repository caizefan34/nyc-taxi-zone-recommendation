"""Tests for the Decision Engine."""
from __future__ import annotations

from datetime import datetime

import pytest

from src.decision.engine import build_decision_score, build_recommendation, compute_confidence
from src.decision.policies.constraints import ConstraintAwarePolicy, ZoneConstraints
from src.decision.schemas import RankedZone, Recommendation


class TestRankedZone:
    def test_creation(self):
        rz = RankedZone(zone_id=132, score=0.91)
        assert rz.zone_id == 132
        assert rz.score == 0.91
        assert rz.expected_demand is None

    def test_to_dict(self):
        rz = RankedZone(zone_id=132, score=0.91, expected_demand=41.7, expected_supply=23.2)
        d = rz.to_dict()
        assert d["zone_id"] == 132
        assert d["expected_demand"] == 41.7
        assert d["expected_supply"] == 23.2

    def test_optional_fields_omitted(self):
        rz = RankedZone(zone_id=132, score=0.91)
        d = rz.to_dict()
        assert "expected_demand" not in d


class TestRecommendation:
    def test_creation(self):
        rec = Recommendation(
            vehicle_id="v1",
            timestamp=datetime(2023, 1, 15, 18, 30),
            current_zone=161,
            recommended_zone=132,
        )
        assert rec.vehicle_id == "v1"
        assert rec.current_zone == 161
        assert rec.recommended_zone == 132

    def test_to_dict(self):
        rec = Recommendation(
            vehicle_id="v1",
            timestamp=datetime(2023, 1, 15, 18, 30),
            current_zone=161,
            recommended_zone=132,
            ranked_zones=[
                RankedZone(zone_id=132, score=0.91),
                RankedZone(zone_id=236, score=0.85),
            ],
            confidence=0.87,
            model_name="two_step",
            model_version="v1",
            explanations=["high demand"],
        )
        d = rec.to_dict()
        assert d["recommended_zone"] == 132
        assert len(d["ranked_zones"]) == 2
        assert d["confidence"] == 0.87
        assert "high demand" in d["explanations"]


class TestBuildRecommendation:
    def test_basic(self):
        rec = build_recommendation(
            vehicle_id="v1",
            current_time=datetime(2023, 1, 15, 18, 30),
            current_zone=161,
            ranked_zone_ids=[132, 236, 237],
            model_name="two_step",
            model_version="v1",
        )
        assert rec.vehicle_id == "v1"
        assert rec.recommended_zone == 132
        assert len(rec.ranked_zones) == 3

    def test_with_scores(self):
        rec = build_recommendation(
            vehicle_id="v1",
            current_time=datetime(2023, 1, 15, 18, 30),
            current_zone=161,
            ranked_zone_ids=[132, 236],
            zone_scores=[0.91, 0.85],
        )
        assert rec.ranked_zones[0].score == 0.91
        assert rec.ranked_zones[1].score == 0.85


class TestConfidence:
    def test_high_separation(self):
        rz = [RankedZone(zone_id=132, score=0.91), RankedZone(zone_id=236, score=0.50)]
        conf = compute_confidence(rz)
        assert conf is not None
        assert 0 < conf < 1

    def test_low_separation(self):
        rz = [RankedZone(zone_id=132, score=0.91), RankedZone(zone_id=236, score=0.90)]
        conf = compute_confidence(rz)
        assert conf is not None
        assert conf < 0.1

    def test_single_zone(self):
        rz = [RankedZone(zone_id=132, score=0.91)]
        conf = compute_confidence(rz)
        assert conf is None

    def test_empty(self):
        conf = compute_confidence([])
        assert conf is None


class TestZoneConstraints:
    def test_defaults(self):
        c = ZoneConstraints()
        assert c.max_reposition_distance_minutes is None

    def test_invalid_distance(self):
        with pytest.raises(ValueError):
            ZoneConstraints(max_reposition_distance_minutes=-1)

    def test_invalid_airport_ratio(self):
        with pytest.raises(ValueError):
            ZoneConstraints(max_airport_exposure_ratio=1.5)


class TestConstraintAwarePolicy:
    def test_passthrough(self):
        def base(dt, zone):
            return [132, 236, 237]
        constraints = ZoneConstraints()
        policy = ConstraintAwarePolicy(base, constraints)
        result = policy.recommend(datetime(2023, 1, 15, 18, 30), 161)
        assert result == [132, 236, 237]

    def test_distance_constraint(self):
        def base(dt, zone):
            return [132, 236, 237]
        travel = [
            [10.0 if i != j else 0.0 for j in range(263)]
            for i in range(263)
        ]
        constraints = ZoneConstraints(max_reposition_distance_minutes=5.0)
        policy = ConstraintAwarePolicy(base, constraints, travel_times=travel)
        result = policy.recommend(datetime(2023, 1, 15, 18, 30), 161)
        # All destinations > 5 min away should be filtered; falls back to original
        assert result == [132, 236, 237]


class TestDecisionScore:
    def test_with_scores(self):
        rz = [RankedZone(zone_id=132, score=0.91)]
        score = build_decision_score(rz)
        assert score == 0.91

    def test_empty(self):
        assert build_decision_score([]) is None

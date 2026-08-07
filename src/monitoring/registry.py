"""Model Registry — lightweight model versioning without MLflow dependency.

Stores model metadata in JSON files under models/registry/.
Supports: model_name, version, training dataset, config hash, metrics.
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """Metadata for one registered model version."""

    model_name: str
    model_version: str
    model_type: str  # "forecasting", "policy", "rl"
    training_dataset: str
    training_timestamp: str
    feature_version: str = "1.0.0"
    config_hash: str = ""
    git_commit: str = "unknown"
    metrics: dict = field(default_factory=dict)
    tags: dict = field(default_factory=dict)
    registered_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict:
        return asdict(self)


class ModelRegistry:
    """File-based model registry.

    Stores metadata as JSON files under models/registry/{model_name}/{version}.json.
    """

    def __init__(self, registry_dir: str | Path | None = None):
        if registry_dir is None:
            self._root = Path(__file__).resolve().parents[3] / "models" / "registry"
        else:
            self._root = Path(registry_dir)
        self._root.mkdir(parents=True, exist_ok=True)

    def register(self, metadata: ModelMetadata) -> Path:
        """Register a model version."""
        model_dir = self._root / metadata.model_name
        model_dir.mkdir(parents=True, exist_ok=True)
        path = model_dir / f"{metadata.model_version}.json"
        path.write_text(json.dumps(metadata.to_dict(), indent=2))
        logger.info("Registered %s v%s → %s", metadata.model_name, metadata.model_version, path)
        return path

    def get(self, model_name: str, model_version: str = "latest") -> Optional[dict]:
        """Retrieve model metadata."""
        model_dir = self._root / model_name
        if not model_dir.exists():
            return None

        if model_version == "latest":
            versions = sorted(model_dir.glob("*.json"))
            if not versions:
                return None
            path = versions[-1]
        else:
            path = model_dir / f"{model_version}.json"

        if not path.exists():
            return None
        return json.loads(path.read_text())

    def list_models(self, model_type: Optional[str] = None) -> list[dict]:
        """List all registered models."""
        models = []
        for model_dir in sorted(self._root.iterdir()):
            if not model_dir.is_dir():
                continue
            for version_file in sorted(model_dir.glob("*.json")):
                data = json.loads(version_file.read_text())
                if model_type is None or data.get("model_type") == model_type:
                    models.append(data)
        return models

    def count(self) -> int:
        return len(self.list_models())


def compute_config_hash(config: dict) -> str:
    """Compute a deterministic hash of a config dict."""
    serialized = json.dumps(config, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()[:12]


_registry_instance: Optional[ModelRegistry] = None


def get_registry() -> ModelRegistry:
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ModelRegistry()
    return _registry_instance

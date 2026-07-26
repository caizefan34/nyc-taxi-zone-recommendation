"""Data version management interface."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


class DataVersion:
    """Track dataset version via content hash."""
    def __init__(self, filepath: str | Path) -> None:
        self.filepath = Path(filepath)
        self.hash = self._compute_hash()

    def _compute_hash(self) -> str:
        h = hashlib.sha256()
        if not self.filepath.exists():
            return "FILE_NOT_FOUND"
        with open(self.filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()[:16]

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DataVersion):
            return NotImplemented
        return self.hash == other.hash

    def __str__(self) -> str:
        return f"DataVersion({self.filepath.name}: {self.hash})"


class VersionManifest:
    """Track multiple dataset versions in a JSON manifest."""
    def __init__(self, manifest_path: str | Path = "data/version_manifest.json") -> None:
        self.path = Path(manifest_path)
        self._data: dict[str, Any] = {}
        if self.path.exists():
            self._data = json.loads(self.path.read_text(encoding="utf-8"))

    def register(self, name: str, filepath: str | Path) -> str:
        dv = DataVersion(filepath)
        entry = {
            "path": str(filepath),
            "hash": dv.hash,
            "timestamp": datetime.now().isoformat(),
        }
        self._data[name] = entry
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._data, indent=2) + "\n", encoding="utf-8")
        return dv.hash

    def verify(self, name: str, filepath: str | Path) -> bool:
        if name not in self._data:
            return False
        dv = DataVersion(filepath)
        return dv.hash == self._data[name]["hash"]

    def summary(self) -> str:
        lines = ["# Data Version Manifest", ""]
        for name, entry in self._data.items():
            lines.append(f"- **{name}**: `{entry['hash']}` ({entry['timestamp']})")
        return "\n".join(lines)

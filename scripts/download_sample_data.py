#!/usr/bin/env python3
"""
Download sample data to data/sample/ for quick-start demos.
No external download needed - sample data is bundled in the repo.
"""
import sys
from pathlib import Path

def download():
    sample_dir = Path("data/sample")
    if not sample_dir.exists():
        print("Creating data/sample/...")
        sample_dir.mkdir(parents=True, exist_ok=True)
    
    print("Sample data is bundled in the repository at data/sample/")
    print()
    print("Files:")
    for f in sorted(sample_dir.iterdir()):
        size = f.stat().st_size
        print(f"  {f.name} ({size:,} bytes)")
    print()
    print("Usage: python scripts/run_demo.py")
    print("Sample data is automatically loaded by the demo scripts.")
    print("Done.")

if __name__ == "__main__":
    download()

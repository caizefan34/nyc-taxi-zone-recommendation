# Release Notes Template

Use this as a guide for creating GitHub Releases. Copy and fill in per version.

---

## vX.Y.Z — Release Title

### Highlights

- ✨ **Feature name** — one-line description of the biggest addition
- 📊 **Benchmark update** — key metric improvement or new baseline
- 🔧 **Infrastructure** — CI, testing, or tooling improvement

### Screenshots

> Add screenshots or GIFs showing new features in action.

![Architecture](https://via.placeholder.com/800x400?text=Screenshot+Placeholder)

### New Features

- Feature A with brief description
- Feature B with brief description

### Breaking Changes

- ⚠ Change that requires action from users
- Migration guide: see `docs/archive_manifest.md`

### Improvements

- Improvement 1
- Improvement 2

### Bug Fixes

- Bug fix 1
- Bug fix 2

### Future Roadmap

See [../ROADMAP.md](../ROADMAP.md) for full details.

| Milestone | Target |
|---|---|
| v3.0 Cross-city validation | TBD |
| v4.0 Real deployment | TBD |

### Contributors

Thanks to everyone who contributed to this release!

---

### Installation

```bash
pip install urban-mobility-ai==X.Y.Z
# or from source
git checkout vX.Y.Z
pip install -e ".[dev,forecasting,graph,rl]"
```

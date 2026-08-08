# GitHub Pages Setup

## Enable Pages
1. Go to repo Settings - Pages
2. Source: "Deploy from a branch"
3. Branch: `master`, folder: `/` (or `/web` if deploying from subdirectory)
4. Click Save

## Alternative: GitHub Actions
Create `.github/workflows/pages.yml` to auto-deploy the `web/` directory:

```yaml
name: Deploy to GitHub Pages
on:
  push:
    branches: [master]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./web
```

## Domain
- Default: `https://caizefan34.github.io/urban-mobility-ai/`
- Custom domain: Configure in Settings - Pages (optional)

## Testing Locally
```bash
# Using Python
cd web && python -m http.server 8000
# Open http://localhost:8000

# Or use VS Code Live Server extension
```

## Files Deployed
The `web/` directory contains all necessary files:
- `index.html`, `css/style.css`, `js/*.js`, `data/zones.json`, `assets/`

## Post-Deployment Check
1. Verify all sections load correctly
2. Test Leaflet map interaction
3. Test simulation workflow
4. Test on mobile devices
5. Check all external CDN links work

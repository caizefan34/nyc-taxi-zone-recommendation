# Security Policy

## Supported Versions

| Version | Supported | EOL |
|---------|-----------|-----|
| 3.0.x | :white_check_mark: Active | — |
| 2.0.x | :white_check_mark: Security fixes | 2027-01 |
| 1.0.x | :x: | 2026-08 |

## Reporting a Vulnerability

This project processes publicly available NYC TLC taxi trip data and does not handle sensitive personal information. However, if you discover a security vulnerability, please **do not** file a public GitHub issue.

**Report via email:** caizefan@sjtu.edu.cn

Please include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if available)

You should receive a response within **48 hours**. If confirmed, a patch will be released as soon as possible depending on complexity.

## Docker Security

Docker images use `python:3.12-slim` as the base image and run as a non-root user where possible. Review `Dockerfile` and `.dockerignore` before deploying in production. Dependabot alerts are enabled for this repository.

## Scope

- **In scope:** Source code in `src/`, `app/`, `pages/`, `web/`, Docker configuration, GitHub Actions workflows
- **Out of scope:** Third-party dependencies (report directly to upstream maintainers), data files in `data/`

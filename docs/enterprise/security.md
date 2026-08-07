# Security Considerations

## Current Status

This is a **research prototype**. The following security features are NOT implemented:

- API authentication
- Rate limiting
- Input sanitization beyond Pydantic validation
- Secrets management
- Audit logging
- HTTPS/TLS enforcement

## For Pilot Deployments

### Recommended Architecture

```
Client → Auth Proxy (nginx/JWT) → API → Decision Engine
```

Place an authentication proxy in front of the API. Do not expose the API directly to the internet.

### Secrets Management

- Use environment variables (`.env`) for configuration
- Never commit `.env` or credentials to git
- Rotate secrets regularly
- Use a secrets manager (AWS Secrets Manager, HashiCorp Vault) for production

### PII Handling

- The platform does NOT require PII (driver names, passenger info, etc.)
- NYC TLC data is publicly available and anonymized
- If integrating proprietary fleet data, strip PII before ingestion
- Vehicle IDs should be opaque strings, not license plates or VINs

### Logging

- Logs contain vehicle IDs, zone IDs, timestamps, and model predictions
- No passenger data, driver identities, or payment information
- Configure log retention policies for production
- Redact sensitive fields if adding custom data sources

### Data Retention

- Trip data is processed in-memory and not persistently stored by the API
- Shadow evaluation records contain zone IDs and timestamps only
- No passenger trip histories are retained

## For Production

Before production deployment, implement:

1. [ ] Authentication (OAuth2, JWT, or API keys)
2. [ ] Rate limiting
3. [ ] HTTPS/TLS
4. [ ] Secrets management
5. [ ] Audit logging
6. [ ] Penetration testing
7. [ ] Data privacy review
8. [ ] Incident response plan

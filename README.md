# mothership-core

Central backend-tjänst för **Mothership Dashboard**-plattformen.

## Översikt
`mothership-core` är skrivet i **Python (FastAPI)** och använder **PostgreSQL** som databas. Den ansvarar för:
- Användarhantering, JWT-autentisering och rollbaserad åtkomstkontroll (RBAC).
- Tjänstekatalog (CRUD för alla tjänster i hemmalabbet/klustret).
- Incident- och driftstörningslogg.
- Datasammanställning mot `mothership-pulse` för dashboarden.
- Telemetri och strukturerad säkerhetsloggning (Azure Application Insights).
- Distributionsmål: Både lokalt k3s-kluster och Azure App Service.

## Hälso-endpoints
- `GET /healthz` – Liveness probe (kontrollerar att processen lever)
- `GET /readyz` – Readiness probe (kontrollerar databasanslutning och beroenden)
- `GET /metrics` – Metrik

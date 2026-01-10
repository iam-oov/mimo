# Monitoring Stack for Mimo Tax Calculator

## Architecture

- **Prometheus**: Metrics collection and storage (self-hosted on Railway)
- **Grafana**: Metrics visualization and dashboards (self-hosted on Railway)
- **Mimo App**: Exposes `/metrics` endpoint with application metrics

## Quick Start (Railway)

### 1. Deploy Mimo App (if not already deployed)

Your main Mimo app already has Prometheus metrics instrumentation:

- `/metrics` endpoint exposes Prometheus-formatted metrics
- `/health` endpoint provides detailed health checks
- Metrics tracked: request rate, latency, errors, AI usage, tax calculations, etc.

### 2. Deploy Prometheus Service

```bash
# From Railway dashboard:
1. Click "New Service" → "Deploy from Dockerfile"
2. Select your mimo repository
3. Set Dockerfile path: monitoring/Dockerfile.prometheus
4. Set environment variable:
   MIMO_APP_URL=<your-mimo-app-url>.up.railway.app

5. Deploy!
```

**Service Name**: `mimo-prometheus`  
**Port**: 9090  
**Health Check**: `/-/healthy`

### 3. Deploy Grafana Service

```bash
# From Railway dashboard:
1. Click "New Service" → "Deploy from Dockerfile"
2. Select your mimo repository
3. Set Dockerfile path: monitoring/Dockerfile.grafana
4. Set environment variables:
   GF_SECURITY_ADMIN_PASSWORD=<your-secure-password>
   PROMETHEUS_URL=http://mimo-prometheus.railway.internal:9090

5. Deploy!
```

**Service Name**: `mimo-grafana`  
**Port**: 3000  
**Health Check**: `/api/health`

### 4. Configure Network Access

In Railway, services can communicate using internal DNS:

- Mimo App → `mimo-app.railway.internal:8000`
- Prometheus → `mimo-prometheus.railway.internal:9090`
- Grafana → `mimo-grafana.railway.internal:3000`

Make Grafana publicly accessible:

1. Go to Grafana service settings
2. Enable "Public Networking"
3. Access Grafana at: `https://<grafana-url>.up.railway.app`

Keep Prometheus internal (more secure).

## Access Dashboards

1. **Grafana**: `https://<grafana-url>.up.railway.app`

   - Username: `admin`
   - Password: `<your-password>`

2. **Pre-configured dashboards**:
   - **Mimo Overview**: Request rate, latency, errors, AI usage
   - Auto-imported from `monitoring/dashboards/mimo-overview.json`

## Metrics Available

### HTTP Metrics

- `http_requests_total` - Total requests by method, endpoint, status
- `http_request_duration_seconds` - Request latency histogram
- `http_requests_in_progress` - Active requests

### Application Metrics

- `mimo_tax_calculations_total` - Tax calculations by fiscal year
- `mimo_ai_recommendations_total` - AI recommendations by provider and status
- `mimo_rate_limit_hits_total` - Rate limit violations
- `mimo_database_queries_total` - Database operations
- `mimo_database_errors_total` - Database errors
- `mimo_active_users` - Active authenticated users

## Alerting (Optional)

Prometheus includes basic alert rules in `monitoring/alerts.yml`:

- High error rate (>5%)
- High latency (P95 >2s)
- Database errors
- Application down
- High rate limit hits

To enable alerting, you'll need to set up Alertmanager (separate service).

## Local Development

Test monitoring stack locally with Docker Compose:

```bash
cd monitoring

# Build and run
docker-compose up

# Access services:
# - Mimo App: http://localhost:8000
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000
```

## Metrics Endpoints

### Mimo App

- **Metrics**: `GET /metrics` - Prometheus-formatted metrics
- **Health**: `GET /health` - Detailed health check (JSON)

### Prometheus

- **UI**: `http://prometheus:9090`
- **Health**: `http://prometheus:9090/-/healthy`
- **Query API**: `http://prometheus:9090/api/v1/query`

### Grafana

- **UI**: `http://grafana:3000`
- **Health**: `http://grafana:3000/api/health`

## Cost Estimate

**Railway Free Tier**:

- 3 services: Mimo + Prometheus + Grafana
- ~$10-15/month for small traffic
- Recommended: Prometheus on Railway, Grafana Cloud free tier (10k series)

**Grafana Cloud Alternative (Free Tier)**:

- 10,000 series, 50GB logs, 14 days retention
- No self-hosting needed for Grafana
- Configure Prometheus to remote_write to Grafana Cloud

## Troubleshooting

### Prometheus can't scrape Mimo app

- Verify `MIMO_APP_URL` environment variable
- Check Railway internal DNS: Use `.railway.internal` domain
- Verify `/metrics` endpoint is accessible

### Grafana shows "No data"

- Verify `PROMETHEUS_URL` environment variable
- Check Prometheus datasource in Grafana settings
- Run test query in Prometheus UI first

### Metrics not showing

- Restart Mimo app to initialize metrics
- Send test requests to generate metrics
- Check `/metrics` endpoint directly

## Security Notes

1. **Prometheus**: Keep internal, don't expose publicly
2. **Grafana**: Use strong admin password
3. **Metrics endpoint**: Consider adding authentication if exposing publicly
4. **Network**: Use Railway's internal DNS for service-to-service communication

## Next Steps

1. **Add custom panels** to Grafana dashboard for your specific metrics
2. **Set up Alertmanager** for notification on critical issues
3. **Configure retention** - Prometheus retains 15 days by default
4. **Add more metrics** in your app code using `prometheus_client`

## Example: Adding Custom Metrics

```python
from prometheus_client import Counter

# In your code:
from src.shared.infrastructure.api.middleware.metrics import TAX_CALCULATIONS

# Increment when calculation completes:
TAX_CALCULATIONS.labels(fiscal_year=2024).inc()
```

## Support

For issues or questions:

- Check Railway logs for each service
- Verify environment variables are set correctly
- Test `/health` and `/metrics` endpoints manually

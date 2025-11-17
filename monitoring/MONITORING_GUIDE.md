# Monitoring Guide - Korean Mental Health Counseling System

## Overview

This guide covers the monitoring infrastructure for the Korean Mental Health Counseling System, including Prometheus metrics, Grafana dashboards, and alerting rules.

## Components

### 1. Prometheus Metrics

The system exports metrics at `/metrics` endpoint in Prometheus format.

**Key Metrics:**
- `api_requests_total` - Total API requests by method, endpoint, status
- `api_response_time_seconds` - Response time histogram
- `crisis_detections_total` - Total crisis situations detected

### 2. Monitoring API Endpoints

```
GET /api/v1/health              # System health check
GET /api/v1/monitoring/system   # CPU, Memory, GPU metrics
GET /api/v1/monitoring/api-stats   # API usage statistics
GET /api/v1/monitoring/performance # Performance metrics
GET /api/v1/monitoring/alerts   # Active alerts
```

### 3. Grafana Dashboard

Import `grafana_dashboard.json` into Grafana for:
- Total API requests
- Response time percentiles (p50, p95)
- Crisis detections
- Request rates (success/error)
- Requests by endpoint
- System status
- Voice API usage
- Export operations

## Setup Instructions

### 1. Start Prometheus

```bash
# Using Docker
docker run -d \
  --name prometheus \
  -p 9090:9090 \
  -v $(pwd)/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml \
  -v $(pwd)/monitoring/alert_rules.yml:/etc/prometheus/alert_rules.yml \
  prom/prometheus

# Or install locally
prometheus --config.file=monitoring/prometheus.yml
```

### 2. Start Grafana

```bash
# Using Docker
docker run -d \
  --name grafana \
  -p 3000:3000 \
  grafana/grafana

# Default login: admin/admin
```

### 3. Configure Grafana

1. Add Prometheus data source:
   - URL: `http://localhost:9090`
   - Name: `prometheus`

2. Import dashboard:
   - Go to Dashboards → Import
   - Upload `monitoring/grafana_dashboard.json`

## Alert Rules

Critical alerts configured:

| Alert | Condition | Severity |
|-------|-----------|----------|
| `HighResponseTime` | p95 > 3s for 2m | warning |
| `CrisisDetected` | Any crisis detected | critical |
| `HighErrorRate` | Error rate > 5% | warning |
| `ServiceDown` | API unreachable | critical |
| `HighMemoryUsage` | Memory > 8GB | warning |
| `HighConcurrentSessions` | Sessions > 100 | warning |
| `VoiceServiceErrors` | >10 errors/10m | warning |
| `ExportServiceErrors` | >5 errors/10m | warning |

## Monitoring Endpoints

### Health Check
```bash
curl http://localhost:8000/api/v1/health
```
Response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-17T10:00:00",
  "components": {
    "llm": true,
    "crisis_detector": true,
    "emotion_analyzer": true,
    "rag_system": true
  },
  "uptime_seconds": 3600
}
```

### System Metrics
```bash
curl http://localhost:8000/api/v1/monitoring/system
```
Response:
```json
{
  "cpu": {"percent": 25.5, "count": 8},
  "memory": {"total_gb": 32.0, "used_gb": 8.5, "percent": 26.6},
  "disk": {"total_gb": 500.0, "used_gb": 120.0, "percent": 24.0},
  "gpu": {"available": true, "memory_allocated_gb": 4.2}
}
```

### Active Alerts
```bash
curl http://localhost:8000/api/v1/monitoring/alerts
```
Response:
```json
{
  "active_alerts": [
    {
      "severity": "warning",
      "type": "crisis_activity",
      "message": "2 crisis situations detected"
    }
  ],
  "alert_count": 1,
  "critical_count": 0,
  "warning_count": 1
}
```

## Docker Compose Integration

Add to your `docker-compose.yml`:

```yaml
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./monitoring/alert_rules.yml:/etc/prometheus/alert_rules.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    networks:
      - mental_health_network

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus
    networks:
      - mental_health_network

  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"
    networks:
      - mental_health_network

volumes:
  grafana_data:
```

## Best Practices

1. **Set up alerts for crisis detections** - Immediate notification
2. **Monitor response times** - Keep p95 under 3 seconds
3. **Track error rates** - Alert on >5% error rate
4. **Monitor memory usage** - LLM models use significant memory
5. **Review dashboards daily** - Check for anomalies

## Troubleshooting

### Prometheus not scraping metrics
- Check if API is running: `curl http://localhost:8000/metrics`
- Verify Prometheus config points to correct target

### High response times
- Check GPU memory usage
- Monitor CPU/RAM
- Consider scaling horizontally

### Crisis alert fatigue
- Adjust alert thresholds
- Implement alert grouping
- Use silence/inhibit rules

## Future Enhancements

1. **Custom metrics** - Add domain-specific metrics
2. **Log aggregation** - Integrate with ELK stack
3. **Distributed tracing** - Add Jaeger/Zipkin
4. **Anomaly detection** - ML-based alerting
5. **SLA monitoring** - Track uptime and availability

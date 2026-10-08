# Payment API — Redis Cache Issues

## Symptoms
- `RedisTimeoutError` in logs
- High CPU usage on Redis nodes
- Latency spikes on payment endpoints

## Investigation
1. Check Redis CPU and memory usage.
2. Identify if there's a traffic spike (e.g., marketing campaign).

## Remediation
- **Cache Stampede:**
  1. DO NOT restart Redis nodes (this flushes the cache and kills the DB).
  2. Increase Redis connection timeout in Payment API (`REDIS_TIMEOUT_MS`).
  3. Scale up Redis worker nodes horizontally.

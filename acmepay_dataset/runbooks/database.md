# Payment API — Database Connection Issues

## Symptoms
- Increased HTTP 5xx errors
- Connection timeout errors (`psycopg2.pool.PoolError`)
- High database connection utilization

## Investigation
1. Check active database connections on PostgreSQL.
2. Check connection pool utilization in the application.
3. Check recent deployments (crucial: a recent deployment causing timeouts often means an N+1 query issue).

## Remediation
- **If the issue started immediately after a deployment:**
  1. Stop the rollout.
  2. Roll back to the previous version.
  3. DO NOT blindly increase the pool size, it will just mask the underlying bad query.
- **If there was NO recent deployment (Traffic Spike):**
  1. Check CPU load on Postgres.
  2. Increase connection pool size temporarily.
  3. Scale up read replicas.

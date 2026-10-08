# External API / Gateway Issues

## Symptoms
- `504 Gateway Timeout` on Customer API
- Payment API workers blocked waiting for external responses
- Adyen / Stripe status page shows degraded performance

## Remediation
1. Verify external provider status.
2. Toggle circuit breaker to fallback mode by setting `FRAUD_CHECK_ENABLED=false` or `EXTERNAL_ROUTING=fallback`.
3. Inform Customer Success team of degraded payment flows.

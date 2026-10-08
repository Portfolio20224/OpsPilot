# Deployment Guidelines and Rollbacks

## Standard Rollback Procedure
1. Identify the faulty deployment ID.
2. Execute: `kubectl rollout undo deployment/payment-api`
3. Verify pods are terminating and old version is starting.
4. Update incident ticket with rollback confirmation.

*Note: Rollbacks should be initiated if error rates exceed 5% for more than 3 minutes post-deployment.*

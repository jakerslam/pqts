# Deployment Procedures

> **Last Updated:** March 19, 2026  
> **Owner:** Platform Operations  
> **Classification:** Internal Use

---

## Overview

This document outlines the standardized procedures for deploying changes to the Protheus trading platform. Following these procedures ensures consistent, safe deployments with minimal risk of service disruption.

---

## Pre-Deployment Checklist

Before any deployment to production or paper trading environments:

- [ ] All tests pass in CI/CD pipeline
- [ ] Code review approved by at least one senior engineer
- [ ] CHANGELOG.md updated with change description
- [ ] Rollback plan documented
- [ ] Deployment window communicated to stakeholders
- [ ] Monitoring dashboards verified as functional

---

## Environment Promotion Flow

Changes must flow through environments in this order:

```
Development → Staging → Paper Trading → Live Shadow → Production
```

### Development
- Purpose: Individual developer testing
- Data: Synthetic market data
- Access: All engineers

### Staging
- Purpose: Integration testing
- Data: Delayed market data (15-min delay)
- Access: Platform team

### Paper Trading
- Purpose: Real-time validation without capital risk
- Data: Live market data, simulated execution
- Access: Platform team, authorized traders

### Live Shadow
- Purpose: Production validation with no customer impact
- Data: Live market data, shadow execution
- Access: Platform team only

### Production
- Purpose: Live customer trading
- Data: Live market data and execution
- Access: On-call platform engineers only

---

## Deployment Steps

### Standard Deployment

1. **Verify target environment health**
   ```bash
   ./scripts/ops_health_report.py --env $TARGET_ENV
   ```

2. **Execute deployment**
   ```bash
   ./scripts/run_promotion_pipeline.py --from $SOURCE_ENV --to $TARGET_ENV
   ```

3. **Verify deployment success**
   ```bash
   ./scripts/slo_health_report.py --env $TARGET_ENV --window 5m
   ```

4. **Monitor for 30 minutes post-deployment**
   - Watch error rates
   - Verify latency metrics
   - Confirm data feed connectivity

### Emergency Deployment

For critical fixes only:

1. Obtain approval from VP Platform
2. Document justification in deployment ticket
3. Execute with accelerated monitoring (15-min window)
4. Post-incident review within 48 hours

---

## Rollback Procedures

If issues are detected post-deployment:

1. **Immediate Mitigation**
   ```bash
   ./scripts/run_incident_automation.py --action pause-$SERVICE
   ```

2. **Rollback Execution**
   ```bash
   ./scripts/run_promotion_pipeline.py --rollback --to $PREVIOUS_VERSION
   ```

3. **Verify rollback**
   - Confirm previous version is active
   - Validate service health metrics
   - Notify stakeholders of rollback completion

---

## Post-Deployment Validation

Every deployment requires:

- [ ] SLO metrics within acceptable bounds (99.9% availability)
- [ ] No critical or high-severity alerts
- [ ] Data pipeline latency under 100ms p99
- [ ] Execution queue depth nominal

---

## Communication Template

**Slack notification format:**
```
🚀 Deployment Complete: $SERVICE-$VERSION to $ENVIRONMENT
- Duration: $X minutes
- Changes: $BRIEF_DESCRIPTION
- Monitoring: #ops-alerts
- Rollback window: 30 minutes
```

---

*For questions or suggestions, contact the Platform Operations team.*

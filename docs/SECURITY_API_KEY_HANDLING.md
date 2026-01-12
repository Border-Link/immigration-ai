# API Key Security & Log Filtering

**Date**: 2024-12-19  
**Status**: Implementation Guide

---

## Overview

This document outlines the strategy for secure API key handling, including log filtering to prevent API keys from being logged.

---

## 1. API Keys in the System

### 1.1 Identified API Keys

The following API keys are used in the system:

1. **OpenAI API Key** (`OPENAI_API_KEY`)
   - Used for: LLM calls, embeddings
   - Location: `src/ai_decisions/services/ai_reasoning_service.py`
   - Location: `src/ai_decisions/services/embedding_service.py`

2. **Stripe Keys** (`STRIPE_SECRET_KEY`, `STRIPE_PUBLIC_KEY`, `STRIPE_WEBHOOK_SECRET`)
   - Used for: Payment processing
   - Location: `src/payments/gateways/stripe_gateway.py`

3. **PayPal Keys** (`PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `PAYPAL_WEBHOOK_ID`)
   - Used for: Payment processing
   - Location: `src/payments/gateways/paypal_gateway.py`

4. **Adyen Keys** (`ADYEN_API_KEY`, `ADYEN_MERCHANT_ACCOUNT`)
   - Used for: Payment processing
   - Location: `src/payments/gateways/adyen_gateway.py`

5. **Mono Keys** (`SANDBOX_PUBLIC_KEY`, `SANDBOX_SECRET_KEY`, `MONO_WEBHOOK_SECRET_KEY`)
   - Used for: Banking/financial services
   - Location: `src/main_system/settings.py`

6. **Open Exchange Rate API Key** (`OPEN_EXCHANGE_RATE_API_KEY`)
   - Used for: Currency conversion
   - Location: `src/main_system/settings.py`

7. **SendGrid API Key** (if used)
   - Used for: Email sending
   - Location: Email configuration

---

## 2. Log Filtering Implementation

### 2.1 Current State

**Status**: ✅ Log sanitization utility created (`src/main_system/utils/log_sanitizer.py`)

**Features**:
- Sanitizes passwords, tokens, API keys
- Truncates emails and tokens
- Redacts sensitive fields in dictionaries

### 2.2 Enhanced Log Filtering

The log sanitizer already handles API keys, but we should ensure it's used consistently.

**Action Required**:
- [ ] Review all log statements for API key exposure
- [ ] Ensure log sanitizer is used in all logging
- [ ] Add specific API key patterns to sanitizer

---

## 3. API Key Rotation Policy

### 3.1 Rotation Schedule

**Recommendations**:

1. **Payment Gateway Keys**:
   - **Frequency**: Quarterly or when compromised
   - **Priority**: HIGH (financial impact)
   - **Process**: Rotate in gateway dashboard, update in secrets manager

2. **OpenAI API Key**:
   - **Frequency**: Quarterly or when compromised
   - **Priority**: MEDIUM
   - **Process**: Generate new key, update in secrets manager

3. **Other API Keys**:
   - **Frequency**: Annually or when compromised
   - **Priority**: LOW-MEDIUM
   - **Process**: Update in secrets manager

### 3.2 Rotation Process

1. **Preparation**:
   - Generate new API key in provider dashboard
   - Store new key in secrets manager (staging first)
   - Document rotation date

2. **Deployment**:
   - Update environment variable in staging
   - Test with new key
   - Update in production
   - Monitor for errors

3. **Cleanup**:
   - Revoke old key after verification period (7 days)
   - Update documentation
   - Log rotation event

---

## 4. API Key Storage Best Practices

### 4.1 Current Implementation

**Status**: ✅ Using environment variables

**Current**:
- Keys stored in `.env` file (not in git) ✅
- Keys loaded via `django-environ` ✅
- Different keys for different environments ✅

### 4.2 Recommended Improvements

1. **Secrets Manager**:
   - Migrate to AWS Secrets Manager, Azure Key Vault, or HashiCorp Vault
   - Automatic rotation support
   - Audit logging
   - Access control

2. **Key Separation**:
   - Use different keys for dev/staging/production
   - Use different keys for different services
   - Limit key scope (read-only keys where possible)

3. **Access Control**:
   - Limit who can access keys
   - Use IAM roles for service access
   - Rotate keys when personnel changes

---

## 5. API Key Usage Monitoring

### 5.1 Monitoring Recommendations

1. **Usage Tracking**:
   - Monitor API key usage (rate limits, costs)
   - Alert on unusual usage patterns
   - Track key rotation dates

2. **Security Monitoring**:
   - Alert on failed authentication attempts
   - Monitor for key exposure in logs
   - Track key access (if using secrets manager)

---

## 6. Implementation Checklist

### Log Filtering
- [x] Create log sanitization utility ✅
- [ ] Review all log statements for API key exposure
- [ ] Add API key patterns to sanitizer
- [ ] Test log filtering

### Key Rotation
- [ ] Document rotation schedule
- [ ] Set up rotation reminders
- [ ] Test rotation process in staging
- [ ] Implement automated rotation (if possible)

### Key Management
- [ ] Migrate to secrets manager
- [ ] Document key locations and purposes
- [ ] Set up access controls
- [ ] Implement key usage monitoring

---

## 7. Code Review Checklist

When reviewing code that uses API keys:

- [ ] API key is loaded from environment variable (not hardcoded)
- [ ] API key is not logged
- [ ] API key is not exposed in error messages
- [ ] API key is not committed to git
- [ ] API key has appropriate scope/permissions
- [ ] API key rotation is documented

---

**Document Version**: 1.0  
**Last Updated**: 2024-12-19

# Encryption Strategy Documentation

**Date**: 2024-12-19  
**Status**: Documentation & Verification Required

---

## Overview

This document outlines the encryption strategy for the immigration backend system. Encryption is critical for protecting sensitive data (PII, payment information, case data) both at rest and in transit.

---

## 1. Encryption at Rest

### 1.1 Database Encryption

**Status**: ⚠️ **VERIFICATION REQUIRED**

#### PostgreSQL Database

**Requirements**:
- Database should use Transparent Data Encryption (TDE) or cloud provider encryption
- All data at rest should be encrypted

**Verification Steps**:
1. **Cloud Provider (AWS RDS, Azure, GCP)**:
   ```sql
   -- Check encryption status (PostgreSQL)
   SELECT * FROM pg_settings WHERE name LIKE '%encrypt%';
   ```
   - AWS RDS: Verify `storage_encrypted = true` in RDS configuration
   - Azure: Verify "Transparent Data Encryption" is enabled
   - GCP: Verify "Encryption at rest" is enabled

2. **Self-Hosted PostgreSQL**:
   - Verify disk encryption (LUKS, BitLocker, etc.)
   - Verify PostgreSQL data directory is on encrypted volume

**Action Required**: 
- [ ] Verify database encryption is enabled
- [ ] Document encryption method used
- [ ] Verify encryption keys are managed securely (KMS)

---

### 1.2 S3/Object Storage Encryption

**Status**: ⚠️ **VERIFICATION REQUIRED**

#### AWS S3 / DigitalOcean Spaces

**Requirements**:
- All objects should be encrypted at rest
- Use SSE-S3 (server-side encryption) or SSE-KMS (key management service)

**Verification Steps**:
1. **AWS S3**:
   ```python
   # Check bucket encryption
   s3_client.get_bucket_encryption(Bucket='your-bucket-name')
   ```
   - Verify `ServerSideEncryptionConfiguration` is set
   - Prefer SSE-KMS for better key management

2. **DigitalOcean Spaces**:
   - Verify encryption is enabled in Space settings
   - Use server-side encryption

**Current Implementation**:
- Files stored with `ACL: 'private'` ✅
- Encryption configuration needs verification ⚠️

**Action Required**:
- [ ] Verify S3/Spaces bucket encryption is enabled
- [ ] Configure SSE-S3 or SSE-KMS
- [ ] Document encryption method

---

### 1.3 Application-Level Encryption

**Status**: ✅ **IMPLEMENTED**

#### Field-Level Encryption

**Package**: `django-encrypted-model-fields`

**Usage**:
- Sensitive fields can be encrypted at the model level
- Encryption keys stored in `FIELD_ENCRYPTION_KEY` environment variable

**Fields That Should Be Encrypted**:
- User PII (if stored in database)
- Payment card numbers (if stored - should NOT be stored per PCI DSS)
- API keys (if stored in database)
- Other sensitive data

**Action Required**:
- [ ] Review models for sensitive fields
- [ ] Apply encryption to sensitive fields
- [ ] Verify encryption keys are rotated regularly

---

## 2. Encryption in Transit

### 2.1 HTTPS/TLS

**Status**: ✅ **IMPLEMENTED**

**Configuration**:
- `SECURE_HSTS_SECONDS = 31536000` (1 year in production) ✅
- `SECURE_HSTS_INCLUDE_SUBDOMAINS = True` ✅
- `SECURE_HSTS_PRELOAD = True` ✅
- `SESSION_COOKIE_SECURE = True` ✅
- `CSRF_COOKIE_SECURE = True` ✅

**Verification**:
- [ ] Verify TLS 1.2+ is enforced
- [ ] Verify weak ciphers are disabled
- [ ] Test with SSL Labs or similar

---

### 2.2 Database Connection Security

**Status**: ⚠️ **VERIFICATION REQUIRED**

**Requirements**:
- Database connections should use SSL/TLS
- Database should not be publicly accessible

**Verification Steps**:

1. **Check Database Settings**:
   ```python
   # In settings.py, verify:
   DATABASES = {
       'default': {
           'OPTIONS': {
               'sslmode': 'require',  # PostgreSQL
               # or
               'ssl': {'ca': '/path/to/ca-cert.pem'}  # MySQL
           }
       }
   }
   ```

2. **Check Network Security**:
   - Database should only accept connections from application servers
   - Use VPC/private networks
   - Firewall rules should restrict access

**Action Required**:
- [ ] Verify SSL/TLS is enabled for database connections
- [ ] Verify database is not publicly accessible
- [ ] Document connection security configuration

---

### 2.3 Redis Connection Security

**Status**: ⚠️ **VERIFICATION REQUIRED**

**Requirements**:
- Redis connections should use TLS (if over network)
- Redis should not be publicly accessible

**Action Required**:
- [ ] Verify Redis uses TLS in production
- [ ] Verify Redis is not publicly accessible
- [ ] Use Redis AUTH password

---

## 3. Key Management

### 3.1 Encryption Keys

**Status**: ⚠️ **IMPROVEMENT NEEDED**

**Current State**:
- Keys stored in environment variables ✅
- Keys loaded from `.env` file ✅

**Best Practices**:
- Use AWS Secrets Manager, Azure Key Vault, or HashiCorp Vault
- Rotate keys regularly (annually or as per compliance)
- Never commit keys to git
- Use different keys for dev/staging/production

**Action Required**:
- [ ] Migrate to secrets manager (AWS Secrets Manager recommended)
- [ ] Implement key rotation policy
- [ ] Document key management process

---

### 3.2 Key Rotation Policy

**Recommendations**:
1. **Rotation Schedule**:
   - `SECRET_KEY`: Annually or when compromised
   - `FIELD_ENCRYPTION_KEY`: Annually
   - API keys: Quarterly or as per provider requirements
   - Database passwords: Quarterly

2. **Rotation Process**:
   - Generate new key
   - Update in secrets manager
   - Deploy with new key
   - Re-encrypt data if needed (for field encryption)
   - Remove old key after verification

**Action Required**:
- [ ] Document key rotation process
- [ ] Set up rotation schedule
- [ ] Test rotation process in staging

---

## 4. Compliance Considerations

### 4.1 GDPR

**Requirements**:
- Encrypt PII at rest and in transit
- Secure key management
- Data retention policies

**Status**: ✅ PII separation implemented, encryption verification needed

---

### 4.2 PCI DSS (if handling credit cards)

**Requirements**:
- **DO NOT STORE** credit card numbers
- Use payment gateways (Stripe, PayPal, Adyen) ✅
- Encrypt any payment-related data
- Secure key management

**Status**: ✅ Payment gateways used, no card storage

---

## 5. Implementation Checklist

### Database Encryption
- [ ] Verify PostgreSQL TDE or cloud encryption enabled
- [ ] Document encryption method
- [ ] Verify encryption keys managed securely

### S3/Object Storage Encryption
- [ ] Verify S3/Spaces encryption enabled
- [ ] Configure SSE-S3 or SSE-KMS
- [ ] Document encryption configuration

### Application-Level Encryption
- [ ] Review models for sensitive fields
- [ ] Apply field encryption where needed
- [ ] Test encryption/decryption

### Connection Security
- [ ] Verify database SSL/TLS enabled
- [ ] Verify database not publicly accessible
- [ ] Verify Redis security (TLS, AUTH)
- [ ] Test connection security

### Key Management
- [ ] Migrate to secrets manager
- [ ] Implement key rotation policy
- [ ] Document key management process

---

## 6. Monitoring & Alerts

**Recommendations**:
- Monitor for unencrypted data access attempts
- Alert on encryption key rotation
- Monitor SSL/TLS certificate expiration
- Log encryption/decryption operations (sanitized)

---

## 7. Next Steps

1. **Immediate** (This Week):
   - Verify database encryption status
   - Verify S3/Spaces encryption
   - Document current encryption state

2. **Short Term** (This Month):
   - Enable SSL/TLS for database connections
   - Migrate to secrets manager
   - Implement key rotation policy

3. **Medium Term** (Next Quarter):
   - Apply field encryption to sensitive data
   - Set up encryption monitoring
   - Conduct encryption audit

---

**Document Version**: 1.0  
**Last Updated**: 2024-12-19

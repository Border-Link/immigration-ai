# Database Connection Security

**Date**: 2024-12-19  
**Status**: Verification & Documentation Required

---

## Overview

This document outlines the security requirements and verification steps for database connections in the immigration backend system.

---

## 1. SSL/TLS Encryption

### 1.1 Requirements

**Status**: ⚠️ **VERIFICATION REQUIRED**

**Requirements**:
- All database connections must use SSL/TLS
- Verify SSL certificates
- Use strong cipher suites
- Disable SSLv2, SSLv3, TLS 1.0, TLS 1.1 (use TLS 1.2+)

---

### 1.2 PostgreSQL SSL Configuration

**Current Settings** (`src/main_system/settings.py`):
```python
DATABASES = {
    "default": {
        "ENGINE": env("DB_ENGINE"),
        "NAME": env("DB_DATABASE"),
        "USER": env("DB_USERNAME"),
        "PASSWORD": env("DB_PASSWORD"),
        "PORT": env("DB_PORT"),
        "HOST": env("DB_HOST"),
        "CONN_MAX_AGE": int(env("CONN_MAX_AGE")),
        "CONN_HEALTH_CHECK": True,
    }
}
```

**Required SSL Configuration**:
```python
DATABASES = {
    "default": {
        # ... existing settings ...
        "OPTIONS": {
            "sslmode": "require",  # Require SSL
            # For production, use:
            # "sslmode": "verify-full",  # Verify certificate
            # "sslcert": "/path/to/client-cert.pem",
            # "sslkey": "/path/to/client-key.pem",
            # "sslrootcert": "/path/to/ca-cert.pem",
        }
    }
}
```

**SSL Modes**:
- `disable`: No SSL (NOT RECOMMENDED)
- `allow`: Try SSL, fallback to non-SSL (NOT RECOMMENDED)
- `prefer`: Prefer SSL, fallback to non-SSL (NOT RECOMMENDED)
- `require`: Require SSL, don't verify certificate (MINIMUM)
- `verify-ca`: Require SSL, verify certificate authority (RECOMMENDED)
- `verify-full`: Require SSL, verify certificate and hostname (BEST)

**Action Required**:
- [ ] Add SSL configuration to database settings
- [ ] Set `sslmode` to `require` (minimum) or `verify-full` (recommended)
- [ ] Test SSL connection
- [ ] Document SSL certificate management

---

## 2. Network Security

### 2.1 Database Access Control

**Status**: ⚠️ **VERIFICATION REQUIRED**

**Requirements**:
- Database should NOT be publicly accessible
- Database should only accept connections from:
  - Application servers (specific IPs or VPC)
  - Admin workstations (specific IPs, VPN)
- Use firewall rules to restrict access
- Use VPC/private networks when possible

**Verification Steps**:

1. **Check Database Network Configuration**:
   - AWS RDS: Check security groups, VPC settings
   - Azure: Check firewall rules, VNet configuration
   - GCP: Check authorized networks, VPC configuration
   - Self-hosted: Check firewall rules (iptables, ufw, etc.)

2. **Test Public Accessibility**:
   ```bash
   # Try to connect from external IP (should fail)
   psql -h <database-host> -U <user> -d <database>
   ```

**Action Required**:
- [ ] Verify database is not publicly accessible
- [ ] Review firewall rules
- [ ] Document allowed IPs/networks
- [ ] Set up VPN for admin access (if needed)

---

### 2.2 Connection Pooling Security

**Current Configuration**:
```python
"CONN_MAX_AGE": int(env("CONN_MAX_AGE")),
"CONN_HEALTH_CHECK": True,
```

**Security Considerations**:
- Connection pooling is secure if SSL is enabled
- Health checks should not expose sensitive data
- Pool size should be limited to prevent resource exhaustion

**Status**: ✅ Connection pooling configured

---

## 3. Authentication & Authorization

### 3.1 Database Credentials

**Status**: ✅ Using environment variables

**Best Practices**:
- Use strong passwords (20+ characters, mixed case, numbers, symbols)
- Rotate passwords regularly (quarterly)
- Use different credentials for dev/staging/production
- Store credentials in secrets manager (not in code)

**Action Required**:
- [ ] Verify strong passwords are used
- [ ] Set up password rotation schedule
- [ ] Migrate to secrets manager

---

### 3.2 Database User Permissions

**Requirements**:
- Application user should have minimal required permissions
- Use principle of least privilege
- Separate users for different operations (read-only, write, admin)

**Verification**:
```sql
-- Check user permissions (PostgreSQL)
\du <username>
SELECT * FROM pg_user WHERE usename = '<username>';
```

**Action Required**:
- [ ] Review database user permissions
- [ ] Ensure minimal required permissions
- [ ] Document user roles and permissions

---

## 4. Connection String Security

### 4.1 Environment Variables

**Status**: ✅ Using environment variables

**Current**:
- Database credentials in `.env` file
- Not committed to git ✅
- Loaded via `django-environ` ✅

**Improvements**:
- Migrate to secrets manager
- Use connection string encryption (if storing in config files)

---

## 5. Monitoring & Logging

### 5.1 Connection Monitoring

**Recommendations**:
- Monitor connection failures
- Alert on suspicious connection patterns
- Track connection pool usage
- Monitor SSL/TLS handshake failures

---

### 5.2 Security Logging

**Recommendations**:
- Log failed authentication attempts
- Log connection attempts from unauthorized IPs
- Log SSL/TLS errors
- **DO NOT** log passwords or connection strings

---

## 6. Implementation Checklist

### SSL/TLS
- [ ] Add SSL configuration to database settings
- [ ] Set `sslmode` to `require` or `verify-full`
- [ ] Test SSL connection
- [ ] Document SSL certificate management
- [ ] Verify TLS 1.2+ is used

### Network Security
- [ ] Verify database is not publicly accessible
- [ ] Review and restrict firewall rules
- [ ] Document allowed IPs/networks
- [ ] Set up VPN for admin access (if needed)
- [ ] Test connection from unauthorized IP (should fail)

### Authentication
- [ ] Verify strong passwords are used
- [ ] Set up password rotation schedule
- [ ] Review database user permissions
- [ ] Ensure principle of least privilege
- [ ] Migrate to secrets manager

### Monitoring
- [ ] Set up connection monitoring
- [ ] Configure alerts for connection failures
- [ ] Set up security logging
- [ ] Test monitoring and alerts

---

## 7. Testing

### 7.1 SSL Connection Test

```python
# Test SSL connection
import psycopg2

conn = psycopg2.connect(
    host=settings.DATABASES['default']['HOST'],
    database=settings.DATABASES['default']['NAME'],
    user=settings.DATABASES['default']['USER'],
    password=settings.DATABASES['default']['PASSWORD'],
    sslmode='require'
)
print("SSL connection successful!")
```

### 7.2 Network Security Test

```bash
# From external IP (should fail)
psql -h <database-host> -U <user> -d <database>

# From authorized IP (should succeed)
psql -h <database-host> -U <user> -d <database>
```

---

## 8. Production Checklist

Before deploying to production:

- [ ] SSL/TLS enabled and verified
- [ ] Database not publicly accessible
- [ ] Firewall rules configured
- [ ] Strong passwords set
- [ ] Database user has minimal permissions
- [ ] Connection monitoring configured
- [ ] Security logging enabled
- [ ] Documentation complete

---

**Document Version**: 1.0  
**Last Updated**: 2024-12-19

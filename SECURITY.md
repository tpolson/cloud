# Security Model and Best Practices

## Overview

This document describes the security architecture of the Cloud Automation Tool and provides guidance for secure usage.

## Credential Storage

### Encryption Architecture

**Version 2.0 (Current)**: PBKDF2-based encryption with cryptographic salt

#### Key Components

1. **Key Derivation**: PBKDF2-HMAC-SHA256
   - **Iterations**: 600,000 (OWASP 2023 recommendation)
   - **Salt**: 32 bytes, cryptographically random (`secrets.token_bytes`)
   - **Key Material**: `username@hostname` (machine-specific)
   - **Output**: 256-bit encryption key

2. **Encryption**: Fernet (symmetric encryption)
   - **Algorithm**: AES-128-CBC + HMAC-SHA256
   - **Authentication**: Built-in message authentication
   - **Format**: Base64-encoded ciphertext

3. **Storage**:
   - **Location**: `~/.cloud-automation/`
   - **Files**:
     - `credentials.enc` - Encrypted credentials (permissions: 0600)
     - `salt` - Cryptographic salt (permissions: 0600)
   - **Format**: JSON with version marker

#### Security Properties

✅ **Strengths**:
- PBKDF2 with 600,000 iterations resists brute force attacks
- Cryptographic salt prevents rainbow table attacks
- Machine-specific key derivation (username + hostname)
- Authenticated encryption (Fernet includes HMAC)
- Automatic migration from legacy format

⚠️ **Limitations**:
- Credentials decryptable on same machine by same user
- No password/passphrase protection (relies on OS user authentication)
- Vulnerable if attacker has file access + can impersonate user/hostname
- Not designed for multi-user systems

### Security Recommendations

#### 1. Use IAM Roles When Possible ⭐ **HIGHEST PRIORITY**

Instead of storing credentials, use:
- **AWS**: EC2 instance roles, ECS task roles, Lambda execution roles
- **GCP**: Service accounts attached to Compute Engine instances

**Benefits**:
- No credentials to store or manage
- Automatic rotation
- Fine-grained permissions
- Audit trail

**Implementation**:
```python
# AWS - No credentials needed when running on EC2 with instance role
provisioner = AWSVMProvisioner(region='us-east-1')

# GCP - No credentials needed when running on GCE with service account
provisioner = GCPVMProvisioner(project_id='my-project', zone='us-central1-a')
```

#### 2. Use Environment Variables for CI/CD

For automation pipelines:
```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1

export GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
export GOOGLE_CLOUD_PROJECT=your-project
```

#### 3. Enable Credential Rotation

Rotate credentials regularly:
- **AWS**: Rotate access keys every 90 days
- **GCP**: Rotate service account keys every 90 days

#### 4. Use Minimum Required Permissions

Follow principle of least privilege:

**AWS IAM Policy Example**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:RunInstances",
        "ec2:DescribeInstances",
        "ec2:StartInstances",
        "ec2:StopInstances",
        "ec2:TerminateInstances"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "ec2:Region": "us-east-1"
        }
      }
    }
  ]
}
```

**GCP IAM Roles Example**:
```bash
# Grant minimum permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:SA_NAME@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/compute.instanceAdmin.v1"
```

#### 5. Enable MFA on Cloud Accounts

- **AWS**: Enable MFA on all IAM users and root account
- **GCP**: Enable 2-Step Verification on all Google accounts

#### 6. Monitor Credential Usage

Enable audit logging:
- **AWS CloudTrail**: Track all API calls
- **GCP Cloud Audit Logs**: Monitor resource access

#### 7. Delete Credentials When Not Needed

```python
from cloud_automation.credential_store import CredentialStore

store = CredentialStore()
store.delete_credentials()  # Removes both encrypted file and salt
```

## Input Validation

### Validation Framework

All user inputs are validated before cloud API calls:

**AWS Validations**:
- AMI IDs: `ami-[0-9a-f]{8,17}`
- Instance IDs: `i-[0-9a-f]{8,17}`
- Volume IDs: `vol-[0-9a-f]{8,17}`
- Instance types: Against known type database
- S3 bucket names: AWS naming rules
- Regions: Whitelist of valid regions

**GCP Validations**:
- Project IDs: 6-30 chars, lowercase, hyphens
- Instance names: Lowercase, hyphens, 63 char max
- Machine types: Against known type database
- Zones: Whitelist of valid zones
- Bucket names: GCP naming rules (no 'google', 'goog')

### Prevention of Injection Attacks

**SQL Injection**: N/A (no direct SQL queries)
**Command Injection**: All inputs validated before shell execution
**API Parameter Injection**: All parameters validated against schemas

## Resource Quota and Cost Controls

### Quota System

Daily limits prevent accidental resource sprawl:

**Default Quotas**:
- **Instances per day**: 10
- **Storage per day**: 1000 GB
- **Max disk size**: 500 GB

**Cost Warnings**:
- Expensive instance type detection (>= 8 vCPUs or >= 32GB RAM)
- Category-based warnings (Compute Optimized, Memory Optimized)
- Configurable warning thresholds

### Modifying Quotas

```python
from cloud_automation.quota import QuotaManager

quota_manager = QuotaManager()
quota_manager.update_limits(
    max_instances_per_day=20,
    max_storage_gb_per_day=2000,
    max_disk_size_gb=1000,
    expensive_instance_threshold='large'  # small, medium, large
)
```

## Network Security

### Streamlit Application

⚠️ **Default Configuration**: HTTP only (localhost)

**Production Recommendations**:

1. **Enable HTTPS**:
```toml
# .streamlit/config.toml
[server]
sslCertFile = "/path/to/cert.pem"
sslKeyFile = "/path/to/key.pem"
enableCORS = false
enableXsrfProtection = true
```

2. **Restrict Access**:
```toml
[server]
address = "127.0.0.1"  # Localhost only
port = 8501

# Or use SSH tunnel for remote access
# ssh -L 8501:localhost:8501 user@remote-host
```

3. **Use Reverse Proxy** (nginx, Apache):
```nginx
server {
    listen 443 ssl;
    server_name cloud-automation.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## Vulnerability Reporting

If you discover a security vulnerability, please:

1. **Do NOT** open a public GitHub issue
2. Email security concerns to: [Your security contact email]
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

## Security Checklist

### Before First Use

- [ ] Review this security documentation
- [ ] Decide on credential storage method (IAM roles preferred)
- [ ] Set up MFA on cloud provider accounts
- [ ] Create limited-permission IAM users/service accounts
- [ ] Configure quotas appropriate for your usage
- [ ] Enable HTTPS if exposing Streamlit UI
- [ ] Enable audit logging on cloud providers

### Regular Maintenance

- [ ] Rotate credentials every 90 days
- [ ] Review IAM permissions quarterly
- [ ] Check quota usage and adjust as needed
- [ ] Review audit logs for suspicious activity
- [ ] Update dependencies for security patches
- [ ] Test credential rotation procedures

### Incident Response

If credentials are compromised:

1. **Immediately**:
   - Delete compromised credentials from cloud provider
   - Delete local credential store: `store.delete_credentials()`
   - Generate new credentials with rotated keys

2. **Investigate**:
   - Review audit logs for unauthorized usage
   - Check for unauthorized resources created
   - Determine scope of compromise

3. **Remediate**:
   - Delete any unauthorized resources
   - Update all systems using compromised credentials
   - Implement additional controls to prevent recurrence

## Compliance Considerations

### Data Residency

- Credentials stored locally at `~/.cloud-automation/`
- No telemetry or external data transmission
- Cloud resources created in specified regions only

### Audit Trail

Enable cloud provider audit logging:
- **AWS CloudTrail**: All API calls logged
- **GCP Cloud Audit Logs**: Admin activity and data access logs

### Regulatory Compliance

This tool does not guarantee compliance with specific regulations (HIPAA, PCI-DSS, SOC 2, etc.).
For regulated environments:
- Consult compliance team before use
- Ensure cloud provider compliance certifications
- Implement additional controls as required
- Maintain audit documentation

## Known Security Limitations

1. **Credential Storage**:
   - Not designed for shared/multi-user systems
   - Relies on OS-level user isolation
   - No password/passphrase protection

2. **Session State**:
   - Streamlit session state may be accessible via browser dev tools
   - Not recommended for untrusted client environments

3. **No Built-in Secrets Management**:
   - For production, integrate with HashiCorp Vault, AWS Secrets Manager, or GCP Secret Manager

4. **No Rate Limiting**:
   - Application-level rate limiting not implemented
   - Relies on cloud provider API throttling

## Security Roadmap

### Planned Enhancements (Future Versions)

- [ ] OS keyring integration (macOS Keychain, Windows Credential Manager, Linux Secret Service)
- [ ] Optional passphrase-protected encryption
- [ ] Integration with cloud secrets managers (AWS Secrets Manager, GCP Secret Manager)
- [ ] Application-level rate limiting
- [ ] Built-in security scanning and recommendations
- [ ] Credential usage monitoring and alerts
- [ ] Support for temporary security tokens (AWS STS, GCP OAuth)

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [AWS Security Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [GCP Security Best Practices](https://cloud.google.com/security/best-practices)
- [NIST Password Guidelines](https://pages.nist.gov/800-63-3/)
- [Cryptography Best Practices](https://cryptography.io/)

---

**Last Updated**: 2025-11-11
**Security Contact**: [Your contact information]

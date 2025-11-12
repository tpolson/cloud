# Credential Management Guide

## Overview

The Cloud Automation Tool supports multiple methods for managing cloud provider credentials:

1. **Persistent Encrypted Storage** (Recommended for single-user workstations)
2. **Session-Only Storage** (Recommended for shared machines)
3. **Environment Variables** (Traditional method)

## Method 1: Persistent Encrypted Storage

### How It Works

- Credentials are encrypted using machine-specific keys (derived from username + hostname)
- Stored in `~/.cloud-automation/credentials.enc` with 0600 permissions
- Automatically loaded when the app starts
- Only works on the machine where they were saved

### Setup Instructions

1. Start the app: `streamlit run app.py`
2. Navigate to **Settings** page (sidebar)
3. Enter your AWS and/or GCP credentials
4. Check **"Remember credentials"** in the sidebar
5. Click **"Save AWS Credentials"** or **"Save GCP Credentials"**
6. Close and restart the app - credentials will be loaded automatically!

### Security Notes

- ✅ Credentials are encrypted (Fernet symmetric encryption)
- ✅ Machine-specific (won't work if you copy to another machine)
- ✅ File permissions: 0600 (only you can read/write)
- ✅ Optional: Disable anytime by unchecking "Remember credentials"

## Method 2: Session-Only Storage

### How It Works

- Credentials stored only in browser session memory
- Lost when you close/refresh the browser
- No files written to disk

### Setup Instructions

1. Start the app: `streamlit run app.py`
2. Navigate to **Settings** page
3. Enter your credentials
4. **Leave "Remember credentials" UNCHECKED**
5. Click **"Save AWS Credentials"** or **"Save GCP Credentials"**
6. Credentials available until you close the browser

### Use When

- Working on shared/public machines
- Testing with temporary credentials
- Maximum security (no disk storage)

## Method 3: Environment Variables

### AWS

```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

Or use AWS CLI:
```bash
aws configure
```

### GCP

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

Or use gcloud CLI:
```bash
gcloud auth application-default login
gcloud config set project your-project-id
```

## Priority Order

The application uses credentials in this order:

1. **UI Credentials** (from Settings page) - Highest priority
2. **Environment Variables** - Fallback
3. **AWS CLI / gcloud CLI** - Default fallback

## Managing Credentials

### Clear All Credentials

1. Go to **Settings** page
2. Click **"Clear All Credentials"** button (sidebar)
3. Clears both session memory and disk storage

### View Status

The Settings page sidebar shows:
- ✅ AWS Configured / ⚠️ AWS Not Configured
- ✅ GCP Configured / ⚠️ GCP Not Configured
- 📁 Credentials stored on disk / 📁 No stored credentials

### Test Credentials

1. Enter credentials in Settings
2. Click **"Test Connection"** button
3. Verifies credentials work with cloud provider APIs

## File Locations

| File | Purpose | Permissions |
|------|---------|-------------|
| `~/.cloud-automation/credentials.enc` | Encrypted credentials | 0600 (rw-------) |
| `~/.cloud-automation/` | Config directory | 0755 (rwxr-xr-x) |

## Troubleshooting

### "Failed to load credentials" Error

**Cause**: Encryption key changed (different user/hostname)

**Solution**:
- Clear stored credentials and re-enter
- Or delete `~/.cloud-automation/credentials.enc`

### Credentials Not Loading

**Check**:
1. Is "Remember credentials" enabled?
2. Does `~/.cloud-automation/credentials.enc` exist?
3. Try clearing and re-saving credentials

### Permission Denied

**Check**:
```bash
ls -la ~/.cloud-automation/credentials.enc
```

**Fix**:
```bash
chmod 600 ~/.cloud-automation/credentials.enc
```

## Security Best Practices

1. ✅ **Rotate credentials regularly** (every 90 days)
2. ✅ **Use IAM roles with minimal permissions**
3. ✅ **Never commit credentials to version control**
4. ✅ **Use separate credentials for dev/prod**
5. ✅ **Enable MFA on cloud accounts**
6. ✅ **Review cloud provider access logs**
7. ✅ **Clear credentials on shared machines**

## Example Workflow

### First-Time Setup

```bash
# 1. Start the app
cd /home/tpolson/cloud
source .venv/bin/activate
streamlit run app.py

# 2. Open browser to http://localhost:8501
# 3. Navigate to Settings
# 4. Enter AWS credentials
# 5. Enable "Remember credentials"
# 6. Click "Save AWS Credentials"
# 7. Close browser

# Next time - credentials automatically loaded!
streamlit run app.py
```

### Switching Between Environments

```bash
# Development
streamlit run app.py
# Use dev credentials in Settings

# Production
export AWS_PROFILE=production
streamlit run app.py
# App uses production environment variables
```

## Additional Resources

- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [GCP Service Account Keys](https://cloud.google.com/iam/docs/creating-managing-service-account-keys)
- [Python Cryptography Library](https://cryptography.io/)

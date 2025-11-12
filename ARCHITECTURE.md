```markdown
# Architecture Guide

## System Overview

The Cloud Automation Tool is a Python-based multi-cloud provisioning system with a modern Streamlit web interface. It provides unified resource management for AWS and GCP with strong security controls.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  PRESENTATION LAYER                      │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Streamlit Web Interface (app.py)          │  │
│  │  ┌────────┬────────┬──────────┬────────────────┐ │  │
│  │  │ Home   │ VM Mgt │ Settings │ Image/Instance │ │  │
│  │  │ (Prov) │        │          │ Browsers       │ │  │
│  │  └────────┴────────┴──────────┴────────────────┘ │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                   BUSINESS LOGIC LAYER                   │
│  ┌───────────────┬────────────────┬──────────────────┐  │
│  │ AWS Module    │  GCP Module    │  Core Services   │  │
│  │               │                │                  │  │
│  │ ┌───────────┐ │ ┌────────────┐ │ ┌──────────────┐│  │
│  │ │ vm.py     │ │ │ vm.py      │ │ │ Validators   ││  │
│  │ │ storage.py│ │ │ storage.py │ │ │ Quota Mgmt   ││  │
│  │ └───────────┘ │ └────────────┘ │ │ Cred Store   ││  │
│  │               │                │ │ Exceptions   ││  │
│  └───────────────┴────────────────┴─┴──────────────┴┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                   INTEGRATION LAYER                      │
│  ┌──────────────────┬──────────────────┬─────────────┐  │
│  │ AWS SDK (boto3)  │ GCP SDK          │ Local FS    │  │
│  │                  │ (google-cloud-*) │             │  │
│  └──────────────────┴──────────────────┴─────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                   INFRASTRUCTURE                         │
│  ┌──────────────────┬──────────────────┬─────────────┐  │
│  │  AWS Resources   │  GCP Resources   │  File System │  │
│  │  (EC2, S3, EBS)  │  (GCE, GCS, PD)  │  (~/.cloud) │  │
│  └──────────────────┴──────────────────┴─────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Presentation Layer (Streamlit UI)

#### Main Application (`app.py`)
- **Purpose**: Resource provisioning interface
- **Features**: VM and storage provisioning forms for AWS/GCP
- **State Management**: Streamlit session state for UI state

#### Pages
- `1_VM_Management.py`: Instance control (start/stop/reboot), storage attachment
- `2_Settings.py`: Credential configuration with encryption
- `3_Image_Browser.py`: AMI/image search and selection
- `4_Instance_Type_Browser.py`: Instance/machine type filtering by specs

#### Helpers
- `streamlit_helpers.py`: Credential retrieval, session state management

### 2. Business Logic Layer

#### Provider Modules

**AWS Module** (`cloud_automation/aws/`)
```
aws/
├── vm.py          # AWSVMProvisioner class
│   ├── create_instance()
│   ├── list_instances()
│   ├── start/stop/reboot/delete_instance()
│   ├── list_images(), search_images()
│   └── get_popular_images()
│
└── storage.py     # AWSStorageProvisioner class
    ├── create_s3_bucket()
    ├── create_ebs_volume()
    ├── attach/detach_volume()
    └── list_volumes()
```

**GCP Module** (`cloud_automation/gcp/`)
```
gcp/
├── vm.py          # GCPVMProvisioner class
│   ├── create_instance()
│   ├── list_instances()
│   ├── start/stop/reboot/delete_instance()
│   ├── list_images(), search_images()
│   └── get_popular_images()
│
└── storage.py     # GCPStorageProvisioner class
    ├── create_bucket()
    ├── create_disk()
    ├── attach/detach_disk()
    └── list_disks()
```

#### Core Services

**Credential Store** (`credential_store.py`)
```python
class CredentialStore:
    - PBKDF2-based encryption (600,000 iterations)
    - Cryptographic salt (32 bytes)
    - Machine-specific key derivation
    - Automatic legacy format migration
```

**Validators** (`validators.py`)
```python
class AWSValidator:
    - validate_ami_id(), validate_instance_id()
    - validate_instance_type(), validate_region()
    - validate_s3_bucket_name()

class GCPValidator:
    - validate_project_id(), validate_instance_name()
    - validate_machine_type(), validate_zone()
    - validate_bucket_name()

class CommonValidator:
    - validate_disk_size()
    - validate_tags_labels()
    - sanitize_name()
```

**Quota Manager** (`quota.py`)
```python
class QuotaManager:
    - Daily instance creation limits
    - Daily storage provisioning limits
    - Single disk size limits
    - Expensive instance warnings
    - Usage tracking and reset
```

**Instance Specifications** (`instance_specs.py`)
```python
- AWS_INSTANCE_TYPES: 50+ instance types with specs
- GCP_MACHINE_TYPES: 70+ machine types with specs
- filter_aws_instances(), filter_gcp_machines()
- Specifications: vCPU, memory, network, category
```

**Exceptions** (`exceptions.py`)
```python
- CloudAutomationError (base)
- CredentialError, ValidationError
- ProvisioningError, QuotaError
- ConnectionError, APIError
```

### 3. Integration Layer

#### AWS SDK Integration (boto3)
- **EC2 Client**: Instance management
- **S3 Client**: Bucket operations
- **Resource Interface**: Volume operations

#### GCP SDK Integration (google-cloud-*)
- **compute_v1**: Instance and disk management
- **storage**: Bucket operations
- **Credentials**: Service account authentication

#### File System Integration
- **Configuration**: `~/.cloud-automation/`
- **Credentials**: `credentials.enc` (encrypted)
- **Salt**: `salt` (32 bytes)
- **Quota**: `quota.json` (usage tracking)

## Data Flow

### Instance Provisioning Flow

```
User Input (Streamlit Form)
    ↓
Validation (validators.py)
    ↓
Quota Check (quota.py)
    ↓
Credential Retrieval (streamlit_helpers.py)
    ↓
Provisioner Call (aws/vm.py or gcp/vm.py)
    ↓
Cloud Provider API (boto3 or google-cloud)
    ↓
Resource Creation
    ↓
Quota Update (quota.py)
    ↓
Success Message (Streamlit UI)
```

### Credential Flow

```
User Input (Settings Page)
    ↓
Optional: Test Connection
    ↓
Encryption (PBKDF2 + Fernet)
    ↓
File Write (credentials.enc, 0600 permissions)
    ↓
Session State Update
    ↓
Auto-load on Next Start
```

## Security Architecture

### Defense in Depth

```
┌─────────────────────────────────────────┐
│  Layer 1: Input Validation              │
│  - Format validation (AMI IDs, etc.)    │
│  - Type checking (instance types)       │
│  - Sanitization (names, tags)           │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│  Layer 2: Quota Controls                │
│  - Daily limits                         │
│  - Cost warnings                        │
│  - Size restrictions                    │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│  Layer 3: Credential Encryption         │
│  - PBKDF2 key derivation                │
│  - Fernet encryption                    │
│  - File permissions (0600)              │
└────────────┬────────────────────────────┘
             │
┌────────────▼────────────────────────────┐
│  Layer 4: Cloud Provider Security       │
│  - IAM policies                         │
│  - Network security groups              │
│  - Audit logging                        │
└─────────────────────────────────────────┘
```

### Encryption Key Derivation

```
Username + Hostname
    ↓
Machine-specific Key Material
    ↓
Cryptographic Salt (32 bytes)
    ↓
PBKDF2-HMAC-SHA256 (600,000 iterations)
    ↓
256-bit Encryption Key
    ↓
Fernet Cipher (AES-128-CBC + HMAC-SHA256)
```

## Scalability Considerations

### Current Limitations

- **Single User**: Designed for individual use, not multi-tenant
- **Local State**: Session state and quotas stored locally
- **No Concurrency**: Sequential resource provisioning
- **No Job Queue**: Immediate execution only

### Future Scalability

For production/multi-user scenarios:
- **Database Backend**: PostgreSQL/MySQL for state and quotas
- **Job Queue**: Celery/RQ for async provisioning
- **API Layer**: REST API separate from Streamlit
- **Auth System**: OAuth/SAML for multi-user
- **Caching**: Redis for session and metadata

## Testing Architecture

### Test Coverage

```
tests/
├── test_credential_store.py    # Encryption, storage, migration
├── test_validators.py          # AWS/GCP/common validators
├── test_quota.py               # Quota management, cost controls
├── test_config.py              # Configuration management
└── test_utils.py               # Utility functions
```

### Testing Strategy

- **Unit Tests**: Individual component testing (validators, quota, etc.)
- **Integration Tests**: AWS/GCP SDK mocking (moto, google-cloud-testutils)
- **UI Tests**: Streamlit testing framework (future)
- **Security Tests**: Input validation bypass attempts, encryption strength

### Test Execution

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=cloud_automation --cov-report=html

# Run specific test suite
pytest tests/test_validators.py -v
```

## Deployment Architecture

### Local Development

```
Developer Machine
├── .venv/ (virtual environment)
├── ~/.cloud-automation/ (config/credentials)
└── streamlit run app.py (port 8501)
```

### Production Deployment

**Option 1: Single Server**
```
Linux Server (EC2/GCE instance with IAM role)
├── Nginx (reverse proxy, HTTPS)
├── Streamlit App (systemd service)
└── Virtual Environment
```

**Option 2: Docker Container**
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "app.py"]
```

**Option 3: Cloud Run / App Engine**
- Containerized deployment
- Auto-scaling
- Integrated with cloud IAM

## Performance Optimization

### Current Optimizations

- **Caching**: Streamlit `@st.cache_data` for image lists
- **Batch Operations**: Multiple instances in single API call
- **Lazy Loading**: Credentials loaded on demand
- **Efficient Queries**: Filtered API requests

### Future Optimizations

- **Connection Pooling**: Reuse boto3/GCP client connections
- **Async Operations**: asyncio for parallel provisioning
- **Result Caching**: Redis/Memcached for API responses
- **Pagination**: Large result set handling

## Monitoring and Observability

### Current Logging

- **Console Output**: `print_info()`, `print_error()`, `print_success()`
- **Exception Logging**: Stack traces in Streamlit UI

### Recommended Monitoring

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cloud_automation.log'),
        logging.StreamHandler()
    ]
)
```

### Metrics to Track

- **Usage**: Instances created, storage provisioned
- **Performance**: API response times, quota hit rate
- **Errors**: Provisioning failures, validation errors
- **Security**: Failed authentication attempts, quota violations

## Extension Points

### Adding New Cloud Providers

1. Create provider module: `cloud_automation/azure/`
2. Implement provisioner classes: `vm.py`, `storage.py`
3. Add validators: Update `validators.py`
4. Add instance specs: Update `instance_specs.py`
5. Create Streamlit pages: `pages/Azure_*.py`

### Adding New Resource Types

1. Extend provisioner classes with new methods
2. Add validation rules
3. Update quota system for new resource types
4. Create UI forms in Streamlit

### Custom Integrations

- **Terraform**: Generate .tf files from configurations
- **Ansible**: Export playbooks for provisioning
- **CloudFormation/Deployment Manager**: Export templates

## Dependencies

### Core Dependencies

```
streamlit>=1.28.0          # Web UI framework
boto3>=1.28.0              # AWS SDK
google-cloud-compute>=1.14.0   # GCP Compute SDK
google-cloud-storage>=2.10.0   # GCP Storage SDK
cryptography>=41.0.0       # Encryption (PBKDF2, Fernet)
```

### Development Dependencies

```
pytest>=7.4.0              # Testing framework
pytest-cov>=4.1.0          # Coverage reporting
black>=23.7.0              # Code formatting
flake8>=6.1.0              # Linting
mypy>=1.5.0                # Type checking
```

### Optional Dependencies

```
moto>=4.2.0                # AWS mocking for tests
```

## Troubleshooting Guide

### Common Issues

**1. Credential Decryption Failed**
- Cause: Different machine or user
- Solution: Re-enter credentials in Settings

**2. Quota Exceeded**
- Cause: Daily limit reached
- Solution: Wait for reset or increase limits via `QuotaManager`

**3. Invalid AMI ID**
- Cause: Incorrect format or non-existent AMI
- Solution: Use Image Browser to find valid AMIs

**4. GCP Authentication Error**
- Cause: Invalid service account key
- Solution: Download new key from GCP Console

## Change Log

### Version 0.6.0 (Current Development)
- ✅ PBKDF2 encryption with cryptographic salt
- ✅ Comprehensive input validation framework
- ✅ Resource quota and cost control system
- ✅ Custom exception hierarchy
- ✅ Expanded test suite (credential store, validators, quota)
- ✅ Security documentation (SECURITY.md)
- ✅ Architecture documentation (this file)

### Version 0.5.0
- Instance Type Browser with filtering by vCPU/RAM

### Version 0.4.0
- Image Browser for AMI/image search

### Version 0.3.0
- Encrypted credential storage

### Version 0.2.0
- VM Management interface

### Version 0.1.0
- Initial release

---

**Last Updated**: 2025-11-11
```

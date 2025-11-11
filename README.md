# Cloud Automation Tool

Automated VM and storage provisioning for AWS and Google Cloud Platform with a modern web interface.

## Features

### 🚀 Resource Provisioning
- **Virtual Machines**: Create EC2 instances (AWS) and Compute Engine VMs (GCP)
- **Storage**: Provision S3 buckets, EBS volumes (AWS), Cloud Storage buckets, and Persistent Disks (GCP)
- **Configuration-driven**: YAML-based configuration for infrastructure as code

### 🖥️ VM Management (NEW)
- **Real-time monitoring**: View all VMs with status, IPs, and resource details
- **Instance control**: Start, stop, reboot VMs from web UI or CLI
- **Storage attachment**: Attach/detach EBS volumes and Persistent Disks to running instances
- **SSH access**: Quick-connect SSH commands for terminal access

### 🎨 Modern Web Interface
- **Streamlit-based UI**: Clean, responsive interface for all operations
- **Multi-page design**: Separate pages for provisioning and VM management
- **Real-time updates**: Refresh to see current resource states
- **History tracking**: View recent provisioning operations

### 🔧 Powerful CLI
- **Comprehensive commands**: Full control via command-line interface
- **Batch operations**: Provision multiple resources from config files
- **Cross-platform**: Works on Linux, macOS, and Windows

## Installation

### Prerequisites
- Python 3.8 or higher
- AWS CLI configured (for AWS operations)
- Google Cloud SDK configured (for GCP operations)

### Install from Source

```bash
# Clone repository
git clone <repository-url>
cd cloud

# Create virtual environment (recommended)
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Linux/macOS
# OR
.venv\Scripts\activate     # On Windows

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Install package in editable mode
pip install -e .
```

**Note**: Always activate the virtual environment before working with the project:
```bash
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
```

To deactivate when done:
```bash
deactivate
```

## Quick Start

### Web Interface

Launch the Streamlit web interface:

```bash
streamlit run app.py
```

Navigate to http://localhost:8501 in your browser.

**Pages:**
- **Home**: Provision new VMs and storage resources
- **VM Management**: Control existing VMs, attach storage, SSH access

### Command Line Interface

```bash
# Get help
cloud-provision --help

# AWS commands
cloud-provision aws --help

# GCP commands
cloud-provision gcp --help
```

## Usage Examples

### Provisioning Resources

#### AWS EC2 Instance (Web UI)
1. Select "AWS" provider
2. Choose region (e.g., us-east-1)
3. Select "Virtual Machine (VM)"
4. Configure instance details
5. Click "🚀 Provision EC2 Instance"

#### AWS EC2 Instance (CLI)
```bash
cloud-provision aws vm create \
  --name my-server \
  --instance-type t2.micro \
  --region us-east-1 \
  --key-name my-key-pair
```

#### GCP Compute Engine Instance (CLI)
```bash
cloud-provision gcp vm create \
  --name my-server \
  --machine-type e2-micro \
  --project-id my-project \
  --zone us-central1-a
```

### VM Management

#### List Instances
```bash
# AWS
cloud-provision aws vm list --region us-east-1

# GCP
cloud-provision gcp vm list --project-id my-project --zone us-central1-a
```

#### Control VMs
```bash
# Stop an instance
cloud-provision aws vm stop --instance-id i-1234567890abcdef0 --region us-east-1

# Start an instance
cloud-provision aws vm start --instance-id i-1234567890abcdef0 --region us-east-1

# Reboot an instance
cloud-provision aws vm reboot --instance-id i-1234567890abcdef0 --region us-east-1
```

#### Attach Storage
```bash
# AWS: Attach EBS volume
cloud-provision aws storage attach \
  --volume-id vol-1234567890abcdef0 \
  --instance-id i-1234567890abcdef0 \
  --device /dev/sdf \
  --region us-east-1

# GCP: Attach Persistent Disk
cloud-provision gcp storage attach-disk \
  --disk-name my-disk \
  --instance-name my-instance \
  --project-id my-project \
  --zone us-central1-a
```

### Configuration-Based Provisioning

Create a `config.yaml` file:

```yaml
aws:
  region: us-east-1
  vms:
    - name: web-server-1
      instance_type: t2.micro
      key_name: my-key
      tags:
        Environment: production
        Application: web
  storage:
    s3_buckets:
      - bucket_name: my-app-data-bucket
        versioning: true
        encryption: true
    ebs_volumes:
      - name: data-volume
        size: 100
        volume_type: gp3
```

Provision all resources:

```bash
cloud-provision aws provision --config config.yaml --region us-east-1
```

## Documentation

- [VM Management Guide](docs/VM_MANAGEMENT.md) - Comprehensive VM control and storage attachment guide
- [CLAUDE.md](CLAUDE.md) - Development guidance for Claude Code

## Architecture

```
cloud_automation/
├── aws/
│   ├── vm.py           # EC2 instance management
│   └── storage.py      # S3 and EBS operations
├── gcp/
│   ├── vm.py           # Compute Engine management
│   └── storage.py      # Cloud Storage and Persistent Disks
├── config.py           # Configuration management
├── utils.py            # Shared utilities
└── cli.py              # Command-line interface

app.py                  # Main Streamlit UI (provisioning)
pages/
└── 1_VM_Management.py  # VM management interface
```

## Cloud Provider Setup

### AWS Configuration

Ensure AWS credentials are configured:

```bash
# Configure AWS CLI
aws configure

# Or set environment variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

Required IAM permissions:
- EC2: `ec2:*` (or specific permissions for instances, volumes)
- S3: `s3:*` (or specific permissions for buckets)

### GCP Configuration

Ensure Google Cloud SDK is configured:

```bash
# Initialize gcloud
gcloud init

# Set project
gcloud config set project YOUR_PROJECT_ID

# Authenticate
gcloud auth application-default login
```

Required IAM roles:
- Compute Admin (`roles/compute.admin`)
- Storage Admin (`roles/storage.admin`)

## Development

### Project Structure
- `cloud_automation/` - Core automation modules
- `tests/` - Test suite
- `configs/` - Configuration templates
- `app.py` - Streamlit web interface
- `pages/` - Streamlit multi-page components
- `docs/` - Documentation

### Running Tests
```bash
pytest
pytest -v  # Verbose output
pytest tests/test_config.py  # Specific test file
```

### Code Quality
```bash
# Format code
black cloud_automation/ tests/

# Lint code
flake8 cloud_automation/ tests/

# Type checking
mypy cloud_automation/
```

## Troubleshooting

### Common Issues

**AWS Credential Errors**
- Verify AWS CLI configuration: `aws sts get-caller-identity`
- Check IAM permissions for your user/role

**GCP Authentication Errors**
- Run `gcloud auth application-default login`
- Verify project ID: `gcloud config get-value project`

**Storage Attachment Fails**
- AWS: Ensure volume and instance are in same Availability Zone
- GCP: Ensure disk and instance are in same zone
- Check that volume/disk is in "available" state

**SSH Connection Issues**
- Verify security group (AWS) or firewall rules (GCP) allow port 22
- Ensure instance has public IP address
- Use correct SSH key and username

## Features Roadmap

- [ ] Bulk VM operations (start/stop multiple instances)
- [ ] Scheduled automation (start/stop on schedule)
- [ ] Cost analysis and optimization
- [ ] Snapshot management
- [ ] Load balancer integration
- [ ] Auto-scaling configuration
- [ ] Azure support

## Contributing

Contributions are welcome! Please follow these guidelines:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and code quality checks
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation in `docs/`
- Review troubleshooting guide above

## Changelog

### v0.2.0 (Current)
- ✨ Added VM management interface with start/stop/reboot
- ✨ Implemented storage attachment (EBS and Persistent Disks)
- ✨ Added SSH connection commands in UI
- ✨ Multi-page Streamlit interface
- 🐛 Various bug fixes and improvements

### v0.1.0
- 🎉 Initial release
- ✅ Basic VM and storage provisioning
- ✅ CLI interface
- ✅ Web UI for provisioning

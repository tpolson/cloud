# VM Management Features

This document describes the new VM management and storage attachment features added to the cloud automation tool.

## Overview

The cloud automation tool now includes comprehensive VM management capabilities through both a web UI and CLI:

- **List and view** all VMs with status and connection details
- **Control VMs**: Start, stop, reboot instances
- **Attach storage**: Connect EBS volumes (AWS) or Persistent Disks (GCP) to running instances
- **SSH access**: Quick SSH connection commands for remote access

## Web UI Features

### Accessing VM Management

1. Launch the Streamlit app: `streamlit run app.py`
2. Navigate to **VM Management** in the sidebar
3. Select your cloud provider (AWS or GCP)
4. Configure region/zone and credentials

### VM Management Interface

The VM Management page displays all instances with:

- **Status indicator** (🟢 Running, 🔴 Stopped, 🟡 Transitioning)
- **Instance details** (name, type, IPs, state)
- **Control buttons**:
  - ▶️ **Start**: Boot a stopped instance
  - ⏸️ **Stop**: Gracefully shut down a running instance
  - 🔄 **Reboot**: Restart a running instance
  - 🗑️ **Terminate/Delete**: Permanently remove instance (requires confirmation)
- **Storage management**:
  - View available volumes/disks
  - Attach storage to instances
  - Specify device name (AWS) or automatic attachment (GCP)
- **SSH access**:
  - Pre-formatted SSH commands for quick connection
  - Platform-specific instructions (ec2-user for AWS, gcloud for GCP)

## CLI Commands

### AWS EC2 Commands

#### Instance Control

```bash
# List instances
cloud-provision aws vm list --region us-east-1

# Start an instance
cloud-provision aws vm start --instance-id i-1234567890abcdef0 --region us-east-1

# Stop an instance
cloud-provision aws vm stop --instance-id i-1234567890abcdef0 --region us-east-1

# Reboot an instance
cloud-provision aws vm reboot --instance-id i-1234567890abcdef0 --region us-east-1

# Terminate an instance
cloud-provision aws vm delete --instance-id i-1234567890abcdef0 --region us-east-1
```

#### Storage Attachment

```bash
# List available volumes
cloud-provision aws storage list-volumes --region us-east-1

# Attach EBS volume to instance
cloud-provision aws storage attach \
  --volume-id vol-1234567890abcdef0 \
  --instance-id i-1234567890abcdef0 \
  --device /dev/sdf \
  --region us-east-1

# Detach EBS volume
cloud-provision aws storage detach \
  --volume-id vol-1234567890abcdef0 \
  --region us-east-1

# Force detach (if stuck)
cloud-provision aws storage detach \
  --volume-id vol-1234567890abcdef0 \
  --force \
  --region us-east-1
```

### GCP Compute Engine Commands

#### Instance Control

```bash
# List instances
cloud-provision gcp vm list --project-id my-project --zone us-central1-a

# Start an instance
cloud-provision gcp vm start \
  --name my-instance \
  --project-id my-project \
  --zone us-central1-a

# Stop an instance
cloud-provision gcp vm stop \
  --name my-instance \
  --project-id my-project \
  --zone us-central1-a

# Reboot an instance
cloud-provision gcp vm reboot \
  --name my-instance \
  --project-id my-project \
  --zone us-central1-a

# Delete an instance
cloud-provision gcp vm delete \
  --name my-instance \
  --project-id my-project \
  --zone us-central1-a
```

#### Storage Attachment

```bash
# List available disks
cloud-provision gcp storage list-disks --project-id my-project --zone us-central1-a

# Attach Persistent Disk to instance
cloud-provision gcp storage attach-disk \
  --disk-name my-disk \
  --instance-name my-instance \
  --project-id my-project \
  --zone us-central1-a

# Detach Persistent Disk
cloud-provision gcp storage detach-disk \
  --disk-name my-disk \
  --instance-name my-instance \
  --project-id my-project \
  --zone us-central1-a
```

## SSH Connection

### AWS EC2

After attaching an SSH key pair during instance creation, connect using:

```bash
# Direct SSH (requires key file)
ssh -i /path/to/key.pem ec2-user@<public-ip>

# Using Session Manager (no key required)
aws ssm start-session --target <instance-id>
```

**Default users by OS:**
- Amazon Linux 2: `ec2-user`
- Ubuntu: `ubuntu`
- CentOS: `centos`
- Debian: `admin`

### GCP Compute Engine

GCP uses project-wide SSH keys managed through metadata:

```bash
# Using gcloud CLI (recommended)
gcloud compute ssh <instance-name> \
  --zone=<zone> \
  --project=<project-id>

# Direct SSH (if keys configured)
ssh <username>@<external-ip>
```

The UI provides pre-formatted commands for easy copy-paste access.

## Implementation Details

### Backend Methods

#### AWS (`cloud_automation/aws/vm.py`)
- `start_instance(instance_id)` - AWS EC2:236
- `stop_instance(instance_id)` - AWS EC2:221
- `reboot_instance(instance_id)` - AWS EC2:236 (NEW)
- `terminate_instance(instance_id)` - AWS EC2:251

#### AWS Storage (`cloud_automation/aws/storage.py`)
- `attach_volume(volume_id, instance_id, device)` - AWS Storage:347
- `detach_volume(volume_id, force)` - AWS Storage:368

#### GCP (`cloud_automation/gcp/vm.py`)
- `start_instance(instance_name)` - GCP VM:253
- `stop_instance(instance_name)` - GCP VM:233
- `reboot_instance(instance_name)` - GCP VM:273 (NEW)
- `delete_instance(instance_name)` - GCP VM:293

#### GCP Storage (`cloud_automation/gcp/storage.py`)
- `attach_disk(instance_name, disk_name)` - GCP Storage:307
- `detach_disk(instance_name, disk_name)` - GCP Storage:336

### UI Implementation

The VM Management interface is implemented as a Streamlit multi-page app:
- Main provisioning page: `app.py`
- VM management page: `pages/1_VM_Management.py`

## Best Practices

### Storage Attachment

1. **AWS EBS Volumes:**
   - Volumes must be in the same Availability Zone as the instance
   - Use `/dev/sd[f-p]` for device names (kernel may rename to `/dev/xvd*`)
   - Detach gracefully when possible (avoid `--force` unless necessary)

2. **GCP Persistent Disks:**
   - Disks must be in the same zone as the instance
   - Can attach up to 128 disks per instance
   - Device names are auto-assigned but can be specified

### SSH Security

1. Use SSH keys instead of passwords
2. Restrict security group/firewall rules to specific IP ranges
3. Consider using bastion hosts for production environments
4. Enable OS-level auditing and logging

### VM Lifecycle Management

1. Stop instances instead of terminating to preserve data
2. Take snapshots before major changes
3. Tag resources appropriately for cost tracking
4. Use automation for scheduled start/stop to reduce costs

## Troubleshooting

### Storage Attachment Issues

**AWS:**
- **Volume in use**: Ensure volume is in "available" state
- **Wrong AZ**: Volume and instance must be in same availability zone
- **Device already exists**: Choose a different device name

**GCP:**
- **Disk already attached**: Detach from current instance first
- **Quota exceeded**: Check project quota limits
- **Zone mismatch**: Disk and instance must be in same zone

### SSH Connection Problems

**AWS:**
- Verify security group allows port 22 from your IP
- Ensure instance has public IP or use Session Manager
- Check correct SSH key is being used
- Verify correct username for the OS

**GCP:**
- Ensure firewall allows SSH (port 22)
- Check that instance has external IP
- Verify SSH keys in project metadata
- Use `gcloud compute ssh` for automatic key management

## Future Enhancements

Potential improvements for future versions:
- Bulk operations (start/stop multiple VMs)
- Scheduled start/stop automation
- Cost analysis and optimization suggestions
- SSH terminal directly in web UI
- Auto-scaling group management
- Snapshot management interface

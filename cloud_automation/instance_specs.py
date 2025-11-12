"""Instance type specifications for AWS and GCP."""

from typing import Dict, List, Any


# AWS EC2 Instance Types with specifications
AWS_INSTANCE_TYPES = {
    # T-Series (Burstable)
    't2.micro': {'vcpu': 1, 'memory_gb': 1, 'network': 'Low to Moderate', 'category': 'General Purpose', 'burstable': True},
    't2.small': {'vcpu': 1, 'memory_gb': 2, 'network': 'Low to Moderate', 'category': 'General Purpose', 'burstable': True},
    't2.medium': {'vcpu': 2, 'memory_gb': 4, 'network': 'Low to Moderate', 'category': 'General Purpose', 'burstable': True},
    't2.large': {'vcpu': 2, 'memory_gb': 8, 'network': 'Low to Moderate', 'category': 'General Purpose', 'burstable': True},
    't2.xlarge': {'vcpu': 4, 'memory_gb': 16, 'network': 'Moderate', 'category': 'General Purpose', 'burstable': True},
    't2.2xlarge': {'vcpu': 8, 'memory_gb': 32, 'network': 'Moderate', 'category': 'General Purpose', 'burstable': True},

    't3.micro': {'vcpu': 2, 'memory_gb': 1, 'network': 'Up to 5 Gbps', 'category': 'General Purpose', 'burstable': True},
    't3.small': {'vcpu': 2, 'memory_gb': 2, 'network': 'Up to 5 Gbps', 'category': 'General Purpose', 'burstable': True},
    't3.medium': {'vcpu': 2, 'memory_gb': 4, 'network': 'Up to 5 Gbps', 'category': 'General Purpose', 'burstable': True},
    't3.large': {'vcpu': 2, 'memory_gb': 8, 'network': 'Up to 5 Gbps', 'category': 'General Purpose', 'burstable': True},
    't3.xlarge': {'vcpu': 4, 'memory_gb': 16, 'network': 'Up to 5 Gbps', 'category': 'General Purpose', 'burstable': True},
    't3.2xlarge': {'vcpu': 8, 'memory_gb': 32, 'network': 'Up to 5 Gbps', 'category': 'General Purpose', 'burstable': True},

    # M-Series (General Purpose)
    'm5.large': {'vcpu': 2, 'memory_gb': 8, 'network': 'Up to 10 Gbps', 'category': 'General Purpose', 'burstable': False},
    'm5.xlarge': {'vcpu': 4, 'memory_gb': 16, 'network': 'Up to 10 Gbps', 'category': 'General Purpose', 'burstable': False},
    'm5.2xlarge': {'vcpu': 8, 'memory_gb': 32, 'network': 'Up to 10 Gbps', 'category': 'General Purpose', 'burstable': False},
    'm5.4xlarge': {'vcpu': 16, 'memory_gb': 64, 'network': '10 Gbps', 'category': 'General Purpose', 'burstable': False},
    'm5.8xlarge': {'vcpu': 32, 'memory_gb': 128, 'network': '10 Gbps', 'category': 'General Purpose', 'burstable': False},
    'm5.12xlarge': {'vcpu': 48, 'memory_gb': 192, 'network': '12 Gbps', 'category': 'General Purpose', 'burstable': False},
    'm5.16xlarge': {'vcpu': 64, 'memory_gb': 256, 'network': '20 Gbps', 'category': 'General Purpose', 'burstable': False},
    'm5.24xlarge': {'vcpu': 96, 'memory_gb': 384, 'network': '25 Gbps', 'category': 'General Purpose', 'burstable': False},

    'm6i.large': {'vcpu': 2, 'memory_gb': 8, 'network': 'Up to 12.5 Gbps', 'category': 'General Purpose', 'burstable': False},
    'm6i.xlarge': {'vcpu': 4, 'memory_gb': 16, 'network': 'Up to 12.5 Gbps', 'category': 'General Purpose', 'burstable': False},
    'm6i.2xlarge': {'vcpu': 8, 'memory_gb': 32, 'network': 'Up to 12.5 Gbps', 'category': 'General Purpose', 'burstable': False},
    'm6i.4xlarge': {'vcpu': 16, 'memory_gb': 64, 'network': '12.5 Gbps', 'category': 'General Purpose', 'burstable': False},
    'm6i.8xlarge': {'vcpu': 32, 'memory_gb': 128, 'network': '12.5 Gbps', 'category': 'General Purpose', 'burstable': False},

    # C-Series (Compute Optimized)
    'c5.large': {'vcpu': 2, 'memory_gb': 4, 'network': 'Up to 10 Gbps', 'category': 'Compute Optimized', 'burstable': False},
    'c5.xlarge': {'vcpu': 4, 'memory_gb': 8, 'network': 'Up to 10 Gbps', 'category': 'Compute Optimized', 'burstable': False},
    'c5.2xlarge': {'vcpu': 8, 'memory_gb': 16, 'network': 'Up to 10 Gbps', 'category': 'Compute Optimized', 'burstable': False},
    'c5.4xlarge': {'vcpu': 16, 'memory_gb': 32, 'network': '10 Gbps', 'category': 'Compute Optimized', 'burstable': False},
    'c5.9xlarge': {'vcpu': 36, 'memory_gb': 72, 'network': '10 Gbps', 'category': 'Compute Optimized', 'burstable': False},
    'c5.12xlarge': {'vcpu': 48, 'memory_gb': 96, 'network': '12 Gbps', 'category': 'Compute Optimized', 'burstable': False},
    'c5.18xlarge': {'vcpu': 72, 'memory_gb': 144, 'network': '25 Gbps', 'category': 'Compute Optimized', 'burstable': False},
    'c5.24xlarge': {'vcpu': 96, 'memory_gb': 192, 'network': '25 Gbps', 'category': 'Compute Optimized', 'burstable': False},

    # R-Series (Memory Optimized)
    'r5.large': {'vcpu': 2, 'memory_gb': 16, 'network': 'Up to 10 Gbps', 'category': 'Memory Optimized', 'burstable': False},
    'r5.xlarge': {'vcpu': 4, 'memory_gb': 32, 'network': 'Up to 10 Gbps', 'category': 'Memory Optimized', 'burstable': False},
    'r5.2xlarge': {'vcpu': 8, 'memory_gb': 64, 'network': 'Up to 10 Gbps', 'category': 'Memory Optimized', 'burstable': False},
    'r5.4xlarge': {'vcpu': 16, 'memory_gb': 128, 'network': '10 Gbps', 'category': 'Memory Optimized', 'burstable': False},
    'r5.8xlarge': {'vcpu': 32, 'memory_gb': 256, 'network': '10 Gbps', 'category': 'Memory Optimized', 'burstable': False},
    'r5.12xlarge': {'vcpu': 48, 'memory_gb': 384, 'network': '12 Gbps', 'category': 'Memory Optimized', 'burstable': False},
    'r5.16xlarge': {'vcpu': 64, 'memory_gb': 512, 'network': '20 Gbps', 'category': 'Memory Optimized', 'burstable': False},
    'r5.24xlarge': {'vcpu': 96, 'memory_gb': 768, 'network': '25 Gbps', 'category': 'Memory Optimized', 'burstable': False},
}

# GCP Machine Types with specifications
GCP_MACHINE_TYPES = {
    # E2 Series (Cost-Optimized)
    'e2-micro': {'vcpu': 2, 'memory_gb': 1, 'network': '1 Gbps', 'category': 'General Purpose', 'shared_cpu': True},
    'e2-small': {'vcpu': 2, 'memory_gb': 2, 'network': '1 Gbps', 'category': 'General Purpose', 'shared_cpu': True},
    'e2-medium': {'vcpu': 2, 'memory_gb': 4, 'network': '1 Gbps', 'category': 'General Purpose', 'shared_cpu': True},
    'e2-standard-2': {'vcpu': 2, 'memory_gb': 8, 'network': 'Up to 4 Gbps', 'category': 'General Purpose', 'shared_cpu': False},
    'e2-standard-4': {'vcpu': 4, 'memory_gb': 16, 'network': 'Up to 8 Gbps', 'category': 'General Purpose', 'shared_cpu': False},
    'e2-standard-8': {'vcpu': 8, 'memory_gb': 32, 'network': 'Up to 16 Gbps', 'category': 'General Purpose', 'shared_cpu': False},
    'e2-standard-16': {'vcpu': 16, 'memory_gb': 64, 'network': '16 Gbps', 'category': 'General Purpose', 'shared_cpu': False},
    'e2-standard-32': {'vcpu': 32, 'memory_gb': 128, 'network': '16 Gbps', 'category': 'General Purpose', 'shared_cpu': False},

    'e2-highmem-2': {'vcpu': 2, 'memory_gb': 16, 'network': 'Up to 4 Gbps', 'category': 'Memory Optimized', 'shared_cpu': False},
    'e2-highmem-4': {'vcpu': 4, 'memory_gb': 32, 'network': 'Up to 8 Gbps', 'category': 'Memory Optimized', 'shared_cpu': False},
    'e2-highmem-8': {'vcpu': 8, 'memory_gb': 64, 'network': 'Up to 16 Gbps', 'category': 'Memory Optimized', 'shared_cpu': False},
    'e2-highmem-16': {'vcpu': 16, 'memory_gb': 128, 'network': '16 Gbps', 'category': 'Memory Optimized', 'shared_cpu': False},

    'e2-highcpu-2': {'vcpu': 2, 'memory_gb': 2, 'network': 'Up to 4 Gbps', 'category': 'Compute Optimized', 'shared_cpu': False},
    'e2-highcpu-4': {'vcpu': 4, 'memory_gb': 4, 'network': 'Up to 8 Gbps', 'category': 'Compute Optimized', 'shared_cpu': False},
    'e2-highcpu-8': {'vcpu': 8, 'memory_gb': 8, 'network': 'Up to 16 Gbps', 'category': 'Compute Optimized', 'shared_cpu': False},
    'e2-highcpu-16': {'vcpu': 16, 'memory_gb': 16, 'network': '16 Gbps', 'category': 'Compute Optimized', 'shared_cpu': False},
    'e2-highcpu-32': {'vcpu': 32, 'memory_gb': 32, 'network': '16 Gbps', 'category': 'Compute Optimized', 'shared_cpu': False},

    # N1 Series (First Generation)
    'n1-standard-1': {'vcpu': 1, 'memory_gb': 3.75, 'network': '2 Gbps', 'category': 'General Purpose', 'shared_cpu': False},
    'n1-standard-2': {'vcpu': 2, 'memory_gb': 7.5, 'network': '10 Gbps', 'category': 'General Purpose', 'shared_cpu': False},
    'n1-standard-4': {'vcpu': 4, 'memory_gb': 15, 'network': '10 Gbps', 'category': 'General Purpose', 'shared_cpu': False},
    'n1-standard-8': {'vcpu': 8, 'memory_gb': 30, 'network': '16 Gbps', 'category': 'General Purpose', 'shared_cpu': False},
    'n1-standard-16': {'vcpu': 16, 'memory_gb': 60, 'network': '32 Gbps', 'category': 'General Purpose', 'shared_cpu': False},
    'n1-standard-32': {'vcpu': 32, 'memory_gb': 120, 'network': '32 Gbps', 'category': 'General Purpose', 'shared_cpu': False},
    'n1-standard-64': {'vcpu': 64, 'memory_gb': 240, 'network': '32 Gbps', 'category': 'General Purpose', 'shared_cpu': False},
    'n1-standard-96': {'vcpu': 96, 'memory_gb': 360, 'network': '32 Gbps', 'category': 'General Purpose', 'shared_cpu': False},

    'n1-highmem-2': {'vcpu': 2, 'memory_gb': 13, 'network': '10 Gbps', 'category': 'Memory Optimized', 'shared_cpu': False},
    'n1-highmem-4': {'vcpu': 4, 'memory_gb': 26, 'network': '10 Gbps', 'category': 'Memory Optimized', 'shared_cpu': False},
    'n1-highmem-8': {'vcpu': 8, 'memory_gb': 52, 'network': '16 Gbps', 'category': 'Memory Optimized', 'shared_cpu': False},
    'n1-highmem-16': {'vcpu': 16, 'memory_gb': 104, 'network': '32 Gbps', 'category': 'Memory Optimized', 'shared_cpu': False},
    'n1-highmem-32': {'vcpu': 32, 'memory_gb': 208, 'network': '32 Gbps', 'category': 'Memory Optimized', 'shared_cpu': False},
    'n1-highmem-64': {'vcpu': 64, 'memory_gb': 416, 'network': '32 Gbps', 'category': 'Memory Optimized', 'shared_cpu': False},
    'n1-highmem-96': {'vcpu': 96, 'memory_gb': 624, 'network': '32 Gbps', 'category': 'Memory Optimized', 'shared_cpu': False},

    'n1-highcpu-2': {'vcpu': 2, 'memory_gb': 1.8, 'network': '10 Gbps', 'category': 'Compute Optimized', 'shared_cpu': False},
    'n1-highcpu-4': {'vcpu': 4, 'memory_gb': 3.6, 'network': '10 Gbps', 'category': 'Compute Optimized', 'shared_cpu': False},
    'n1-highcpu-8': {'vcpu': 8, 'memory_gb': 7.2, 'network': '16 Gbps', 'category': 'Compute Optimized', 'shared_cpu': False},
    'n1-highcpu-16': {'vcpu': 16, 'memory_gb': 14.4, 'network': '32 Gbps', 'category': 'Compute Optimized', 'shared_cpu': False},
    'n1-highcpu-32': {'vcpu': 32, 'memory_gb': 28.8, 'network': '32 Gbps', 'category': 'Compute Optimized', 'shared_cpu': False},
    'n1-highcpu-64': {'vcpu': 64, 'memory_gb': 57.6, 'network': '32 Gbps', 'category': 'Compute Optimized', 'shared_cpu': False},
    'n1-highcpu-96': {'vcpu': 96, 'memory_gb': 86.4, 'network': '32 Gbps', 'category': 'Compute Optimized', 'shared_cpu': False},

    # N2 Series (Second Generation)
    'n2-standard-2': {'vcpu': 2, 'memory_gb': 8, 'network': 'Up to 10 Gbps', 'category': 'General Purpose', 'shared_cpu': False},
    'n2-standard-4': {'vcpu': 4, 'memory_gb': 16, 'network': 'Up to 10 Gbps', 'category': 'General Purpose', 'shared_cpu': False},
    'n2-standard-8': {'vcpu': 8, 'memory_gb': 32, 'network': 'Up to 16 Gbps', 'category': 'General Purpose', 'shared_cpu': False},
    'n2-standard-16': {'vcpu': 16, 'memory_gb': 64, 'network': '32 Gbps', 'category': 'General Purpose', 'shared_cpu': False},
    'n2-standard-32': {'vcpu': 32, 'memory_gb': 128, 'network': '32 Gbps', 'category': 'General Purpose', 'shared_cpu': False},
    'n2-standard-48': {'vcpu': 48, 'memory_gb': 192, 'network': '32 Gbps', 'category': 'General Purpose', 'shared_cpu': False},
    'n2-standard-64': {'vcpu': 64, 'memory_gb': 256, 'network': '32 Gbps', 'category': 'General Purpose', 'shared_cpu': False},
    'n2-standard-80': {'vcpu': 80, 'memory_gb': 320, 'network': '32 Gbps', 'category': 'General Purpose', 'shared_cpu': False},

    'n2-highmem-2': {'vcpu': 2, 'memory_gb': 16, 'network': 'Up to 10 Gbps', 'category': 'Memory Optimized', 'shared_cpu': False},
    'n2-highmem-4': {'vcpu': 4, 'memory_gb': 32, 'network': 'Up to 10 Gbps', 'category': 'Memory Optimized', 'shared_cpu': False},
    'n2-highmem-8': {'vcpu': 8, 'memory_gb': 64, 'network': 'Up to 16 Gbps', 'category': 'Memory Optimized', 'shared_cpu': False},
    'n2-highmem-16': {'vcpu': 16, 'memory_gb': 128, 'network': '32 Gbps', 'category': 'Memory Optimized', 'shared_cpu': False},
    'n2-highmem-32': {'vcpu': 32, 'memory_gb': 256, 'network': '32 Gbps', 'category': 'Memory Optimized', 'shared_cpu': False},
    'n2-highmem-48': {'vcpu': 48, 'memory_gb': 384, 'network': '32 Gbps', 'category': 'Memory Optimized', 'shared_cpu': False},
    'n2-highmem-64': {'vcpu': 64, 'memory_gb': 512, 'network': '32 Gbps', 'category': 'Memory Optimized', 'shared_cpu': False},
    'n2-highmem-80': {'vcpu': 80, 'memory_gb': 640, 'network': '32 Gbps', 'category': 'Memory Optimized', 'shared_cpu': False},

    'n2-highcpu-2': {'vcpu': 2, 'memory_gb': 2, 'network': 'Up to 10 Gbps', 'category': 'Compute Optimized', 'shared_cpu': False},
    'n2-highcpu-4': {'vcpu': 4, 'memory_gb': 4, 'network': 'Up to 10 Gbps', 'category': 'Compute Optimized', 'shared_cpu': False},
    'n2-highcpu-8': {'vcpu': 8, 'memory_gb': 8, 'network': 'Up to 16 Gbps', 'category': 'Compute Optimized', 'shared_cpu': False},
    'n2-highcpu-16': {'vcpu': 16, 'memory_gb': 16, 'network': '32 Gbps', 'category': 'Compute Optimized', 'shared_cpu': False},
    'n2-highcpu-32': {'vcpu': 32, 'memory_gb': 32, 'network': '32 Gbps', 'category': 'Compute Optimized', 'shared_cpu': False},
    'n2-highcpu-48': {'vcpu': 48, 'memory_gb': 48, 'network': '32 Gbps', 'category': 'Compute Optimized', 'shared_cpu': False},
    'n2-highcpu-64': {'vcpu': 64, 'memory_gb': 64, 'network': '32 Gbps', 'category': 'Compute Optimized', 'shared_cpu': False},
    'n2-highcpu-80': {'vcpu': 80, 'memory_gb': 80, 'network': '32 Gbps', 'category': 'Compute Optimized', 'shared_cpu': False},
}


def filter_aws_instances(
    min_vcpu: int = None,
    max_vcpu: int = None,
    min_memory_gb: float = None,
    max_memory_gb: float = None,
    category: str = None,
    burstable_only: bool = None
) -> List[Dict[str, Any]]:
    """Filter AWS instance types by specifications.

    Args:
        min_vcpu: Minimum number of vCPUs
        max_vcpu: Maximum number of vCPUs
        min_memory_gb: Minimum memory in GB
        max_memory_gb: Maximum memory in GB
        category: Instance category filter
        burstable_only: Filter for burstable instances only

    Returns:
        List of matching instance types with specifications
    """
    results = []

    for instance_type, specs in AWS_INSTANCE_TYPES.items():
        # Apply filters
        if min_vcpu is not None and specs['vcpu'] < min_vcpu:
            continue
        if max_vcpu is not None and specs['vcpu'] > max_vcpu:
            continue
        if min_memory_gb is not None and specs['memory_gb'] < min_memory_gb:
            continue
        if max_memory_gb is not None and specs['memory_gb'] > max_memory_gb:
            continue
        if category and specs['category'] != category:
            continue
        if burstable_only is not None and specs['burstable'] != burstable_only:
            continue

        results.append({
            'instance_type': instance_type,
            **specs
        })

    # Sort by vCPU, then memory
    results.sort(key=lambda x: (x['vcpu'], x['memory_gb']))

    return results


def filter_gcp_machines(
    min_vcpu: int = None,
    max_vcpu: int = None,
    min_memory_gb: float = None,
    max_memory_gb: float = None,
    category: str = None,
    exclude_shared_cpu: bool = False
) -> List[Dict[str, Any]]:
    """Filter GCP machine types by specifications.

    Args:
        min_vcpu: Minimum number of vCPUs
        max_vcpu: Maximum number of vCPUs
        min_memory_gb: Minimum memory in GB
        max_memory_gb: Maximum memory in GB
        category: Machine category filter
        exclude_shared_cpu: Exclude shared-CPU instances

    Returns:
        List of matching machine types with specifications
    """
    results = []

    for machine_type, specs in GCP_MACHINE_TYPES.items():
        # Apply filters
        if min_vcpu is not None and specs['vcpu'] < min_vcpu:
            continue
        if max_vcpu is not None and specs['vcpu'] > max_vcpu:
            continue
        if min_memory_gb is not None and specs['memory_gb'] < min_memory_gb:
            continue
        if max_memory_gb is not None and specs['memory_gb'] > max_memory_gb:
            continue
        if category and specs['category'] != category:
            continue
        if exclude_shared_cpu and specs['shared_cpu']:
            continue

        results.append({
            'machine_type': machine_type,
            **specs
        })

    # Sort by vCPU, then memory
    results.sort(key=lambda x: (x['vcpu'], x['memory_gb']))

    return results


def get_instance_categories() -> Dict[str, List[str]]:
    """Get all instance categories.

    Returns:
        Dictionary of provider to list of categories
    """
    return {
        'AWS': sorted(set(specs['category'] for specs in AWS_INSTANCE_TYPES.values())),
        'GCP': sorted(set(specs['category'] for specs in GCP_MACHINE_TYPES.values()))
    }


def get_instance_specs(provider: str, instance_type: str) -> Dict[str, Any]:
    """Get specifications for a specific instance type.

    Args:
        provider: 'AWS' or 'GCP'
        instance_type: Instance/machine type name

    Returns:
        Specifications dictionary or None if not found
    """
    if provider == 'AWS':
        return AWS_INSTANCE_TYPES.get(instance_type)
    elif provider == 'GCP':
        return GCP_MACHINE_TYPES.get(instance_type)
    return None

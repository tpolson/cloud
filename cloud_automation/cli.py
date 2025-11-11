"""Command-line interface for cloud automation."""

import sys
import click
from pathlib import Path
from tabulate import tabulate
from typing import Optional

from cloud_automation.config import ConfigManager
from cloud_automation.aws.vm import AWSVMProvisioner
from cloud_automation.aws.storage import AWSStorageProvisioner
from cloud_automation.gcp.vm import GCPVMProvisioner
from cloud_automation.gcp.storage import GCPStorageProvisioner
from cloud_automation.utils import (
    print_success,
    print_error,
    print_info,
    print_warning,
)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Cloud Automation - Automated VM and storage provisioning for AWS and GCP."""
    pass


# ==================== AWS Commands ====================

@cli.group()
def aws():
    """AWS provisioning commands."""
    pass


@aws.command()
@click.option('--config', type=click.Path(exists=True), help='Configuration file path')
@click.option('--region', default='us-east-1', help='AWS region')
def provision(config: Optional[str], region: str):
    """Provision all resources from config file."""
    try:
        if not config:
            print_error("Configuration file required. Use --config option")
            sys.exit(1)

        config_manager = ConfigManager(config)
        aws_config = config_manager.get_aws_config()

        region = aws_config.get('region', region)

        print_info(f"Provisioning AWS resources in {region}...")

        # Provision VMs
        if 'vms' in aws_config:
            vm_provisioner = AWSVMProvisioner(region=region)
            for vm_config in aws_config['vms']:
                vm_provisioner.create_instance(**vm_config)

        # Provision S3 buckets
        if 'storage' in aws_config and 's3_buckets' in aws_config['storage']:
            storage_provisioner = AWSStorageProvisioner(region=region)
            for bucket_config in aws_config['storage']['s3_buckets']:
                storage_provisioner.create_s3_bucket(**bucket_config)

        # Provision EBS volumes
        if 'storage' in aws_config and 'ebs_volumes' in aws_config['storage']:
            storage_provisioner = AWSStorageProvisioner(region=region)
            for volume_config in aws_config['storage']['ebs_volumes']:
                storage_provisioner.create_ebs_volume(**volume_config)

        print_success("AWS provisioning completed!")

    except Exception as e:
        print_error(f"Provisioning failed: {e}")
        sys.exit(1)


@aws.group()
def vm():
    """AWS EC2 instance commands."""
    pass


@vm.command('create')
@click.option('--name', required=True, help='Instance name')
@click.option('--instance-type', default='t2.micro', help='Instance type')
@click.option('--ami', help='AMI ID')
@click.option('--region', default='us-east-1', help='AWS region')
@click.option('--key-name', help='SSH key pair name')
def vm_create(name: str, instance_type: str, ami: Optional[str], region: str, key_name: Optional[str]):
    """Create an EC2 instance."""
    try:
        provisioner = AWSVMProvisioner(region=region)
        provisioner.create_instance(
            name=name,
            instance_type=instance_type,
            ami=ami,
            key_name=key_name
        )
    except Exception as e:
        print_error(f"Failed to create instance: {e}")
        sys.exit(1)


@vm.command('list')
@click.option('--region', default='us-east-1', help='AWS region')
def vm_list(region: str):
    """List EC2 instances."""
    try:
        provisioner = AWSVMProvisioner(region=region)
        instances = provisioner.list_instances()

        if not instances:
            print_info("No instances found")
            return

        table_data = [
            [i['instance_id'], i['name'], i['instance_type'], i['state'], i['public_ip'], i['private_ip']]
            for i in instances
        ]
        headers = ['Instance ID', 'Name', 'Type', 'State', 'Public IP', 'Private IP']

        print(tabulate(table_data, headers=headers, tablefmt='grid'))

    except Exception as e:
        print_error(f"Failed to list instances: {e}")
        sys.exit(1)


@vm.command('delete')
@click.option('--instance-id', required=True, help='Instance ID to delete')
@click.option('--region', default='us-east-1', help='AWS region')
@click.confirmation_option(prompt='Are you sure you want to delete this instance?')
def vm_delete(instance_id: str, region: str):
    """Delete an EC2 instance."""
    try:
        provisioner = AWSVMProvisioner(region=region)
        provisioner.terminate_instance(instance_id)
    except Exception as e:
        print_error(f"Failed to delete instance: {e}")
        sys.exit(1)


@aws.group()
def storage():
    """AWS storage commands."""
    pass


@storage.command('create-bucket')
@click.option('--name', required=True, help='Bucket name')
@click.option('--region', default='us-east-1', help='AWS region')
@click.option('--versioning/--no-versioning', default=False, help='Enable versioning')
def storage_create_bucket(name: str, region: str, versioning: bool):
    """Create an S3 bucket."""
    try:
        provisioner = AWSStorageProvisioner(region=region)
        provisioner.create_s3_bucket(bucket_name=name, versioning=versioning)
    except Exception as e:
        print_error(f"Failed to create bucket: {e}")
        sys.exit(1)


@storage.command('list-buckets')
@click.option('--region', default='us-east-1', help='AWS region')
def storage_list_buckets(region: str):
    """List S3 buckets."""
    try:
        provisioner = AWSStorageProvisioner(region=region)
        buckets = provisioner.list_s3_buckets()

        if not buckets:
            print_info("No buckets found")
            return

        table_data = [[b['name'], b['region'], b['creation_date']] for b in buckets]
        headers = ['Bucket Name', 'Region', 'Creation Date']

        print(tabulate(table_data, headers=headers, tablefmt='grid'))

    except Exception as e:
        print_error(f"Failed to list buckets: {e}")
        sys.exit(1)


@storage.command('create-volume')
@click.option('--name', required=True, help='Volume name')
@click.option('--size', type=int, required=True, help='Volume size in GB')
@click.option('--volume-type', default='gp3', help='Volume type')
@click.option('--region', default='us-east-1', help='AWS region')
def storage_create_volume(name: str, size: int, volume_type: str, region: str):
    """Create an EBS volume."""
    try:
        provisioner = AWSStorageProvisioner(region=region)
        provisioner.create_ebs_volume(name=name, size=size, volume_type=volume_type)
    except Exception as e:
        print_error(f"Failed to create volume: {e}")
        sys.exit(1)


# ==================== GCP Commands ====================

@cli.group()
def gcp():
    """GCP provisioning commands."""
    pass


@gcp.command()
@click.option('--config', type=click.Path(exists=True), help='Configuration file path')
@click.option('--project-id', required=True, help='GCP project ID')
@click.option('--zone', default='us-central1-a', help='GCP zone')
def provision(config: Optional[str], project_id: str, zone: str):
    """Provision all resources from config file."""
    try:
        if not config:
            print_error("Configuration file required. Use --config option")
            sys.exit(1)

        config_manager = ConfigManager(config)
        gcp_config = config_manager.get_gcp_config()

        project_id = gcp_config.get('project_id', project_id)
        zone = gcp_config.get('zone', zone)

        print_info(f"Provisioning GCP resources in project {project_id}, zone {zone}...")

        # Provision VMs
        if 'vms' in gcp_config:
            vm_provisioner = GCPVMProvisioner(project_id=project_id, zone=zone)
            for vm_config in gcp_config['vms']:
                vm_provisioner.create_instance(**vm_config)

        # Provision Cloud Storage buckets
        if 'storage' in gcp_config and 'buckets' in gcp_config['storage']:
            storage_provisioner = GCPStorageProvisioner(project_id=project_id, zone=zone)
            for bucket_config in gcp_config['storage']['buckets']:
                storage_provisioner.create_bucket(**bucket_config)

        # Provision Persistent Disks
        if 'storage' in gcp_config and 'disks' in gcp_config['storage']:
            storage_provisioner = GCPStorageProvisioner(project_id=project_id, zone=zone)
            for disk_config in gcp_config['storage']['disks']:
                storage_provisioner.create_disk(**disk_config)

        print_success("GCP provisioning completed!")

    except Exception as e:
        print_error(f"Provisioning failed: {e}")
        sys.exit(1)


@gcp.group()
def vm():
    """GCP Compute Engine instance commands."""
    pass


@vm.command('create')
@click.option('--name', required=True, help='Instance name')
@click.option('--machine-type', default='e2-micro', help='Machine type')
@click.option('--project-id', required=True, help='GCP project ID')
@click.option('--zone', default='us-central1-a', help='GCP zone')
def vm_create(name: str, machine_type: str, project_id: str, zone: str):
    """Create a GCE instance."""
    try:
        provisioner = GCPVMProvisioner(project_id=project_id, zone=zone)
        provisioner.create_instance(name=name, machine_type=machine_type)
    except Exception as e:
        print_error(f"Failed to create instance: {e}")
        sys.exit(1)


@vm.command('list')
@click.option('--project-id', required=True, help='GCP project ID')
@click.option('--zone', default='us-central1-a', help='GCP zone')
def vm_list(project_id: str, zone: str):
    """List GCE instances."""
    try:
        provisioner = GCPVMProvisioner(project_id=project_id, zone=zone)
        instances = provisioner.list_instances()

        if not instances:
            print_info("No instances found")
            return

        table_data = [
            [i['name'], i['machine_type'], i['status'], i['external_ip'], i['internal_ip']]
            for i in instances
        ]
        headers = ['Name', 'Machine Type', 'Status', 'External IP', 'Internal IP']

        print(tabulate(table_data, headers=headers, tablefmt='grid'))

    except Exception as e:
        print_error(f"Failed to list instances: {e}")
        sys.exit(1)


@vm.command('delete')
@click.option('--name', required=True, help='Instance name to delete')
@click.option('--project-id', required=True, help='GCP project ID')
@click.option('--zone', default='us-central1-a', help='GCP zone')
@click.confirmation_option(prompt='Are you sure you want to delete this instance?')
def vm_delete(name: str, project_id: str, zone: str):
    """Delete a GCE instance."""
    try:
        provisioner = GCPVMProvisioner(project_id=project_id, zone=zone)
        provisioner.delete_instance(name)
    except Exception as e:
        print_error(f"Failed to delete instance: {e}")
        sys.exit(1)


@gcp.group()
def storage():
    """GCP storage commands."""
    pass


@storage.command('create-bucket')
@click.option('--name', required=True, help='Bucket name')
@click.option('--project-id', required=True, help='GCP project ID')
@click.option('--location', default='US', help='Bucket location')
@click.option('--storage-class', default='STANDARD', help='Storage class')
def storage_create_bucket(name: str, project_id: str, location: str, storage_class: str):
    """Create a Cloud Storage bucket."""
    try:
        provisioner = GCPStorageProvisioner(project_id=project_id)
        provisioner.create_bucket(bucket_name=name, location=location, storage_class=storage_class)
    except Exception as e:
        print_error(f"Failed to create bucket: {e}")
        sys.exit(1)


@storage.command('list-buckets')
@click.option('--project-id', required=True, help='GCP project ID')
def storage_list_buckets(project_id: str):
    """List Cloud Storage buckets."""
    try:
        provisioner = GCPStorageProvisioner(project_id=project_id)
        buckets = provisioner.list_buckets()

        if not buckets:
            print_info("No buckets found")
            return

        table_data = [[b['name'], b['location'], b['storage_class'], b['time_created']] for b in buckets]
        headers = ['Bucket Name', 'Location', 'Storage Class', 'Created']

        print(tabulate(table_data, headers=headers, tablefmt='grid'))

    except Exception as e:
        print_error(f"Failed to list buckets: {e}")
        sys.exit(1)


@storage.command('create-disk')
@click.option('--name', required=True, help='Disk name')
@click.option('--size', type=int, required=True, help='Disk size in GB')
@click.option('--project-id', required=True, help='GCP project ID')
@click.option('--zone', default='us-central1-a', help='GCP zone')
@click.option('--disk-type', default='pd-standard', help='Disk type')
def storage_create_disk(name: str, size: int, project_id: str, zone: str, disk_type: str):
    """Create a Persistent Disk."""
    try:
        provisioner = GCPStorageProvisioner(project_id=project_id, zone=zone)
        provisioner.create_disk(disk_name=name, size_gb=size, disk_type=disk_type)
    except Exception as e:
        print_error(f"Failed to create disk: {e}")
        sys.exit(1)


def main():
    """Main entry point for CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        print_warning("\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

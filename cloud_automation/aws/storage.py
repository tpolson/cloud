"""AWS storage provisioning (S3 and EBS)."""

import boto3
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError

from cloud_automation.utils import (
    print_success,
    print_error,
    print_info,
    print_warning,
    format_tags,
    validate_name,
)


class AWSStorageProvisioner:
    """Provisions and manages AWS storage (S3 and EBS)."""

    region: str
    s3_client: Any
    ec2_client: Any

    def __init__(self, region: str = "us-east-1", **kwargs: Any) -> None:
        """Initialize AWS storage provisioner.

        Args:
            region: AWS region
            **kwargs: Additional boto3 client parameters
        """
        self.region = region
        try:
            self.s3_client = boto3.client('s3', region_name=region, **kwargs)
            self.ec2_client = boto3.client('ec2', region_name=region, **kwargs)
        except Exception as e:
            print_error(f"Failed to initialize AWS clients: {e}")
            raise

    # ==================== S3 Buckets ====================

    def create_s3_bucket(
        self,
        bucket_name: str,
        versioning: bool = False,
        encryption: bool = True,
        public_access: bool = False,
        tags: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create an S3 bucket.

        Args:
            bucket_name: Bucket name (must be globally unique)
            versioning: Enable versioning
            encryption: Enable default encryption (AES256)
            public_access: Allow public access (default: False)
            tags: Resource tags

        Returns:
            Bucket information dictionary

        Raises:
            ValueError: If bucket name is invalid
            ClientError: If AWS API call fails
        """
        try:
            # S3 bucket names have specific rules
            if not bucket_name.islower():
                raise ValueError("S3 bucket names must be lowercase")
            if len(bucket_name) < 3 or len(bucket_name) > 63:
                raise ValueError("S3 bucket name must be between 3 and 63 characters")

            print_info(f"Creating S3 bucket '{bucket_name}'...")

            # Create bucket
            if self.region == 'us-east-1':
                self.s3_client.create_bucket(Bucket=bucket_name)
            else:
                self.s3_client.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={'LocationConstraint': self.region}
                )

            print_success(f"S3 bucket created: {bucket_name}")

            # Enable versioning if requested
            if versioning:
                self.s3_client.put_bucket_versioning(
                    Bucket=bucket_name,
                    VersioningConfiguration={'Status': 'Enabled'}
                )
                print_success(f"Versioning enabled for {bucket_name}")

            # Enable encryption if requested
            if encryption:
                self.s3_client.put_bucket_encryption(
                    Bucket=bucket_name,
                    ServerSideEncryptionConfiguration={
                        'Rules': [
                            {
                                'ApplyServerSideEncryptionByDefault': {
                                    'SSEAlgorithm': 'AES256'
                                }
                            }
                        ]
                    }
                )
                print_success(f"Encryption enabled for {bucket_name}")

            # Block public access unless explicitly allowed
            if not public_access:
                self.s3_client.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration={
                        'BlockPublicAcls': True,
                        'IgnorePublicAcls': True,
                        'BlockPublicPolicy': True,
                        'RestrictPublicBuckets': True
                    }
                )
                print_success(f"Public access blocked for {bucket_name}")

            # Add tags if provided
            if tags:
                self.s3_client.put_bucket_tagging(
                    Bucket=bucket_name,
                    Tagging={'TagSet': format_tags(tags)}
                )

            return {
                'bucket_name': bucket_name,
                'region': self.region,
                'versioning': versioning,
                'encryption': encryption,
            }

        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketAlreadyExists':
                print_error(f"Bucket name '{bucket_name}' already exists globally")
            elif e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
                print_warning(f"Bucket '{bucket_name}' already owned by you")
            else:
                print_error(f"Failed to create bucket: {e}")
            raise
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            raise

    def list_s3_buckets(self) -> List[Dict[str, Any]]:
        """List all S3 buckets.

        Returns:
            List of bucket information dictionaries
        """
        try:
            response = self.s3_client.list_buckets()

            buckets = []
            for bucket in response['Buckets']:
                bucket_info = {
                    'name': bucket['Name'],
                    'creation_date': bucket['CreationDate'],
                }

                # Try to get bucket region
                try:
                    location = self.s3_client.get_bucket_location(Bucket=bucket['Name'])
                    bucket_info['region'] = location['LocationConstraint'] or 'us-east-1'
                except:
                    bucket_info['region'] = 'unknown'

                buckets.append(bucket_info)

            return buckets

        except ClientError as e:
            print_error(f"Failed to list buckets: {e}")
            raise

    def delete_s3_bucket(self, bucket_name: str, force: bool = False) -> None:
        """Delete an S3 bucket.

        Args:
            bucket_name: Bucket name
            force: If True, delete all objects first

        Raises:
            ClientError: If deletion fails
        """
        try:
            if force:
                print_warning(f"Deleting all objects in {bucket_name}...")
                # Delete all objects and versions
                paginator = self.s3_client.get_paginator('list_object_versions')
                for page in paginator.paginate(Bucket=bucket_name):
                    objects = []
                    for version in page.get('Versions', []):
                        objects.append({'Key': version['Key'], 'VersionId': version['VersionId']})
                    for marker in page.get('DeleteMarkers', []):
                        objects.append({'Key': marker['Key'], 'VersionId': marker['VersionId']})

                    if objects:
                        self.s3_client.delete_objects(
                            Bucket=bucket_name,
                            Delete={'Objects': objects}
                        )

            print_warning(f"Deleting S3 bucket '{bucket_name}'...")
            self.s3_client.delete_bucket(Bucket=bucket_name)
            print_success(f"S3 bucket deleted: {bucket_name}")

        except ClientError as e:
            if e.response['Error']['Code'] == 'BucketNotEmpty':
                print_error(f"Bucket '{bucket_name}' is not empty. Use --force to delete contents")
            else:
                print_error(f"Failed to delete bucket: {e}")
            raise

    # ==================== EBS Volumes ====================

    def create_ebs_volume(
        self,
        name: str,
        size: int,
        volume_type: str = "gp3",
        availability_zone: Optional[str] = None,
        snapshot_id: Optional[str] = None,
        iops: Optional[int] = None,
        throughput: Optional[int] = None,
        tags: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create an EBS volume.

        Args:
            name: Volume name
            size: Volume size in GB
            volume_type: Volume type (gp2, gp3, io1, io2, st1, sc1, standard)
            availability_zone: AZ (if None, uses first AZ in region)
            snapshot_id: Snapshot to restore from
            iops: Provisioned IOPS (for io1, io2, gp3)
            throughput: Throughput in MB/s (for gp3)
            tags: Resource tags

        Returns:
            Volume information dictionary
        """
        try:
            validate_name(name, "aws")

            # Get availability zone if not specified
            if not availability_zone:
                azs = self.ec2_client.describe_availability_zones()['AvailabilityZones']
                availability_zone = azs[0]['ZoneName']
                print_info(f"Using availability zone: {availability_zone}")

            # Prepare volume parameters
            volume_params = {
                'AvailabilityZone': availability_zone,
                'Size': size,
                'VolumeType': volume_type,
                'TagSpecifications': [
                    {
                        'ResourceType': 'volume',
                        'Tags': format_tags({'Name': name, **(tags or {})}),
                    }
                ],
            }

            if snapshot_id:
                volume_params['SnapshotId'] = snapshot_id

            if iops and volume_type in ['io1', 'io2', 'gp3']:
                volume_params['Iops'] = iops

            if throughput and volume_type == 'gp3':
                volume_params['Throughput'] = throughput

            print_info(f"Creating EBS volume '{name}' ({size}GB, {volume_type})...")

            response = self.ec2_client.create_volume(**volume_params)
            volume_id = response['VolumeId']

            print_success(f"EBS volume created: {volume_id}")

            return {
                'volume_id': volume_id,
                'name': name,
                'size': size,
                'volume_type': volume_type,
                'availability_zone': availability_zone,
                'state': response['State'],
            }

        except ClientError as e:
            print_error(f"Failed to create EBS volume: {e}")
            raise

    def list_ebs_volumes(self, filters: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """List EBS volumes.

        Args:
            filters: Optional filters for the query

        Returns:
            List of volume information dictionaries
        """
        try:
            params = {}
            if filters:
                params['Filters'] = filters

            response = self.ec2_client.describe_volumes(**params)

            volumes = []
            for volume in response['Volumes']:
                volumes.append({
                    'volume_id': volume['VolumeId'],
                    'name': next(
                        (tag['Value'] for tag in volume.get('Tags', []) if tag['Key'] == 'Name'),
                        'N/A'
                    ),
                    'size': volume['Size'],
                    'volume_type': volume['VolumeType'],
                    'state': volume['State'],
                    'availability_zone': volume['AvailabilityZone'],
                })

            return volumes

        except ClientError as e:
            print_error(f"Failed to list EBS volumes: {e}")
            raise

    def delete_ebs_volume(self, volume_id: str) -> None:
        """Delete an EBS volume.

        Args:
            volume_id: Volume ID

        Raises:
            ClientError: If deletion fails
        """
        try:
            print_warning(f"Deleting EBS volume {volume_id}...")
            self.ec2_client.delete_volume(VolumeId=volume_id)
            print_success(f"EBS volume deleted: {volume_id}")

        except ClientError as e:
            print_error(f"Failed to delete volume: {e}")
            raise

    def attach_volume(self, volume_id: str, instance_id: str, device: str = "/dev/sdf") -> None:
        """Attach EBS volume to an EC2 instance.

        Args:
            volume_id: Volume ID
            instance_id: EC2 instance ID
            device: Device name (e.g., /dev/sdf)
        """
        try:
            print_info(f"Attaching volume {volume_id} to instance {instance_id}...")
            self.ec2_client.attach_volume(
                VolumeId=volume_id,
                InstanceId=instance_id,
                Device=device
            )
            print_success(f"Volume attached successfully")

        except ClientError as e:
            print_error(f"Failed to attach volume: {e}")
            raise

    def detach_volume(self, volume_id: str, force: bool = False) -> None:
        """Detach EBS volume from an instance.

        Args:
            volume_id: Volume ID
            force: Force detachment

        Raises:
            ClientError: If detachment fails
        """
        try:
            print_info(f"Detaching volume {volume_id}...")
            self.ec2_client.detach_volume(VolumeId=volume_id, Force=force)
            print_success(f"Volume detached successfully")

        except ClientError as e:
            print_error(f"Failed to detach volume: {e}")
            raise

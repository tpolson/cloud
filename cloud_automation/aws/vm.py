"""AWS EC2 VM provisioning."""

import boto3
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError, BotoCoreError

from cloud_automation.utils import (
    print_success,
    print_error,
    print_info,
    print_warning,
    format_tags,
    validate_name,
)


class AWSVMProvisioner:
    """Provisions and manages AWS EC2 instances."""

    def __init__(self, region: str = "us-east-1", **kwargs):
        """Initialize AWS VM provisioner.

        Args:
            region: AWS region
            **kwargs: Additional boto3 client parameters
        """
        self.region = region
        try:
            self.ec2_client = boto3.client('ec2', region_name=region, **kwargs)
            self.ec2_resource = boto3.resource('ec2', region_name=region, **kwargs)
        except Exception as e:
            print_error(f"Failed to initialize AWS client: {e}")
            raise

    def create_instance(
        self,
        name: str,
        instance_type: str = "t2.micro",
        ami: Optional[str] = None,
        key_name: Optional[str] = None,
        security_group_ids: Optional[List[str]] = None,
        subnet_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        user_data: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create an EC2 instance.

        Args:
            name: Instance name
            instance_type: EC2 instance type (e.g., t2.micro, t3.medium)
            ami: AMI ID (if None, uses latest Amazon Linux 2)
            key_name: SSH key pair name
            security_group_ids: List of security group IDs
            subnet_id: Subnet ID
            tags: Additional tags
            user_data: User data script
            **kwargs: Additional parameters for run_instances

        Returns:
            Instance information dictionary

        Raises:
            ValueError: If parameters are invalid
            ClientError: If AWS API call fails
        """
        try:
            validate_name(name, "aws")

            # Get latest Amazon Linux 2 AMI if not specified
            if not ami:
                ami = self._get_latest_amazon_linux_ami()
                print_info(f"Using AMI: {ami}")

            # Prepare tags
            instance_tags = {"Name": name}
            if tags:
                instance_tags.update(tags)

            tag_specifications = [
                {
                    "ResourceType": "instance",
                    "Tags": format_tags(instance_tags),
                }
            ]

            # Prepare instance parameters
            instance_params = {
                "ImageId": ami,
                "InstanceType": instance_type,
                "MinCount": 1,
                "MaxCount": 1,
                "TagSpecifications": tag_specifications,
            }

            if key_name:
                instance_params["KeyName"] = key_name

            if security_group_ids:
                instance_params["SecurityGroupIds"] = security_group_ids

            if subnet_id:
                instance_params["SubnetId"] = subnet_id

            if user_data:
                instance_params["UserData"] = user_data

            # Merge additional parameters
            instance_params.update(kwargs)

            print_info(f"Creating EC2 instance '{name}' ({instance_type})...")

            # Create instance
            response = self.ec2_client.run_instances(**instance_params)
            instance_id = response['Instances'][0]['InstanceId']

            print_success(f"Instance created: {instance_id}")

            # Wait for instance to be running
            print_info("Waiting for instance to be running...")
            waiter = self.ec2_client.get_waiter('instance_running')
            waiter.wait(InstanceIds=[instance_id])

            # Get instance details
            instance_info = self.get_instance(instance_id)
            print_success(f"Instance '{name}' is now running")

            if instance_info.get('public_ip'):
                print_info(f"Public IP: {instance_info['public_ip']}")
            if instance_info.get('private_ip'):
                print_info(f"Private IP: {instance_info['private_ip']}")

            return instance_info

        except ClientError as e:
            print_error(f"Failed to create instance: {e}")
            raise
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            raise

    def get_instance(self, instance_id: str) -> Dict[str, Any]:
        """Get instance information.

        Args:
            instance_id: EC2 instance ID

        Returns:
            Instance information dictionary
        """
        try:
            response = self.ec2_client.describe_instances(InstanceIds=[instance_id])
            instance = response['Reservations'][0]['Instances'][0]

            return {
                'instance_id': instance['InstanceId'],
                'instance_type': instance['InstanceType'],
                'state': instance['State']['Name'],
                'public_ip': instance.get('PublicIpAddress'),
                'private_ip': instance.get('PrivateIpAddress'),
                'launch_time': instance['LaunchTime'],
                'tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])},
            }

        except ClientError as e:
            print_error(f"Failed to get instance info: {e}")
            raise

    def list_instances(self, filters: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """List EC2 instances.

        Args:
            filters: Optional filters for the query

        Returns:
            List of instance information dictionaries
        """
        try:
            params = {}
            if filters:
                params['Filters'] = filters

            response = self.ec2_client.describe_instances(**params)

            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instances.append({
                        'instance_id': instance['InstanceId'],
                        'name': next(
                            (tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'),
                            'N/A'
                        ),
                        'instance_type': instance['InstanceType'],
                        'state': instance['State']['Name'],
                        'public_ip': instance.get('PublicIpAddress', 'N/A'),
                        'private_ip': instance.get('PrivateIpAddress', 'N/A'),
                    })

            return instances

        except ClientError as e:
            print_error(f"Failed to list instances: {e}")
            raise

    def stop_instance(self, instance_id: str) -> None:
        """Stop an EC2 instance.

        Args:
            instance_id: EC2 instance ID
        """
        try:
            print_info(f"Stopping instance {instance_id}...")
            self.ec2_client.stop_instances(InstanceIds=[instance_id])
            print_success(f"Instance {instance_id} stopped")

        except ClientError as e:
            print_error(f"Failed to stop instance: {e}")
            raise

    def start_instance(self, instance_id: str) -> None:
        """Start an EC2 instance.

        Args:
            instance_id: EC2 instance ID
        """
        try:
            print_info(f"Starting instance {instance_id}...")
            self.ec2_client.start_instances(InstanceIds=[instance_id])
            print_success(f"Instance {instance_id} started")

        except ClientError as e:
            print_error(f"Failed to start instance: {e}")
            raise

    def reboot_instance(self, instance_id: str) -> None:
        """Reboot an EC2 instance.

        Args:
            instance_id: EC2 instance ID
        """
        try:
            print_info(f"Rebooting instance {instance_id}...")
            self.ec2_client.reboot_instances(InstanceIds=[instance_id])
            print_success(f"Instance {instance_id} rebooted")

        except ClientError as e:
            print_error(f"Failed to reboot instance: {e}")
            raise

    def terminate_instance(self, instance_id: str) -> None:
        """Terminate an EC2 instance.

        Args:
            instance_id: EC2 instance ID
        """
        try:
            print_warning(f"Terminating instance {instance_id}...")
            self.ec2_client.terminate_instances(InstanceIds=[instance_id])
            print_success(f"Instance {instance_id} terminated")

        except ClientError as e:
            print_error(f"Failed to terminate instance: {e}")
            raise

    def _get_latest_amazon_linux_ami(self) -> str:
        """Get the latest Amazon Linux 2 AMI ID.

        Returns:
            AMI ID
        """
        try:
            response = self.ec2_client.describe_images(
                Owners=['amazon'],
                Filters=[
                    {'Name': 'name', 'Values': ['amzn2-ami-hvm-*-x86_64-gp2']},
                    {'Name': 'state', 'Values': ['available']},
                ],
            )

            # Sort by creation date and get the latest
            images = sorted(response['Images'], key=lambda x: x['CreationDate'], reverse=True)
            return images[0]['ImageId']

        except Exception as e:
            print_error(f"Failed to get latest AMI: {e}")
            # Fallback to a known AMI (this might be outdated)
            return "ami-0c55b159cbfafe1f0"

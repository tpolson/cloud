"""AWS EC2 VM provisioning."""

import boto3
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from botocore.exceptions import ClientError, BotoCoreError

if TYPE_CHECKING:
    from mypy_boto3_ec2.client import EC2Client
    from mypy_boto3_ec2.service_resource import EC2ServiceResource

from cloud_automation.utils import (
    print_success,
    print_error,
    print_info,
    print_warning,
    format_tags,
    validate_name,
)
from cloud_automation.validators import AWSValidator, CommonValidator, ValidationError


class AWSVMProvisioner:
    """Provisions and manages AWS EC2 instances."""

    region: str
    ec2_client: Any  # Would be EC2Client with mypy_boto3_ec2 installed
    ec2_resource: Any  # Would be EC2ServiceResource with mypy_boto3_ec2 installed

    def __init__(self, region: str = "us-east-1", **kwargs: Any) -> None:
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
        spot_instance: bool = False,
        **kwargs: Any
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
            spot_instance: Request spot instance for cost savings (default: False)
            **kwargs: Additional parameters for run_instances

        Returns:
            Instance information dictionary

        Raises:
            ValueError: If parameters are invalid
            ClientError: If AWS API call fails
        """
        try:
            # Validate inputs
            validate_name(name, "aws")
            AWSValidator.validate_instance_type(instance_type)

            if ami:
                AWSValidator.validate_ami_id(ami)
            else:
                # Get latest Amazon Linux 2 AMI if not specified
                ami = self._get_latest_amazon_linux_ami()
                print_info(f"Using AMI: {ami}")

            # Validate security group IDs if provided
            if security_group_ids:
                for sg_id in security_group_ids:
                    if not sg_id.startswith('sg-'):
                        raise ValidationError(f"Invalid security group ID format: {sg_id}")

            # Prepare and validate tags
            instance_tags = {"Name": name}
            if tags:
                tags = CommonValidator.validate_tags_labels(tags)
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

            # Configure spot instance if requested
            if spot_instance:
                instance_params["InstanceMarketOptions"] = {
                    "MarketType": "spot",
                    "SpotOptions": {
                        "SpotInstanceType": "one-time"
                    }
                }
                print_info("Requesting spot instance for cost savings...")

            # Merge additional parameters
            instance_params.update(kwargs)

            instance_desc = f"spot instance" if spot_instance else f"instance"
            print_info(f"Creating EC2 {instance_desc} '{name}' ({instance_type})...")

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

    def list_images(
        self,
        owners: Optional[List[str]] = None,
        name_filter: Optional[str] = None,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """List available AMIs.

        Args:
            owners: List of owner IDs (e.g., ['self', 'amazon', '099720109477'])
                   'self' for your own images, 'amazon' for AWS official
            name_filter: Filter by image name (wildcard supported)
            max_results: Maximum number of results to return

        Returns:
            List of image information dictionaries
        """
        try:
            filters = [{'Name': 'state', 'Values': ['available']}]

            if name_filter:
                filters.append({'Name': 'name', 'Values': [f'*{name_filter}*']})

            # Default to common owners if none specified
            if owners is None:
                owners = ['amazon', 'self']

            response = self.ec2_client.describe_images(
                Owners=owners,
                Filters=filters,
            )

            images = []
            for img in response.get('Images', [])[:max_results]:
                images.append({
                    'image_id': img['ImageId'],
                    'name': img.get('Name', 'N/A'),
                    'description': img.get('Description', 'N/A'),
                    'architecture': img.get('Architecture', 'N/A'),
                    'platform': img.get('Platform', 'Linux'),
                    'creation_date': img.get('CreationDate', 'N/A'),
                    'owner_id': img.get('OwnerId', 'N/A'),
                    'public': img.get('Public', False),
                    'root_device_type': img.get('RootDeviceType', 'N/A'),
                })

            # Sort by creation date (newest first)
            images.sort(key=lambda x: x['creation_date'], reverse=True)

            return images

        except ClientError as e:
            print_error(f"Failed to list images: {e}")
            raise

    def search_images(
        self,
        search_term: str,
        owner: str = 'amazon',
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """Search for AMIs by name or description.

        Args:
            search_term: Term to search for
            owner: Owner filter ('amazon', 'self', 'aws-marketplace', etc.)
            max_results: Maximum number of results

        Returns:
            List of matching image information
        """
        return self.list_images(
            owners=[owner],
            name_filter=search_term,
            max_results=max_results
        )

    def get_popular_images(self) -> Dict[str, List[Dict[str, str]]]:
        """Get commonly used AMI categories.

        Returns:
            Dictionary of image categories with AMI information
        """
        popular_images = {
            'Amazon Linux': [
                {'name': 'Amazon Linux 2023', 'filter': 'al2023-ami-*-x86_64'},
                {'name': 'Amazon Linux 2', 'filter': 'amzn2-ami-hvm-*-x86_64-gp2'},
            ],
            'Ubuntu': [
                {'name': 'Ubuntu 22.04 LTS', 'filter': 'ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*'},
                {'name': 'Ubuntu 20.04 LTS', 'filter': 'ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*'},
            ],
            'Red Hat': [
                {'name': 'RHEL 9', 'filter': 'RHEL-9.*_HVM-*-x86_64-*'},
                {'name': 'RHEL 8', 'filter': 'RHEL-8.*_HVM-*-x86_64-*'},
            ],
            'Windows': [
                {'name': 'Windows Server 2022', 'filter': 'Windows_Server-2022-English-Full-Base-*'},
                {'name': 'Windows Server 2019', 'filter': 'Windows_Server-2019-English-Full-Base-*'},
            ],
        }

        results = {}
        for category, image_list in popular_images.items():
            results[category] = []
            for image_info in image_list:
                try:
                    response = self.ec2_client.describe_images(
                        Owners=['amazon', '099720109477'],  # Amazon and Canonical (Ubuntu)
                        Filters=[
                            {'Name': 'name', 'Values': [image_info['filter']]},
                            {'Name': 'state', 'Values': ['available']},
                        ],
                    )

                    if response['Images']:
                        # Get the latest image
                        latest = sorted(response['Images'],
                                      key=lambda x: x['CreationDate'],
                                      reverse=True)[0]
                        results[category].append({
                            'name': image_info['name'],
                            'image_id': latest['ImageId'],
                            'description': latest.get('Description', ''),
                            'creation_date': latest['CreationDate'],
                        })
                except Exception:
                    continue

        return results

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

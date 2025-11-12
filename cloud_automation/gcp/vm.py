"""GCP Compute Engine VM provisioning."""

from typing import Dict, List, Optional, Any
from google.cloud import compute_v1
from google.api_core.exceptions import GoogleAPIError, NotFound

from cloud_automation.utils import (
    print_success,
    print_error,
    print_info,
    print_warning,
    format_labels,
    validate_name,
)


class GCPVMProvisioner:
    """Provisions and manages GCP Compute Engine instances."""

    def __init__(self, project_id: str, zone: str = "us-central1-a", credentials=None):
        """Initialize GCP VM provisioner.

        Args:
            project_id: GCP project ID
            zone: GCP zone
            credentials: Optional Google credentials object
        """
        self.project_id = project_id
        self.zone = zone
        self.credentials = credentials
        try:
            self.instances_client = compute_v1.InstancesClient(credentials=credentials)
            self.images_client = compute_v1.ImagesClient(credentials=credentials)
        except Exception as e:
            print_error(f"Failed to initialize GCP clients: {e}")
            raise

    def create_instance(
        self,
        name: str,
        machine_type: str = "e2-micro",
        source_image_family: str = "debian-11",
        source_image_project: str = "debian-cloud",
        disk_size_gb: int = 10,
        network: str = "global/networks/default",
        external_ip: bool = True,
        labels: Optional[Dict[str, str]] = None,
        startup_script: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a GCE instance.

        Args:
            name: Instance name
            machine_type: Machine type (e.g., e2-micro, n1-standard-1)
            source_image_family: Image family (e.g., debian-11, ubuntu-2004-lts)
            source_image_project: Image project (e.g., debian-cloud, ubuntu-os-cloud)
            disk_size_gb: Boot disk size in GB
            network: Network (default: default network)
            external_ip: Assign external IP address
            labels: Resource labels
            startup_script: Startup script to run
            **kwargs: Additional parameters

        Returns:
            Instance information dictionary

        Raises:
            ValueError: If parameters are invalid
            GoogleAPIError: If GCP API call fails
        """
        try:
            validate_name(name, "gcp")

            # Get the latest image from the family
            image = self.images_client.get_from_family(
                project=source_image_project,
                family=source_image_family
            )

            print_info(f"Using image: {image.name}")

            # Configure the machine type
            machine_type_path = f"zones/{self.zone}/machineTypes/{machine_type}"

            # Configure the boot disk
            disk = compute_v1.AttachedDisk()
            disk.boot = True
            disk.auto_delete = True
            disk.initialize_params = compute_v1.AttachedDiskInitializeParams()
            disk.initialize_params.source_image = image.self_link
            disk.initialize_params.disk_size_gb = disk_size_gb

            # Configure the network interface
            network_interface = compute_v1.NetworkInterface()
            network_interface.network = f"projects/{self.project_id}/{network}"

            if external_ip:
                access_config = compute_v1.AccessConfig()
                access_config.name = "External NAT"
                access_config.type_ = "ONE_TO_ONE_NAT"
                network_interface.access_configs = [access_config]

            # Create the instance
            instance = compute_v1.Instance()
            instance.name = name
            instance.machine_type = machine_type_path
            instance.disks = [disk]
            instance.network_interfaces = [network_interface]

            # Add labels
            if labels:
                instance.labels = format_labels(labels)

            # Add startup script
            if startup_script:
                metadata = compute_v1.Metadata()
                metadata.items = [
                    compute_v1.Items(key="startup-script", value=startup_script)
                ]
                instance.metadata = metadata

            print_info(f"Creating GCE instance '{name}' ({machine_type})...")

            # Insert the instance
            operation = self.instances_client.insert(
                project=self.project_id,
                zone=self.zone,
                instance_resource=instance
            )

            # Wait for operation to complete
            print_info("Waiting for instance creation to complete...")
            self._wait_for_operation(operation)

            print_success(f"Instance '{name}' created successfully")

            # Get instance details
            instance_info = self.get_instance(name)

            if instance_info.get('external_ip'):
                print_info(f"External IP: {instance_info['external_ip']}")
            if instance_info.get('internal_ip'):
                print_info(f"Internal IP: {instance_info['internal_ip']}")

            return instance_info

        except GoogleAPIError as e:
            print_error(f"Failed to create instance: {e}")
            raise
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            raise

    def get_instance(self, instance_name: str) -> Dict[str, Any]:
        """Get instance information.

        Args:
            instance_name: Instance name

        Returns:
            Instance information dictionary
        """
        try:
            instance = self.instances_client.get(
                project=self.project_id,
                zone=self.zone,
                instance=instance_name
            )

            # Extract network information
            external_ip = None
            internal_ip = None
            if instance.network_interfaces:
                interface = instance.network_interfaces[0]
                internal_ip = interface.network_i_p
                if interface.access_configs:
                    external_ip = interface.access_configs[0].nat_i_p

            return {
                'name': instance.name,
                'machine_type': instance.machine_type.split('/')[-1],
                'status': instance.status,
                'zone': self.zone,
                'external_ip': external_ip,
                'internal_ip': internal_ip,
                'creation_timestamp': instance.creation_timestamp,
                'labels': dict(instance.labels) if instance.labels else {},
            }

        except NotFound:
            print_error(f"Instance '{instance_name}' not found")
            raise
        except GoogleAPIError as e:
            print_error(f"Failed to get instance info: {e}")
            raise

    def list_instances(self) -> List[Dict[str, Any]]:
        """List all GCE instances in the zone.

        Returns:
            List of instance information dictionaries
        """
        try:
            instances = []
            request = compute_v1.ListInstancesRequest(
                project=self.project_id,
                zone=self.zone
            )

            for instance in self.instances_client.list(request=request):
                # Extract network information
                external_ip = "N/A"
                internal_ip = "N/A"
                if instance.network_interfaces:
                    interface = instance.network_interfaces[0]
                    internal_ip = interface.network_i_p or "N/A"
                    if interface.access_configs:
                        external_ip = interface.access_configs[0].nat_i_p or "N/A"

                instances.append({
                    'name': instance.name,
                    'machine_type': instance.machine_type.split('/')[-1],
                    'status': instance.status,
                    'external_ip': external_ip,
                    'internal_ip': internal_ip,
                })

            return instances

        except GoogleAPIError as e:
            print_error(f"Failed to list instances: {e}")
            raise

    def stop_instance(self, instance_name: str) -> None:
        """Stop a GCE instance.

        Args:
            instance_name: Instance name
        """
        try:
            print_info(f"Stopping instance '{instance_name}'...")
            operation = self.instances_client.stop(
                project=self.project_id,
                zone=self.zone,
                instance=instance_name
            )
            self._wait_for_operation(operation)
            print_success(f"Instance '{instance_name}' stopped")

        except GoogleAPIError as e:
            print_error(f"Failed to stop instance: {e}")
            raise

    def start_instance(self, instance_name: str) -> None:
        """Start a GCE instance.

        Args:
            instance_name: Instance name
        """
        try:
            print_info(f"Starting instance '{instance_name}'...")
            operation = self.instances_client.start(
                project=self.project_id,
                zone=self.zone,
                instance=instance_name
            )
            self._wait_for_operation(operation)
            print_success(f"Instance '{instance_name}' started")

        except GoogleAPIError as e:
            print_error(f"Failed to start instance: {e}")
            raise

    def reboot_instance(self, instance_name: str) -> None:
        """Reboot a GCE instance.

        Args:
            instance_name: Instance name
        """
        try:
            print_info(f"Rebooting instance '{instance_name}'...")
            operation = self.instances_client.reset(
                project=self.project_id,
                zone=self.zone,
                instance=instance_name
            )
            self._wait_for_operation(operation)
            print_success(f"Instance '{instance_name}' rebooted")

        except GoogleAPIError as e:
            print_error(f"Failed to reboot instance: {e}")
            raise

    def delete_instance(self, instance_name: str) -> None:
        """Delete a GCE instance.

        Args:
            instance_name: Instance name
        """
        try:
            print_warning(f"Deleting instance '{instance_name}'...")
            operation = self.instances_client.delete(
                project=self.project_id,
                zone=self.zone,
                instance=instance_name
            )
            self._wait_for_operation(operation)
            print_success(f"Instance '{instance_name}' deleted")

        except GoogleAPIError as e:
            print_error(f"Failed to delete instance: {e}")
            raise

    def list_images(
        self,
        project: Optional[str] = None,
        name_filter: Optional[str] = None,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """List available images.

        Args:
            project: Project ID to list images from (None for current project)
            name_filter: Filter by image name (partial match)
            max_results: Maximum number of results

        Returns:
            List of image information dictionaries
        """
        try:
            project_to_use = project or self.project_id
            request = compute_v1.ListImagesRequest(
                project=project_to_use
            )

            images = []
            for img in self.images_client.list(request=request):
                # Apply name filter if specified
                if name_filter and name_filter.lower() not in img.name.lower():
                    continue

                images.append({
                    'name': img.name,
                    'description': img.description or 'N/A',
                    'family': img.family or 'N/A',
                    'architecture': img.architecture or 'X86_64',
                    'creation_timestamp': img.creation_timestamp or 'N/A',
                    'disk_size_gb': img.disk_size_gb or 0,
                    'project': project_to_use,
                    'self_link': img.self_link,
                    'status': img.status or 'READY',
                })

                if len(images) >= max_results:
                    break

            # Sort by creation date (newest first)
            images.sort(key=lambda x: x['creation_timestamp'], reverse=True)

            return images

        except GoogleAPIError as e:
            print_error(f"Failed to list images: {e}")
            raise

    def search_images(
        self,
        search_term: str,
        project: Optional[str] = None,
        max_results: int = 20
    ) -> List[Dict[str, Any]]:
        """Search for images by name.

        Args:
            search_term: Term to search for
            project: Project to search in (None for current project)
            max_results: Maximum number of results

        Returns:
            List of matching image information
        """
        return self.list_images(
            project=project,
            name_filter=search_term,
            max_results=max_results
        )

    def get_popular_images(self) -> Dict[str, List[Dict[str, str]]]:
        """Get commonly used image families.

        Returns:
            Dictionary of image categories with image information
        """
        popular_projects = {
            'Debian': {
                'project': 'debian-cloud',
                'families': ['debian-12', 'debian-11', 'debian-10']
            },
            'Ubuntu': {
                'project': 'ubuntu-os-cloud',
                'families': ['ubuntu-2204-lts', 'ubuntu-2004-lts', 'ubuntu-1804-lts']
            },
            'CentOS': {
                'project': 'centos-cloud',
                'families': ['centos-stream-9', 'centos-stream-8', 'centos-7']
            },
            'Rocky Linux': {
                'project': 'rocky-linux-cloud',
                'families': ['rocky-linux-9', 'rocky-linux-8']
            },
            'Red Hat': {
                'project': 'rhel-cloud',
                'families': ['rhel-9', 'rhel-8', 'rhel-7']
            },
            'Windows Server': {
                'project': 'windows-cloud',
                'families': ['windows-2022', 'windows-2019', 'windows-2016']
            },
        }

        results = {}
        for category, info in popular_projects.items():
            results[category] = []
            for family in info['families']:
                try:
                    image = self.images_client.get_from_family(
                        project=info['project'],
                        family=family
                    )
                    results[category].append({
                        'name': f"{family} (latest)",
                        'image_name': image.name,
                        'family': family,
                        'project': info['project'],
                        'description': image.description or '',
                        'creation_timestamp': image.creation_timestamp,
                        'disk_size_gb': image.disk_size_gb,
                    })
                except Exception:
                    continue

        return results

    def list_image_families(self, project: Optional[str] = None) -> List[str]:
        """List available image families in a project.

        Args:
            project: Project ID (None for current project)

        Returns:
            List of image family names
        """
        try:
            project_to_use = project or self.project_id
            images = self.list_images(project=project_to_use, max_results=1000)

            # Extract unique families
            families = set()
            for img in images:
                if img['family'] != 'N/A':
                    families.add(img['family'])

            return sorted(list(families))

        except GoogleAPIError as e:
            print_error(f"Failed to list image families: {e}")
            raise

    def _wait_for_operation(self, operation) -> None:
        """Wait for a zone operation to complete.

        Args:
            operation: Operation to wait for
        """
        from google.cloud.compute_v1.types import Operation

        if operation.status == Operation.Status.DONE:
            return

        operations_client = compute_v1.ZoneOperationsClient(credentials=self.credentials)

        while True:
            result = operations_client.wait(
                project=self.project_id,
                zone=self.zone,
                operation=operation.name
            )

            if result.status == Operation.Status.DONE:
                if result.error:
                    raise GoogleAPIError(f"Operation failed: {result.error}")
                return

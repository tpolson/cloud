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

    def __init__(self, project_id: str, zone: str = "us-central1-a"):
        """Initialize GCP VM provisioner.

        Args:
            project_id: GCP project ID
            zone: GCP zone
        """
        self.project_id = project_id
        self.zone = zone
        try:
            self.instances_client = compute_v1.InstancesClient()
            self.images_client = compute_v1.ImagesClient()
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

    def _wait_for_operation(self, operation) -> None:
        """Wait for a zone operation to complete.

        Args:
            operation: Operation to wait for
        """
        from google.cloud.compute_v1.types import Operation

        if operation.status == Operation.Status.DONE:
            return

        operations_client = compute_v1.ZoneOperationsClient()

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

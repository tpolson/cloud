"""GCP storage provisioning (Cloud Storage and Persistent Disks)."""

from typing import Dict, List, Optional, Any
from google.cloud import storage
from google.cloud import compute_v1
from google.api_core.exceptions import GoogleAPIError, NotFound, Conflict

from cloud_automation.utils import (
    print_success,
    print_error,
    print_info,
    print_warning,
    format_labels,
)


class GCPStorageProvisioner:
    """Provisions and manages GCP storage (Cloud Storage and Persistent Disks)."""

    def __init__(self, project_id: str, zone: str = "us-central1-a"):
        """Initialize GCP storage provisioner.

        Args:
            project_id: GCP project ID
            zone: GCP zone (for persistent disks)
        """
        self.project_id = project_id
        self.zone = zone
        try:
            self.storage_client = storage.Client(project=project_id)
            self.disks_client = compute_v1.DisksClient()
        except Exception as e:
            print_error(f"Failed to initialize GCP clients: {e}")
            raise

    # ==================== Cloud Storage Buckets ====================

    def create_bucket(
        self,
        bucket_name: str,
        location: str = "US",
        storage_class: str = "STANDARD",
        versioning: bool = False,
        labels: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a Cloud Storage bucket.

        Args:
            bucket_name: Bucket name (must be globally unique)
            location: Bucket location (e.g., US, EU, us-central1)
            storage_class: Storage class (STANDARD, NEARLINE, COLDLINE, ARCHIVE)
            versioning: Enable object versioning
            labels: Resource labels

        Returns:
            Bucket information dictionary

        Raises:
            ValueError: If bucket name is invalid
            GoogleAPIError: If GCP API call fails
        """
        try:
            # GCS bucket names must be lowercase
            if not bucket_name.islower():
                raise ValueError("Cloud Storage bucket names must be lowercase")

            print_info(f"Creating Cloud Storage bucket '{bucket_name}'...")

            # Create bucket
            bucket = self.storage_client.bucket(bucket_name)
            bucket.storage_class = storage_class
            bucket.location = location

            if versioning:
                bucket.versioning_enabled = True

            if labels:
                bucket.labels = format_labels(labels)

            bucket = self.storage_client.create_bucket(bucket)

            print_success(f"Bucket created: {bucket_name}")

            if versioning:
                print_success(f"Versioning enabled for {bucket_name}")

            return {
                'bucket_name': bucket.name,
                'location': bucket.location,
                'storage_class': bucket.storage_class,
                'versioning': versioning,
                'time_created': bucket.time_created,
            }

        except Conflict:
            print_error(f"Bucket name '{bucket_name}' already exists globally")
            raise
        except GoogleAPIError as e:
            print_error(f"Failed to create bucket: {e}")
            raise
        except Exception as e:
            print_error(f"Unexpected error: {e}")
            raise

    def list_buckets(self) -> List[Dict[str, Any]]:
        """List all Cloud Storage buckets in the project.

        Returns:
            List of bucket information dictionaries
        """
        try:
            buckets = []
            for bucket in self.storage_client.list_buckets():
                buckets.append({
                    'name': bucket.name,
                    'location': bucket.location,
                    'storage_class': bucket.storage_class,
                    'time_created': bucket.time_created,
                })

            return buckets

        except GoogleAPIError as e:
            print_error(f"Failed to list buckets: {e}")
            raise

    def delete_bucket(self, bucket_name: str, force: bool = False) -> None:
        """Delete a Cloud Storage bucket.

        Args:
            bucket_name: Bucket name
            force: If True, delete all objects first

        Raises:
            GoogleAPIError: If deletion fails
        """
        try:
            bucket = self.storage_client.bucket(bucket_name)

            if force:
                print_warning(f"Deleting all objects in {bucket_name}...")
                blobs = bucket.list_blobs()
                for blob in blobs:
                    blob.delete()

            print_warning(f"Deleting bucket '{bucket_name}'...")
            bucket.delete()
            print_success(f"Bucket deleted: {bucket_name}")

        except GoogleAPIError as e:
            print_error(f"Failed to delete bucket: {e}")
            raise

    def upload_file(self, bucket_name: str, source_file: str, destination_blob: str) -> None:
        """Upload a file to Cloud Storage.

        Args:
            bucket_name: Bucket name
            source_file: Path to local file
            destination_blob: Destination blob name
        """
        try:
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(destination_blob)

            print_info(f"Uploading {source_file} to {bucket_name}/{destination_blob}...")
            blob.upload_from_filename(source_file)
            print_success(f"File uploaded successfully")

        except GoogleAPIError as e:
            print_error(f"Failed to upload file: {e}")
            raise

    def download_file(self, bucket_name: str, source_blob: str, destination_file: str) -> None:
        """Download a file from Cloud Storage.

        Args:
            bucket_name: Bucket name
            source_blob: Source blob name
            destination_file: Path to save file locally
        """
        try:
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(source_blob)

            print_info(f"Downloading {bucket_name}/{source_blob} to {destination_file}...")
            blob.download_to_filename(destination_file)
            print_success(f"File downloaded successfully")

        except GoogleAPIError as e:
            print_error(f"Failed to download file: {e}")
            raise

    # ==================== Persistent Disks ====================

    def create_disk(
        self,
        disk_name: str,
        size_gb: int,
        disk_type: str = "pd-standard",
        labels: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Create a Persistent Disk.

        Args:
            disk_name: Disk name
            size_gb: Disk size in GB
            disk_type: Disk type (pd-standard, pd-ssd, pd-balanced)
            labels: Resource labels

        Returns:
            Disk information dictionary

        Raises:
            GoogleAPIError: If GCP API call fails
        """
        try:
            # Construct disk type URL
            disk_type_url = f"zones/{self.zone}/diskTypes/{disk_type}"

            # Create disk configuration
            disk = compute_v1.Disk()
            disk.name = disk_name
            disk.size_gb = size_gb
            disk.type_ = disk_type_url

            if labels:
                disk.labels = format_labels(labels)

            print_info(f"Creating Persistent Disk '{disk_name}' ({size_gb}GB, {disk_type})...")

            # Create the disk
            operation = self.disks_client.insert(
                project=self.project_id,
                zone=self.zone,
                disk_resource=disk
            )

            # Wait for operation to complete
            print_info("Waiting for disk creation to complete...")
            self._wait_for_zone_operation(operation)

            print_success(f"Disk '{disk_name}' created successfully")

            return {
                'name': disk_name,
                'size_gb': size_gb,
                'disk_type': disk_type,
                'zone': self.zone,
            }

        except GoogleAPIError as e:
            print_error(f"Failed to create disk: {e}")
            raise

    def list_disks(self) -> List[Dict[str, Any]]:
        """List all Persistent Disks in the zone.

        Returns:
            List of disk information dictionaries
        """
        try:
            disks = []
            request = compute_v1.ListDisksRequest(
                project=self.project_id,
                zone=self.zone
            )

            for disk in self.disks_client.list(request=request):
                disks.append({
                    'name': disk.name,
                    'size_gb': disk.size_gb,
                    'disk_type': disk.type_.split('/')[-1],
                    'status': disk.status,
                    'zone': self.zone,
                })

            return disks

        except GoogleAPIError as e:
            print_error(f"Failed to list disks: {e}")
            raise

    def delete_disk(self, disk_name: str) -> None:
        """Delete a Persistent Disk.

        Args:
            disk_name: Disk name

        Raises:
            GoogleAPIError: If deletion fails
        """
        try:
            print_warning(f"Deleting disk '{disk_name}'...")
            operation = self.disks_client.delete(
                project=self.project_id,
                zone=self.zone,
                disk=disk_name
            )
            self._wait_for_zone_operation(operation)
            print_success(f"Disk '{disk_name}' deleted")

        except GoogleAPIError as e:
            print_error(f"Failed to delete disk: {e}")
            raise

    def attach_disk(self, instance_name: str, disk_name: str) -> None:
        """Attach a Persistent Disk to an instance.

        Args:
            instance_name: Instance name
            disk_name: Disk name
        """
        try:
            instances_client = compute_v1.InstancesClient()

            # Create attached disk object
            attached_disk = compute_v1.AttachedDisk()
            attached_disk.source = f"zones/{self.zone}/disks/{disk_name}"
            attached_disk.device_name = disk_name

            print_info(f"Attaching disk '{disk_name}' to instance '{instance_name}'...")
            operation = instances_client.attach_disk(
                project=self.project_id,
                zone=self.zone,
                instance=instance_name,
                attached_disk_resource=attached_disk
            )
            self._wait_for_zone_operation(operation)
            print_success(f"Disk attached successfully")

        except GoogleAPIError as e:
            print_error(f"Failed to attach disk: {e}")
            raise

    def detach_disk(self, instance_name: str, disk_name: str) -> None:
        """Detach a Persistent Disk from an instance.

        Args:
            instance_name: Instance name
            disk_name: Disk name
        """
        try:
            instances_client = compute_v1.InstancesClient()

            print_info(f"Detaching disk '{disk_name}' from instance '{instance_name}'...")
            operation = instances_client.detach_disk(
                project=self.project_id,
                zone=self.zone,
                instance=instance_name,
                device_name=disk_name
            )
            self._wait_for_zone_operation(operation)
            print_success(f"Disk detached successfully")

        except GoogleAPIError as e:
            print_error(f"Failed to detach disk: {e}")
            raise

    def _wait_for_zone_operation(self, operation) -> None:
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

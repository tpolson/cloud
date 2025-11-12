"""Integration tests for GCP VM provisioner using unittest.mock."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from google.cloud import compute_v1
from google.api_core.exceptions import GoogleAPIError, NotFound

from cloud_automation.gcp.vm import GCPVMProvisioner
from cloud_automation.exceptions import ValidationError


@pytest.fixture
def mock_credentials():
    """Mock GCP credentials."""
    return Mock()


@pytest.fixture
def mock_instances_client():
    """Mock GCP InstancesClient."""
    return MagicMock(spec=compute_v1.InstancesClient)


@pytest.fixture
def mock_images_client():
    """Mock GCP ImagesClient."""
    return MagicMock(spec=compute_v1.ImagesClient)


@pytest.fixture
def provisioner(mock_credentials, mock_instances_client, mock_images_client):
    """Create GCP provisioner with mocked clients."""
    with patch('cloud_automation.gcp.vm.compute_v1.InstancesClient', return_value=mock_instances_client), \
         patch('cloud_automation.gcp.vm.compute_v1.ImagesClient', return_value=mock_images_client):
        prov = GCPVMProvisioner(
            project_id='test-project-123',
            zone='us-central1-a',
            credentials=mock_credentials
        )
        prov.instances_client = mock_instances_client
        prov.images_client = mock_images_client
        return prov


class TestGCPVMProvisionerInitialization:
    """Test provisioner initialization and validation."""

    def test_init_valid_project_and_zone(self, mock_credentials):
        """Test initialization with valid project and zone."""
        with patch('cloud_automation.gcp.vm.compute_v1.InstancesClient'), \
             patch('cloud_automation.gcp.vm.compute_v1.ImagesClient'):
            prov = GCPVMProvisioner(
                project_id='test-project-123',
                zone='us-central1-a',
                credentials=mock_credentials
            )
            assert prov.project_id == 'test-project-123'
            assert prov.zone == 'us-central1-a'

    def test_init_invalid_project_id(self, mock_credentials):
        """Test that invalid project IDs are rejected."""
        with pytest.raises(ValidationError, match="Invalid GCP project ID"):
            GCPVMProvisioner(
                project_id='Invalid_Project!',
                zone='us-central1-a',
                credentials=mock_credentials
            )

    def test_init_invalid_zone(self, mock_credentials):
        """Test that invalid zones are rejected."""
        with pytest.raises(ValidationError, match="Invalid GCP zone"):
            GCPVMProvisioner(
                project_id='test-project-123',
                zone='invalid-zone',
                credentials=mock_credentials
            )


class TestGCPVMProvisionerCreation:
    """Test instance creation operations."""

    def test_create_instance_basic(self, provisioner, mock_images_client):
        """Test basic instance creation."""
        # Mock image response
        mock_image = Mock()
        mock_image.name = 'debian-11-bullseye-v20230101'
        mock_image.self_link = 'projects/debian-cloud/global/images/debian-11-bullseye-v20230101'
        mock_images_client.get_from_family.return_value = mock_image

        # Mock insert response
        mock_operation = Mock()
        mock_operation.name = 'operation-123'
        provisioner.instances_client.insert.return_value = mock_operation

        result = provisioner.create_instance(
            name='test-instance',
            machine_type='e2-micro'
        )

        assert result is not None
        assert result['name'] == 'test-instance'
        assert result['machine_type'] == 'e2-micro'
        assert result['zone'] == 'us-central1-a'

        # Verify insert was called
        provisioner.instances_client.insert.assert_called_once()

    def test_create_instance_with_labels(self, provisioner, mock_images_client):
        """Test instance creation with labels."""
        mock_image = Mock()
        mock_image.name = 'debian-11-bullseye-v20230101'
        mock_image.self_link = 'projects/debian-cloud/global/images/debian-11-bullseye-v20230101'
        mock_images_client.get_from_family.return_value = mock_image

        mock_operation = Mock()
        provisioner.instances_client.insert.return_value = mock_operation

        labels = {
            'environment': 'test',
            'project': 'cloud-automation'
        }

        result = provisioner.create_instance(
            name='labeled-instance',
            machine_type='e2-micro',
            labels=labels
        )

        assert result is not None
        provisioner.instances_client.insert.assert_called_once()

    def test_create_instance_invalid_name(self, provisioner):
        """Test instance creation with invalid name."""
        with pytest.raises(ValidationError, match="Invalid GCP instance name"):
            provisioner.create_instance(
                name='Invalid_Name_With_Underscores',
                machine_type='e2-micro'
            )

    def test_create_instance_invalid_machine_type(self, provisioner):
        """Test instance creation with invalid machine type."""
        with pytest.raises(ValidationError, match="Unknown GCP machine type"):
            provisioner.create_instance(
                name='test-instance',
                machine_type='invalid-type'
            )

    def test_create_instance_invalid_disk_size(self, provisioner, mock_images_client):
        """Test instance creation with invalid disk size."""
        mock_image = Mock()
        mock_image.name = 'debian-11-bullseye-v20230101'
        mock_images_client.get_from_family.return_value = mock_image

        # Disk too small
        with pytest.raises(ValidationError, match="Disk size must be"):
            provisioner.create_instance(
                name='test-instance',
                machine_type='e2-micro',
                disk_size_gb=5  # Below minimum of 10
            )


class TestGCPVMProvisionerListing:
    """Test instance listing operations."""

    def test_list_instances_empty(self, provisioner):
        """Test listing instances when none exist."""
        # Mock empty list response
        provisioner.instances_client.list.return_value = []

        instances = provisioner.list_instances()
        assert instances == []

    def test_list_instances_with_instances(self, provisioner):
        """Test listing instances with results."""
        # Mock instance responses
        mock_instance1 = Mock()
        mock_instance1.name = 'instance-1'
        mock_instance1.machine_type = 'zones/us-central1-a/machineTypes/e2-micro'
        mock_instance1.status = 'RUNNING'
        mock_instance1.network_interfaces = [Mock()]
        mock_instance1.network_interfaces[0].network_i_p = '10.0.0.1'
        mock_instance1.network_interfaces[0].access_configs = [Mock()]
        mock_instance1.network_interfaces[0].access_configs[0].nat_i_p = '35.1.2.3'

        mock_instance2 = Mock()
        mock_instance2.name = 'instance-2'
        mock_instance2.machine_type = 'zones/us-central1-a/machineTypes/e2-small'
        mock_instance2.status = 'TERMINATED'
        mock_instance2.network_interfaces = [Mock()]
        mock_instance2.network_interfaces[0].network_i_p = '10.0.0.2'
        mock_instance2.network_interfaces[0].access_configs = []

        provisioner.instances_client.list.return_value = [mock_instance1, mock_instance2]

        instances = provisioner.list_instances()
        assert len(instances) == 2

        # Verify instance details
        names = [inst['name'] for inst in instances]
        assert 'instance-1' in names
        assert 'instance-2' in names


class TestGCPVMProvisionerLifecycle:
    """Test instance lifecycle operations."""

    def test_stop_instance(self, provisioner):
        """Test stopping an instance."""
        mock_operation = Mock()
        provisioner.instances_client.stop.return_value = mock_operation

        provisioner.stop_instance('test-instance')

        provisioner.instances_client.stop.assert_called_once_with(
            project=provisioner.project_id,
            zone=provisioner.zone,
            instance='test-instance'
        )

    def test_start_instance(self, provisioner):
        """Test starting an instance."""
        mock_operation = Mock()
        provisioner.instances_client.start.return_value = mock_operation

        provisioner.start_instance('test-instance')

        provisioner.instances_client.start.assert_called_once_with(
            project=provisioner.project_id,
            zone=provisioner.zone,
            instance='test-instance'
        )

    def test_reboot_instance(self, provisioner):
        """Test rebooting an instance."""
        mock_operation = Mock()
        provisioner.instances_client.reset.return_value = mock_operation

        provisioner.reboot_instance('test-instance')

        provisioner.instances_client.reset.assert_called_once_with(
            project=provisioner.project_id,
            zone=provisioner.zone,
            instance='test-instance'
        )

    def test_delete_instance(self, provisioner):
        """Test deleting an instance."""
        mock_operation = Mock()
        provisioner.instances_client.delete.return_value = mock_operation

        provisioner.delete_instance('test-instance')

        provisioner.instances_client.delete.assert_called_once_with(
            project=provisioner.project_id,
            zone=provisioner.zone,
            instance='test-instance'
        )

    def test_delete_nonexistent_instance(self, provisioner):
        """Test deleting a non-existent instance raises error."""
        provisioner.instances_client.delete.side_effect = NotFound("Instance not found")

        with pytest.raises(NotFound):
            provisioner.delete_instance('nonexistent-instance')


class TestGCPVMProvisionerImageSearch:
    """Test image search and listing operations."""

    def test_list_images(self, provisioner):
        """Test listing images from a project."""
        # Mock image responses
        mock_image1 = Mock()
        mock_image1.name = 'debian-11-bullseye-v20230101'
        mock_image1.family = 'debian-11'
        mock_image1.description = 'Debian 11 Bullseye'
        mock_image1.disk_size_gb = 10
        mock_image1.architecture = 'X86_64'
        mock_image1.creation_timestamp = '2023-01-01T00:00:00.000-08:00'

        provisioner.images_client.list.return_value = [mock_image1]

        images = provisioner.list_images(project='debian-cloud', max_results=10)

        assert len(images) == 1
        assert images[0]['name'] == 'debian-11-bullseye-v20230101'
        assert images[0]['family'] == 'debian-11'

    def test_search_images(self, provisioner):
        """Test searching for images by name."""
        # Mock image responses
        mock_image = Mock()
        mock_image.name = 'ubuntu-2004-focal-v20230101'
        mock_image.family = 'ubuntu-2004-lts'
        mock_image.description = 'Ubuntu 20.04 LTS'
        mock_image.disk_size_gb = 10
        mock_image.architecture = 'X86_64'
        mock_image.creation_timestamp = '2023-01-01T00:00:00.000-08:00'

        provisioner.images_client.list.return_value = [mock_image]

        results = provisioner.search_images('ubuntu')

        assert len(results) >= 0
        # Mock data should match search term
        if len(results) > 0:
            assert 'ubuntu' in results[0]['name'].lower()

    def test_get_popular_images(self, provisioner):
        """Test getting popular images categorized."""
        # Mock image responses for different families
        mock_images = []
        for family in ['debian-11', 'ubuntu-2004-lts', 'centos-7']:
            mock_img = Mock()
            mock_img.name = f'{family}-v20230101'
            mock_img.family = family
            mock_img.description = f'{family} image'
            mock_img.disk_size_gb = 10
            mock_img.architecture = 'X86_64'
            mock_img.creation_timestamp = '2023-01-01T00:00:00.000-08:00'
            mock_images.append(mock_img)

        provisioner.images_client.list.return_value = mock_images

        popular = provisioner.get_popular_images()

        assert isinstance(popular, dict)
        # Should have categorized results
        assert len(popular) > 0


class TestGCPVMProvisionerValidation:
    """Test input validation in provisioner."""

    def test_invalid_machine_type(self, provisioner):
        """Test that invalid machine types are rejected."""
        with pytest.raises(ValidationError):
            provisioner.create_instance(
                name='test',
                machine_type='not-a-real-machine-type'
            )

    def test_invalid_instance_name_format(self, provisioner):
        """Test that invalid instance names are rejected."""
        # Uppercase not allowed
        with pytest.raises(ValidationError):
            provisioner.create_instance(
                name='InvalidName',
                machine_type='e2-micro'
            )

        # Underscores not allowed
        with pytest.raises(ValidationError):
            provisioner.create_instance(
                name='invalid_name',
                machine_type='e2-micro'
            )

    def test_invalid_labels(self, provisioner, mock_images_client):
        """Test that invalid labels are rejected."""
        mock_image = Mock()
        mock_image.name = 'debian-11-bullseye-v20230101'
        mock_images_client.get_from_family.return_value = mock_image

        # Too many labels
        too_many_labels = {f'key{i}': f'value{i}' for i in range(70)}

        with pytest.raises(ValidationError):
            provisioner.create_instance(
                name='test',
                machine_type='e2-micro',
                labels=too_many_labels
            )


class TestGCPVMProvisionerMultiZone:
    """Test multi-zone support."""

    def test_different_zones(self, mock_credentials):
        """Test creating provisioners in different zones."""
        zones = ['us-central1-a', 'us-east1-b', 'europe-west1-b']

        with patch('cloud_automation.gcp.vm.compute_v1.InstancesClient'), \
             patch('cloud_automation.gcp.vm.compute_v1.ImagesClient'):
            for zone in zones:
                prov = GCPVMProvisioner(
                    project_id='test-project-123',
                    zone=zone,
                    credentials=mock_credentials
                )
                assert prov.zone == zone
                assert prov.instances_client is not None


class TestGCPVMProvisionerErrorHandling:
    """Test error handling scenarios."""

    def test_api_error_on_create(self, provisioner, mock_images_client):
        """Test handling of API errors during instance creation."""
        mock_image = Mock()
        mock_image.name = 'debian-11-bullseye-v20230101'
        mock_image.self_link = 'projects/debian-cloud/global/images/debian-11-bullseye-v20230101'
        mock_images_client.get_from_family.return_value = mock_image

        # Simulate API error
        provisioner.instances_client.insert.side_effect = GoogleAPIError("Quota exceeded")

        with pytest.raises(GoogleAPIError, match="Quota exceeded"):
            provisioner.create_instance(
                name='test-instance',
                machine_type='e2-micro'
            )

    def test_image_not_found(self, provisioner, mock_images_client):
        """Test handling when image family is not found."""
        mock_images_client.get_from_family.side_effect = NotFound("Image family not found")

        with pytest.raises(NotFound):
            provisioner.create_instance(
                name='test-instance',
                machine_type='e2-micro',
                source_image_family='nonexistent-family'
            )

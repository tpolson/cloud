"""Web UI for Cloud Automation Tool."""

import streamlit as st
import sys
from pathlib import Path

from cloud_automation.aws.vm import AWSVMProvisioner
from cloud_automation.aws.storage import AWSStorageProvisioner
from cloud_automation.gcp.vm import GCPVMProvisioner
from cloud_automation.gcp.storage import GCPStorageProvisioner
from streamlit_helpers import (
    initialize_session_state,
    get_aws_credentials,
    get_gcp_credentials,
    get_aws_region,
    get_gcp_project_id,
    get_gcp_zone
)

# Page configuration
st.set_page_config(
    page_title="Cloud Automation",
    page_icon="☁️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        background-color: #d4edda;
        border-left: 5px solid #28a745;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        background-color: #f8d7da;
        border-left: 5px solid #dc3545;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        background-color: #d1ecf1;
        border-left: 5px solid #17a2b8;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state with credentials
initialize_session_state()

# Initialize provisioning history
if 'provisioning_history' not in st.session_state:
    st.session_state.provisioning_history = []

# Header
st.markdown('<h1 class="main-header">☁️ Cloud Automation Tool</h1>', unsafe_allow_html=True)
st.info("💡 **Quick Start**: Configure your credentials in **Settings** → Provision resources here → Manage VMs in **VM Management**")
st.markdown("---")

# Sidebar - Provider Selection
with st.sidebar:
    st.header("⚙️ Configuration")

    provider = st.selectbox(
        "Select Cloud Provider",
        ["AWS", "Google Cloud Platform (GCP)"],
        help="Choose your cloud provider"
    )

    resource_type = st.selectbox(
        "Resource Type",
        ["Virtual Machine (VM)", "Storage"],
        help="Choose what you want to provision"
    )

    st.markdown("---")
    st.info("💡 **Tip**: Configure your cloud credentials in the **Settings** page (sidebar navigation) before provisioning!")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    # AWS Configuration
    if provider == "AWS":
        st.header("🔶 AWS Configuration")

        # Common AWS settings
        aws_region = st.selectbox(
            "AWS Region",
            ["us-east-1", "us-east-2", "us-west-1", "us-west-2",
             "eu-west-1", "eu-central-1", "ap-southeast-1", "ap-northeast-1"],
            help="Select the AWS region"
        )

        if resource_type == "Virtual Machine (VM)":
            st.subheader("EC2 Instance Configuration")

            # Show selected image if available
            if 'selected_aws_image' in st.session_state and st.session_state.selected_aws_image:
                st.success(f"✅ Using selected AMI: `{st.session_state.selected_aws_image}`")
                if st.button("🖼️ Change Image", key="change_aws_image"):
                    st.info("Go to Image Browser to select a different AMI")
            else:
                st.info("💡 Browse and select an AMI in the **Image Browser** page, or enter one manually below")

            with st.form("aws_vm_form"):
                instance_name = st.text_input(
                    "Instance Name",
                    placeholder="my-server",
                    help="Name for your EC2 instance"
                )

                instance_type = st.selectbox(
                    "Instance Type",
                    ["t2.micro", "t2.small", "t2.medium", "t3.micro",
                     "t3.small", "t3.medium", "t3.large"],
                    help="Choose instance size"
                )

                col_a, col_b = st.columns(2)
                with col_a:
                    # Pre-fill with selected image if available
                    default_ami = st.session_state.get('selected_aws_image', '')
                    ami_id = st.text_input(
                        "AMI ID (Optional)",
                        value=default_ami,
                        placeholder="ami-xxxxx",
                        help="Leave empty to use latest Amazon Linux 2, or select from Image Browser"
                    )
                with col_b:
                    key_name = st.text_input(
                        "SSH Key Pair (Optional)",
                        placeholder="my-key-pair",
                        help="SSH key for access"
                    )

                # Tags
                st.write("**Tags (Optional)**")
                tag_col1, tag_col2 = st.columns(2)
                with tag_col1:
                    tag_env = st.text_input("Environment", placeholder="production")
                with tag_col2:
                    tag_app = st.text_input("Application", placeholder="web-server")

                submit_vm = st.form_submit_button("🚀 Provision EC2 Instance", use_container_width=True)

                if submit_vm:
                    if not instance_name:
                        st.error("❌ Instance name is required!")
                    else:
                        with st.spinner("Creating EC2 instance..."):
                            try:
                                aws_creds = get_aws_credentials()
                                provisioner = AWSVMProvisioner(region=aws_region, **aws_creds)

                                tags = {}
                                if tag_env:
                                    tags["Environment"] = tag_env
                                if tag_app:
                                    tags["Application"] = tag_app

                                result = provisioner.create_instance(
                                    name=instance_name,
                                    instance_type=instance_type,
                                    ami=ami_id if ami_id else None,
                                    key_name=key_name if key_name else None,
                                    tags=tags if tags else None
                                )

                                st.success(f"✅ Successfully created EC2 instance: {result['instance_id']}")
                                if result.get('public_ip'):
                                    st.info(f"🌐 Public IP: {result['public_ip']}")

                                # Add to history
                                st.session_state.provisioning_history.append({
                                    'provider': 'AWS',
                                    'type': 'EC2',
                                    'name': instance_name,
                                    'details': result
                                })

                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")

        else:  # Storage
            st.subheader("AWS Storage Configuration")

            storage_tab1, storage_tab2 = st.tabs(["S3 Bucket", "EBS Volume"])

            with storage_tab1:
                with st.form("aws_s3_form"):
                    bucket_name = st.text_input(
                        "Bucket Name",
                        placeholder="my-unique-bucket-name",
                        help="Must be globally unique and lowercase"
                    )

                    col_s1, col_s2 = st.columns(2)
                    with col_s1:
                        versioning = st.checkbox("Enable Versioning", value=False)
                    with col_s2:
                        encryption = st.checkbox("Enable Encryption", value=True)

                    submit_s3 = st.form_submit_button("🚀 Create S3 Bucket", use_container_width=True)

                    if submit_s3:
                        if not bucket_name:
                            st.error("❌ Bucket name is required!")
                        else:
                            with st.spinner("Creating S3 bucket..."):
                                try:
                                    aws_creds = get_aws_credentials()
                                    provisioner = AWSStorageProvisioner(region=aws_region, **aws_creds)
                                    result = provisioner.create_s3_bucket(
                                        bucket_name=bucket_name,
                                        versioning=versioning,
                                        encryption=encryption
                                    )
                                    st.success(f"✅ Successfully created S3 bucket: {bucket_name}")
                                    st.session_state.provisioning_history.append({
                                        'provider': 'AWS',
                                        'type': 'S3',
                                        'name': bucket_name,
                                        'details': result
                                    })
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")

            with storage_tab2:
                with st.form("aws_ebs_form"):
                    volume_name = st.text_input(
                        "Volume Name",
                        placeholder="my-data-volume"
                    )

                    col_e1, col_e2 = st.columns(2)
                    with col_e1:
                        volume_size = st.number_input("Size (GB)", min_value=1, max_value=16384, value=100)
                    with col_e2:
                        volume_type = st.selectbox(
                            "Volume Type",
                            ["gp3", "gp2", "io1", "io2", "st1", "sc1"]
                        )

                    submit_ebs = st.form_submit_button("🚀 Create EBS Volume", use_container_width=True)

                    if submit_ebs:
                        if not volume_name:
                            st.error("❌ Volume name is required!")
                        else:
                            with st.spinner("Creating EBS volume..."):
                                try:
                                    aws_creds = get_aws_credentials()
                                    provisioner = AWSStorageProvisioner(region=aws_region, **aws_creds)
                                    result = provisioner.create_ebs_volume(
                                        name=volume_name,
                                        size=volume_size,
                                        volume_type=volume_type
                                    )
                                    st.success(f"✅ Successfully created EBS volume: {result['volume_id']}")
                                    st.session_state.provisioning_history.append({
                                        'provider': 'AWS',
                                        'type': 'EBS',
                                        'name': volume_name,
                                        'details': result
                                    })
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")

    # GCP Configuration
    else:  # GCP
        st.header("🔷 Google Cloud Platform Configuration")

        # Common GCP settings
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            gcp_project = st.text_input(
                "GCP Project ID",
                placeholder="my-project-id",
                help="Your GCP project ID"
            )
        with col_g2:
            gcp_zone = st.selectbox(
                "Zone",
                ["us-central1-a", "us-central1-b", "us-east1-b", "us-west1-a",
                 "europe-west1-b", "asia-east1-a"],
                help="Select the GCP zone"
            )

        if resource_type == "Virtual Machine (VM)":
            st.subheader("Compute Engine Instance Configuration")

            # Show selected image if available
            if 'selected_gcp_image' in st.session_state and st.session_state.selected_gcp_image:
                img_info = st.session_state.selected_gcp_image
                if 'family' in img_info:
                    st.success(f"✅ Using selected image: Family `{img_info['family']}` from `{img_info['project']}`")
                else:
                    st.success(f"✅ Using selected image: `{img_info['name']}` from `{img_info['project']}`")
                if st.button("🖼️ Change Image", key="change_gcp_image"):
                    st.info("Go to Image Browser to select a different image")
            else:
                st.info("💡 Browse and select an image in the **Image Browser** page, or choose from defaults below")

            with st.form("gcp_vm_form"):
                instance_name = st.text_input(
                    "Instance Name",
                    placeholder="my-server",
                    help="Name for your GCE instance (lowercase, hyphens only)"
                )

                machine_type = st.selectbox(
                    "Machine Type",
                    ["e2-micro", "e2-small", "e2-medium", "n1-standard-1",
                     "n1-standard-2", "n2-standard-2"],
                    help="Choose machine size"
                )

                col_gc1, col_gc2 = st.columns(2)
                with col_gc1:
                    # If image selected from browser, show it as info only
                    if 'selected_gcp_image' in st.session_state and st.session_state.selected_gcp_image:
                        selected_img = st.session_state.selected_gcp_image
                        if 'family' in selected_img:
                            st.info(f"Using family: {selected_img['family']}")
                            image_family = selected_img['family']
                        else:
                            st.info(f"Using image: {selected_img['name']}")
                            image_family = None
                    else:
                        image_family = st.selectbox(
                            "Image Family",
                            ["debian-11", "ubuntu-2004-lts", "centos-7", "rocky-linux-8"],
                            help="Operating system"
                        )
                with col_gc2:
                    disk_size = st.number_input("Boot Disk Size (GB)", min_value=10, max_value=500, value=10)

                external_ip = st.checkbox("Assign External IP", value=True)

                # Labels
                st.write("**Labels (Optional)**")
                label_col1, label_col2 = st.columns(2)
                with label_col1:
                    label_env = st.text_input("environment", placeholder="production")
                with label_col2:
                    label_app = st.text_input("application", placeholder="web-server")

                submit_gcp_vm = st.form_submit_button("🚀 Provision GCE Instance", use_container_width=True)

                if submit_gcp_vm:
                    if not gcp_project:
                        st.error("❌ GCP Project ID is required!")
                    elif not instance_name:
                        st.error("❌ Instance name is required!")
                    else:
                        with st.spinner("Creating GCE instance..."):
                            try:
                                gcp_creds = get_gcp_credentials()
                                provisioner = GCPVMProvisioner(
                                    project_id=gcp_project,
                                    zone=gcp_zone,
                                    credentials=gcp_creds
                                )

                                labels = {}
                                if label_env:
                                    labels["environment"] = label_env
                                if label_app:
                                    labels["application"] = label_app

                                # Determine image source
                                if 'selected_gcp_image' in st.session_state and st.session_state.selected_gcp_image:
                                    selected_img = st.session_state.selected_gcp_image
                                    if 'family' in selected_img:
                                        # Use image family
                                        result = provisioner.create_instance(
                                            name=instance_name,
                                            machine_type=machine_type,
                                            source_image_family=selected_img['family'],
                                            source_image_project=selected_img['project'],
                                            disk_size_gb=disk_size,
                                            external_ip=external_ip,
                                            labels=labels if labels else None
                                        )
                                    else:
                                        # Use specific image name
                                        result = provisioner.create_instance(
                                            name=instance_name,
                                            machine_type=machine_type,
                                            source_image_family=selected_img['name'],
                                            source_image_project=selected_img['project'],
                                            disk_size_gb=disk_size,
                                            external_ip=external_ip,
                                            labels=labels if labels else None
                                        )
                                else:
                                    # Use default image family
                                    result = provisioner.create_instance(
                                        name=instance_name,
                                        machine_type=machine_type,
                                        source_image_family=image_family if image_family else "debian-11",
                                        disk_size_gb=disk_size,
                                        external_ip=external_ip,
                                        labels=labels if labels else None
                                    )

                                st.success(f"✅ Successfully created GCE instance: {instance_name}")
                                if result.get('external_ip'):
                                    st.info(f"🌐 External IP: {result['external_ip']}")

                                st.session_state.provisioning_history.append({
                                    'provider': 'GCP',
                                    'type': 'GCE',
                                    'name': instance_name,
                                    'details': result
                                })

                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")

        else:  # Storage
            st.subheader("GCP Storage Configuration")

            storage_tab1, storage_tab2 = st.tabs(["Cloud Storage Bucket", "Persistent Disk"])

            with storage_tab1:
                with st.form("gcp_bucket_form"):
                    bucket_name = st.text_input(
                        "Bucket Name",
                        placeholder="my-unique-bucket-name",
                        help="Must be globally unique and lowercase"
                    )

                    col_gb1, col_gb2 = st.columns(2)
                    with col_gb1:
                        location = st.selectbox(
                            "Location",
                            ["US", "EU", "ASIA", "us-central1", "europe-west1"]
                        )
                    with col_gb2:
                        storage_class = st.selectbox(
                            "Storage Class",
                            ["STANDARD", "NEARLINE", "COLDLINE", "ARCHIVE"]
                        )

                    versioning_gcp = st.checkbox("Enable Versioning", value=False)

                    submit_gcp_bucket = st.form_submit_button("🚀 Create Cloud Storage Bucket", use_container_width=True)

                    if submit_gcp_bucket:
                        if not gcp_project:
                            st.error("❌ GCP Project ID is required!")
                        elif not bucket_name:
                            st.error("❌ Bucket name is required!")
                        else:
                            with st.spinner("Creating Cloud Storage bucket..."):
                                try:
                                    gcp_creds = get_gcp_credentials()
                                    provisioner = GCPStorageProvisioner(
                                        project_id=gcp_project,
                                        zone=gcp_zone,
                                        credentials=gcp_creds
                                    )
                                    result = provisioner.create_bucket(
                                        bucket_name=bucket_name,
                                        location=location,
                                        storage_class=storage_class,
                                        versioning=versioning_gcp
                                    )
                                    st.success(f"✅ Successfully created Cloud Storage bucket: {bucket_name}")
                                    st.session_state.provisioning_history.append({
                                        'provider': 'GCP',
                                        'type': 'Cloud Storage',
                                        'name': bucket_name,
                                        'details': result
                                    })
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")

            with storage_tab2:
                with st.form("gcp_disk_form"):
                    disk_name = st.text_input(
                        "Disk Name",
                        placeholder="my-data-disk"
                    )

                    col_gd1, col_gd2 = st.columns(2)
                    with col_gd1:
                        disk_size_gcp = st.number_input("Size (GB)", min_value=10, max_value=65536, value=100)
                    with col_gd2:
                        disk_type = st.selectbox(
                            "Disk Type",
                            ["pd-standard", "pd-ssd", "pd-balanced"]
                        )

                    submit_gcp_disk = st.form_submit_button("🚀 Create Persistent Disk", use_container_width=True)

                    if submit_gcp_disk:
                        if not gcp_project:
                            st.error("❌ GCP Project ID is required!")
                        elif not disk_name:
                            st.error("❌ Disk name is required!")
                        else:
                            with st.spinner("Creating Persistent Disk..."):
                                try:
                                    gcp_creds = get_gcp_credentials()
                                    provisioner = GCPStorageProvisioner(
                                        project_id=gcp_project,
                                        zone=gcp_zone,
                                        credentials=gcp_creds
                                    )
                                    result = provisioner.create_disk(
                                        disk_name=disk_name,
                                        size_gb=disk_size_gcp,
                                        disk_type=disk_type
                                    )
                                    st.success(f"✅ Successfully created Persistent Disk: {disk_name}")
                                    st.session_state.provisioning_history.append({
                                        'provider': 'GCP',
                                        'type': 'Persistent Disk',
                                        'name': disk_name,
                                        'details': result
                                    })
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")

# Right column - Provisioning History
with col2:
    st.header("📜 History")

    if st.session_state.provisioning_history:
        for i, item in enumerate(reversed(st.session_state.provisioning_history[-10:])):
            with st.expander(f"{item['provider']} - {item['type']}: {item['name']}", expanded=False):
                st.json(item['details'])

        if st.button("🗑️ Clear History", use_container_width=True):
            st.session_state.provisioning_history = []
            st.rerun()
    else:
        st.info("No provisioning history yet. Create your first resource!")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>Cloud Automation Tool | Built with ❤️ using Streamlit</p>
        <p>Configure your cloud credentials in the Settings page or use environment credentials.</p>
    </div>
    """,
    unsafe_allow_html=True
)

"""Web UI for Cloud Automation Tool."""

import streamlit as st
import sys
from pathlib import Path

from cloud_automation.aws.vm import AWSVMProvisioner
from cloud_automation.aws.storage import AWSStorageProvisioner
from cloud_automation.gcp.vm import GCPVMProvisioner
from cloud_automation.gcp.storage import GCPStorageProvisioner
from cloud_automation.templates import (
    TemplateManager,
    create_aws_vm_template,
    create_gcp_vm_template,
    create_aws_storage_template,
    create_gcp_storage_template
)
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

# Initialize template manager
template_mgr = TemplateManager()

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

    # Template Management Section
    st.markdown("---")
    st.subheader("📋 Configuration Templates")

    template_action = st.radio(
        "Template Action",
        ["Load Template", "Save Current as Template", "Manage Templates"],
        horizontal=False,
        key="template_action"
    )

    if template_action == "Load Template":
        # List available templates for current provider
        provider_key = "aws" if provider == "AWS" else "gcp"
        templates = template_mgr.list_templates(provider=provider_key)

        if templates:
            template_names = [t['name'] for t in templates]
            selected_template = st.selectbox(
                "Select Template",
                template_names,
                key="selected_template"
            )

            if st.button("📥 Load Template", use_container_width=True):
                try:
                    loaded = template_mgr.load_template(selected_template, provider_key)
                    st.session_state.loaded_template = loaded['config']
                    st.session_state.template_loaded = True
                    st.success(f"✅ Loaded template: {selected_template}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to load template: {e}")
        else:
            st.info(f"No {provider_key.upper()} templates saved yet")

    elif template_action == "Save Current as Template":
        with st.form("save_template_form"):
            template_name = st.text_input(
                "Template Name",
                placeholder="e.g., Web Server Standard",
                help="Give your template a descriptive name"
            )
            template_desc = st.text_area(
                "Description (Optional)",
                placeholder="Describe this configuration...",
                height=80
            )

            save_template_btn = st.form_submit_button("💾 Save Template", use_container_width=True)

            if save_template_btn:
                if not template_name:
                    st.error("❌ Template name is required")
                else:
                    st.session_state.save_template_name = template_name
                    st.session_state.save_template_desc = template_desc
                    st.session_state.save_template_trigger = True
                    st.info("✅ Fill in the form below and the template will be saved")

    elif template_action == "Manage Templates":
        provider_key = "aws" if provider == "AWS" else "gcp"
        templates = template_mgr.list_templates(provider=provider_key)

        if templates:
            st.write(f"**{len(templates)} template(s) found:**")

            for template in templates:
                col_t1, col_t2 = st.columns([3, 1])
                with col_t1:
                    st.write(f"**{template['name']}**")
                    if template['description']:
                        st.caption(template['description'])
                with col_t2:
                    if st.button("🗑️ Delete", key=f"delete_{template['name']}", use_container_width=True):
                        try:
                            template_mgr.delete_template(template['name'], provider_key)
                            st.success(f"✅ Deleted: {template['name']}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error: {e}")

                st.markdown("---")
        else:
            st.info(f"No {provider_key.upper()} templates saved yet")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    # AWS Configuration
    if provider == "AWS":
        st.header("🔶 AWS Configuration")

        # Check for loaded template
        loaded_template = st.session_state.get('loaded_template', {})
        template_loaded = st.session_state.get('template_loaded', False)

        if template_loaded:
            col_info1, col_info2 = st.columns([3, 1])
            with col_info1:
                st.info("✅ Template loaded - form fields pre-filled below")
            with col_info2:
                if st.button("🗑️ Clear", key="clear_aws_template"):
                    st.session_state.loaded_template = {}
                    st.session_state.template_loaded = False
                    st.rerun()

        # Common AWS settings
        default_region = loaded_template.get('region', 'us-east-1') if loaded_template else 'us-east-1'
        region_options = ["us-east-1", "us-east-2", "us-west-1", "us-west-2",
                          "eu-west-1", "eu-central-1", "ap-southeast-1", "ap-northeast-1"]
        region_index = region_options.index(default_region) if default_region in region_options else 0

        aws_region = st.selectbox(
            "AWS Region",
            region_options,
            index=region_index,
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
                # Pre-fill from template if loaded
                vm_config = loaded_template.get('vm', {}) if template_loaded else {}

                instance_name = st.text_input(
                    "Instance Name",
                    value=vm_config.get('name', ''),
                    placeholder="my-server",
                    help="Name for your EC2 instance"
                )

                # Instance type selection with template default
                instance_type_options = ["t2.micro", "t2.small", "t2.medium", "t3.micro",
                                         "t3.small", "t3.medium", "t3.large"]
                template_instance_type = vm_config.get('instance_type')
                instance_type_index = instance_type_options.index(template_instance_type) if template_instance_type in instance_type_options else 0

                instance_type = st.selectbox(
                    "Instance Type",
                    instance_type_options,
                    index=instance_type_index,
                    help="Choose instance size"
                )

                col_a, col_b = st.columns(2)
                with col_a:
                    # Pre-fill with template or selected image
                    default_ami = vm_config.get('ami') or st.session_state.get('selected_aws_image', '')
                    ami_id = st.text_input(
                        "AMI ID (Optional)",
                        value=default_ami,
                        placeholder="ami-xxxxx",
                        help="Leave empty to use latest Amazon Linux 2, or select from Image Browser"
                    )
                with col_b:
                    key_name = st.text_input(
                        "SSH Key Pair (Optional)",
                        value=vm_config.get('key_name', ''),
                        placeholder="my-key-pair",
                        help="SSH key for access"
                    )

                # Tags
                st.write("**Tags (Optional)**")
                template_tags = vm_config.get('tags', {})
                tag_col1, tag_col2 = st.columns(2)
                with tag_col1:
                    tag_env = st.text_input("Environment", value=template_tags.get('Environment', ''), placeholder="production")
                with tag_col2:
                    tag_app = st.text_input("Application", value=template_tags.get('Application', ''), placeholder="web-server")

                # Spot instance option
                spot_instance = st.checkbox(
                    "💰 Request Spot Instance (up to 70% cost savings)",
                    value=vm_config.get('spot_instance', False),
                    help="Spot instances can be interrupted by AWS with 2-minute notice. Good for fault-tolerant workloads."
                )

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
                                    tags=tags if tags else None,
                                    spot_instance=spot_instance
                                )

                                instance_type_desc = "spot instance" if spot_instance else "instance"
                                st.success(f"✅ Successfully created EC2 {instance_type_desc}: {result['instance_id']}")
                                if spot_instance:
                                    st.info("💰 Spot instance requested - savings up to 70% vs on-demand pricing")
                                if result.get('public_ip'):
                                    st.info(f"🌐 Public IP: {result['public_ip']}")

                                # Add to history
                                st.session_state.provisioning_history.append({
                                    'provider': 'AWS',
                                    'type': 'EC2',
                                    'name': instance_name,
                                    'details': result
                                })

                                # Save template if requested
                                if st.session_state.get('save_template_trigger'):
                                    template_config = create_aws_vm_template(
                                        name=instance_name,
                                        instance_type=instance_type,
                                        region=aws_region,
                                        ami=ami_id if ami_id else None,
                                        key_name=key_name if key_name else None,
                                        tags=tags if tags else None,
                                        spot_instance=spot_instance
                                    )
                                    template_mgr.save_template(
                                        name=st.session_state.save_template_name,
                                        provider="aws",
                                        config=template_config,
                                        description=st.session_state.get('save_template_desc', '')
                                    )
                                    st.success(f"💾 Template saved: {st.session_state.save_template_name}")
                                    st.session_state.save_template_trigger = False

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

                # Spot VM option
                spot_vm = st.checkbox(
                    "💰 Use Spot VM (up to 91% cost savings)",
                    value=False,
                    help="Spot VMs can be preempted by GCP with 30-second notice. Ideal for fault-tolerant workloads."
                )

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
                                            labels=labels if labels else None,
                                            spot_vm=spot_vm
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
                                            labels=labels if labels else None,
                                            spot_vm=spot_vm
                                        )
                                else:
                                    # Use default image family
                                    result = provisioner.create_instance(
                                        name=instance_name,
                                        machine_type=machine_type,
                                        source_image_family=image_family if image_family else "debian-11",
                                        disk_size_gb=disk_size,
                                        external_ip=external_ip,
                                        labels=labels if labels else None,
                                        spot_vm=spot_vm
                                    )

                                vm_type_desc = "Spot VM" if spot_vm else "instance"
                                st.success(f"✅ Successfully created GCE {vm_type_desc}: {instance_name}")
                                if spot_vm:
                                    st.info("💰 Spot VM requested - savings up to 91% vs standard pricing")
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

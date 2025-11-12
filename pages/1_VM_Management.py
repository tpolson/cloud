"""VM Management Page for Cloud Automation Tool."""

import streamlit as st
import subprocess
import platform
from cloud_automation.aws.vm import AWSVMProvisioner
from cloud_automation.aws.storage import AWSStorageProvisioner
from cloud_automation.gcp.vm import GCPVMProvisioner
from cloud_automation.gcp.storage import GCPStorageProvisioner
from streamlit_helpers import (
    get_aws_credentials,
    get_gcp_credentials,
    get_aws_region,
    get_gcp_project_id,
    get_gcp_zone
)
from cloud_automation.credential_store import CredentialStore

# Page configuration
st.set_page_config(
    page_title="VM Management - Cloud Automation",
    page_icon="🖥️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize credential store and load saved credentials
if 'credential_store' not in st.session_state:
    st.session_state.credential_store = CredentialStore()

# Initialize session state for credentials - load from disk if available
if 'aws_credentials' not in st.session_state:
    stored_creds = st.session_state.credential_store.load_credentials()
    if stored_creds and 'aws_credentials' in stored_creds:
        st.session_state.aws_credentials = stored_creds['aws_credentials']
    else:
        st.session_state.aws_credentials = {
            'access_key_id': '',
            'secret_access_key': '',
            'region': 'us-east-1'
        }

if 'gcp_credentials' not in st.session_state:
    stored_creds = st.session_state.credential_store.load_credentials()
    if stored_creds and 'gcp_credentials' in stored_creds:
        st.session_state.gcp_credentials = stored_creds['gcp_credentials']
    else:
        st.session_state.gcp_credentials = {
            'project_id': '',
            'service_account_json': None,
            'zone': 'us-central1-a'
        }

st.markdown('<h1 class="main-header">🖥️ Virtual Machine Management</h1>', unsafe_allow_html=True)
st.markdown("---")

# Sidebar - Provider Selection
with st.sidebar:
    st.header("⚙️ Configuration")

    provider = st.selectbox(
        "Cloud Provider",
        ["AWS", "Google Cloud Platform (GCP)"],
        help="Choose your cloud provider"
    )

    if provider == "AWS":
        aws_region = st.selectbox(
            "AWS Region",
            ["us-east-1", "us-east-2", "us-west-1", "us-west-2",
             "eu-west-1", "eu-central-1", "ap-southeast-1", "ap-northeast-1"],
            help="Select the AWS region"
        )
    else:
        col1, col2 = st.columns(2)
        with col1:
            gcp_project = st.text_input(
                "GCP Project ID",
                placeholder="my-project-id",
                help="Your GCP project ID"
            )
        with col2:
            gcp_zone = st.selectbox(
                "Zone",
                ["us-central1-a", "us-central1-b", "us-east1-b", "us-west1-a",
                 "europe-west1-b", "asia-east1-a"],
                help="Select the GCP zone"
            )

    st.markdown("---")
    if st.button("🔄 Refresh VM List", use_container_width=True):
        st.rerun()

# AWS VM Management
if provider == "AWS":
    st.header("🔶 AWS EC2 Instances")

    try:
        aws_creds = get_aws_credentials()
        provisioner = AWSVMProvisioner(region=aws_region, **aws_creds)
        instances = provisioner.list_instances()

        # Pre-fetch volumes once for all instances (fix N+1 query)
        storage_provisioner = AWSStorageProvisioner(region=aws_region, **aws_creds)
        all_volumes = storage_provisioner.list_ebs_volumes()
        available_volumes = [v for v in all_volumes if v['state'] == 'available']

        if not instances:
            st.info("No EC2 instances found in this region.")
        else:
            # Display instances in cards
            for instance in instances:
                status_color = {
                    'running': '🟢',
                    'stopped': '🔴',
                    'stopping': '🟡',
                    'pending': '🟡',
                    'terminated': '⚫',
                    'shutting-down': '🟡'
                }.get(instance['state'], '⚪')

                with st.expander(f"{status_color} {instance['name']} ({instance['instance_id']})", expanded=True):
                    col1, col2, col3 = st.columns([2, 2, 1])

                    with col1:
                        st.write("**Instance Details:**")
                        st.write(f"• **Type:** {instance['instance_type']}")
                        st.write(f"• **State:** {instance['state']}")
                        st.write(f"• **Public IP:** {instance['public_ip']}")
                        st.write(f"• **Private IP:** {instance['private_ip']}")

                    with col2:
                        st.write("**Storage Management:**")

                        # Get available volumes
                        storage_provisioner = AWSStorageProvisioner(region=aws_region, **aws_creds)
                        volumes = storage_provisioner.list_ebs_volumes()
                        available_volumes = [v for v in volumes if v['state'] == 'available']

                        if available_volumes:
                            volume_names = [f"{v['name']} ({v['volume_id']}) - {v['size']}GB"
                                          for v in available_volumes]
                            selected_volume = st.selectbox(
                                "Select volume to attach:",
                                ["-- Select --"] + volume_names,
                                key=f"vol_{instance['instance_id']}"
                            )

                            device_name = st.text_input(
                                "Device name:",
                                value="/dev/sdf",
                                key=f"dev_{instance['instance_id']}"
                            )

                            if st.button("📎 Attach Volume", key=f"attach_{instance['instance_id']}"):
                                if selected_volume != "-- Select --":
                                    volume_id = selected_volume.split('(')[1].split(')')[0]
                                    try:
                                        storage_provisioner.attach_volume(
                                            volume_id=volume_id,
                                            instance_id=instance['instance_id'],
                                            device=device_name
                                        )
                                        st.success(f"✅ Volume attached to {device_name}")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"❌ Failed to attach volume: {e}")
                        else:
                            st.info("No available volumes to attach")

                    with col3:
                        st.write("**Actions:**")

                        # Control buttons
                        if instance['state'] == 'running':
                            if st.button("⏸️ Stop", key=f"stop_{instance['instance_id']}", use_container_width=True):
                                try:
                                    with st.spinner("Stopping instance..."):
                                        provisioner.stop_instance(instance['instance_id'])
                                    st.success("Instance stopped")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

                            if st.button("🔄 Reboot", key=f"reboot_{instance['instance_id']}", use_container_width=True):
                                try:
                                    with st.spinner("Rebooting instance..."):
                                        provisioner.reboot_instance(instance['instance_id'])
                                    st.success("Instance rebooting")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

                            if instance['public_ip'] != 'N/A':
                                if st.button("🔐 SSH Login", key=f"ssh_{instance['instance_id']}", use_container_width=True):
                                    ssh_command = f"ssh ec2-user@{instance['public_ip']}"
                                    st.code(ssh_command, language="bash")
                                    st.info("💡 Copy and paste this command in your terminal to connect")

                        elif instance['state'] == 'stopped':
                            if st.button("▶️ Start", key=f"start_{instance['instance_id']}", use_container_width=True):
                                try:
                                    with st.spinner("Starting instance..."):
                                        provisioner.start_instance(instance['instance_id'])
                                    st.success("Instance starting")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

                        if instance['state'] in ['running', 'stopped']:
                            if st.button("🗑️ Terminate", key=f"term_{instance['instance_id']}",
                                       use_container_width=True, type="secondary"):
                                if st.session_state.get(f"confirm_term_{instance['instance_id']}", False):
                                    try:
                                        provisioner.terminate_instance(instance['instance_id'])
                                        st.success("Instance terminated")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                                else:
                                    st.session_state[f"confirm_term_{instance['instance_id']}"] = True
                                    st.warning("⚠️ Click again to confirm termination")

    except Exception as e:
        st.error(f"❌ Error loading instances: {e}")

# GCP VM Management
else:
    st.header("🔷 Google Compute Engine Instances")

    if not gcp_project:
        st.warning("⚠️ Please enter your GCP Project ID in the sidebar")
    else:
        try:
            gcp_creds = get_gcp_credentials()
            provisioner = GCPVMProvisioner(
                project_id=gcp_project,
                zone=gcp_zone,
                credentials=gcp_creds
            )
            instances = provisioner.list_instances()

            if not instances:
                st.info("No GCE instances found in this zone.")
            else:
                # Display instances in cards
                for instance in instances:
                    status_color = {
                        'RUNNING': '🟢',
                        'TERMINATED': '🔴',
                        'STOPPING': '🟡',
                        'PROVISIONING': '🟡',
                        'STAGING': '🟡',
                        'SUSPENDING': '🟡',
                        'SUSPENDED': '🔴'
                    }.get(instance['status'], '⚪')

                    with st.expander(f"{status_color} {instance['name']}", expanded=True):
                        col1, col2, col3 = st.columns([2, 2, 1])

                        with col1:
                            st.write("**Instance Details:**")
                            st.write(f"• **Machine Type:** {instance['machine_type']}")
                            st.write(f"• **Status:** {instance['status']}")
                            st.write(f"• **External IP:** {instance['external_ip']}")
                            st.write(f"• **Internal IP:** {instance['internal_ip']}")

                        with col2:
                            st.write("**Storage Management:**")

                            # Get available disks
                            storage_provisioner = GCPStorageProvisioner(
                                project_id=gcp_project,
                                zone=gcp_zone,
                                credentials=gcp_creds
                            )
                            disks = storage_provisioner.list_disks()
                            available_disks = [d for d in disks if d['status'] == 'READY']

                            if available_disks:
                                disk_names = [f"{d['name']} - {d['size_gb']}GB ({d['disk_type']})"
                                            for d in available_disks]
                                selected_disk = st.selectbox(
                                    "Select disk to attach:",
                                    ["-- Select --"] + disk_names,
                                    key=f"disk_{instance['name']}"
                                )

                                if st.button("📎 Attach Disk", key=f"attach_{instance['name']}"):
                                    if selected_disk != "-- Select --":
                                        disk_name = selected_disk.split(' - ')[0]
                                        try:
                                            storage_provisioner.attach_disk(
                                                instance_name=instance['name'],
                                                disk_name=disk_name
                                            )
                                            st.success(f"✅ Disk attached successfully")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"❌ Failed to attach disk: {e}")
                            else:
                                st.info("No available disks to attach")

                        with col3:
                            st.write("**Actions:**")

                            # Control buttons
                            if instance['status'] == 'RUNNING':
                                if st.button("⏸️ Stop", key=f"stop_{instance['name']}", use_container_width=True):
                                    try:
                                        with st.spinner("Stopping instance..."):
                                            provisioner.stop_instance(instance['name'])
                                        st.success("Instance stopped")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")

                                if st.button("🔄 Reboot", key=f"reboot_{instance['name']}", use_container_width=True):
                                    try:
                                        with st.spinner("Rebooting instance..."):
                                            provisioner.reboot_instance(instance['name'])
                                        st.success("Instance rebooting")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")

                                if instance['external_ip'] != 'N/A':
                                    if st.button("🔐 SSH Login", key=f"ssh_{instance['name']}", use_container_width=True):
                                        # GCP uses project metadata for SSH keys
                                        ssh_command = f"gcloud compute ssh {instance['name']} --zone={gcp_zone} --project={gcp_project}"
                                        st.code(ssh_command, language="bash")
                                        st.info("💡 Or use: ssh username@" + instance['external_ip'])

                            elif instance['status'] == 'TERMINATED':
                                if st.button("▶️ Start", key=f"start_{instance['name']}", use_container_width=True):
                                    try:
                                        with st.spinner("Starting instance..."):
                                            provisioner.start_instance(instance['name'])
                                        st.success("Instance starting")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")

                            if instance['status'] in ['RUNNING', 'TERMINATED']:
                                if st.button("🗑️ Delete", key=f"del_{instance['name']}",
                                           use_container_width=True, type="secondary"):
                                    if st.session_state.get(f"confirm_del_{instance['name']}", False):
                                        try:
                                            provisioner.delete_instance(instance['name'])
                                            st.success("Instance deleted")
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error: {e}")
                                    else:
                                        st.session_state[f"confirm_del_{instance['name']}"] = True
                                        st.warning("⚠️ Click again to confirm deletion")

        except Exception as e:
            st.error(f"❌ Error loading instances: {e}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>🖥️ VM Management | Control and monitor your cloud instances</p>
    </div>
    """,
    unsafe_allow_html=True
)

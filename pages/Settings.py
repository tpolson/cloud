"""Settings Page for Cloud Automation Tool - Credential Management."""

import streamlit as st
import json
import os
from pathlib import Path
from streamlit_helpers import initialize_session_state

# Page configuration
st.set_page_config(
    page_title="Settings - Cloud Automation",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown('<h1 class="main-header">⚙️ Settings & Credentials</h1>', unsafe_allow_html=True)
st.markdown("---")

# Initialize session state with credentials
initialize_session_state()

# Initialize persistence preference
if 'persist_credentials' not in st.session_state:
    st.session_state.persist_credentials = st.session_state.credential_store.credentials_exist()

# Check for existing credentials from environment
def check_aws_env_credentials():
    """Check if AWS credentials exist in environment."""
    return bool(os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'))

def check_gcp_env_credentials():
    """Check if GCP credentials exist in environment."""
    return bool(os.getenv('GOOGLE_APPLICATION_CREDENTIALS') or os.getenv('GOOGLE_CLOUD_PROJECT'))

# Sidebar
with st.sidebar:
    st.header("📋 Credential Status")

    # AWS Status
    aws_configured = (st.session_state.aws_credentials['access_key_id'] and
                     st.session_state.aws_credentials['secret_access_key']) or check_aws_env_credentials()

    if aws_configured:
        st.success("✅ AWS Configured")
    else:
        st.warning("⚠️ AWS Not Configured")

    # GCP Status
    gcp_configured = (st.session_state.gcp_credentials['service_account_json'] or
                     st.session_state.gcp_credentials['project_id']) or check_gcp_env_credentials()

    if gcp_configured:
        st.success("✅ GCP Configured")
    else:
        st.warning("⚠️ GCP Not Configured")

    st.markdown("---")

    # Persistence toggle
    st.subheader("💾 Credential Persistence")

    persist = st.checkbox(
        "Remember credentials",
        value=st.session_state.persist_credentials,
        help="Save encrypted credentials to disk (~/.cloud-automation/credentials.enc)"
    )

    if persist != st.session_state.persist_credentials:
        st.session_state.persist_credentials = persist
        if persist:
            # Save current credentials to disk
            try:
                creds = {
                    'aws_credentials': st.session_state.aws_credentials,
                    'gcp_credentials': st.session_state.gcp_credentials
                }
                st.session_state.credential_store.save_credentials(creds)
                st.success("✅ Credentials saved to disk")
            except Exception as e:
                st.error(f"❌ Failed to save: {e}")
        else:
            # Delete credentials from disk
            try:
                st.session_state.credential_store.delete_credentials()
                st.success("✅ Stored credentials deleted")
            except Exception as e:
                st.error(f"❌ Failed to delete: {e}")
        st.rerun()

    if st.session_state.credential_store.credentials_exist():
        st.info("📁 Credentials stored on disk")
    else:
        st.info("📁 No stored credentials")

    st.markdown("---")

    if st.button("🗑️ Clear All Credentials", use_container_width=True):
        # Clear session state
        st.session_state.aws_credentials = {
            'access_key_id': '',
            'secret_access_key': '',
            'region': 'us-east-1'
        }
        st.session_state.gcp_credentials = {
            'project_id': '',
            'service_account_json': None,
            'zone': 'us-central1-a'
        }

        # Clear disk storage if persistence is enabled
        if st.session_state.persist_credentials:
            try:
                st.session_state.credential_store.delete_credentials()
                st.session_state.persist_credentials = False
            except Exception as e:
                st.error(f"❌ Failed to clear stored credentials: {e}")

        st.success("All credentials cleared!")
        st.rerun()

# Main content
tab1, tab2, tab3 = st.tabs(["🔶 AWS Credentials", "🔷 GCP Credentials", "ℹ️ Information"])

# AWS Credentials Tab
with tab1:
    st.header("AWS Credentials Configuration")

    st.info("""
    💡 **How to get AWS credentials:**
    1. Log in to AWS Console
    2. Go to IAM → Users → Your User
    3. Security Credentials → Create Access Key
    4. Save both Access Key ID and Secret Access Key
    """)

    with st.form("aws_credentials_form"):
        aws_access_key = st.text_input(
            "AWS Access Key ID",
            value=st.session_state.aws_credentials['access_key_id'],
            type="password",
            help="Your AWS Access Key ID",
            placeholder="AKIAIOSFODNN7EXAMPLE"
        )

        aws_secret_key = st.text_input(
            "AWS Secret Access Key",
            value=st.session_state.aws_credentials['secret_access_key'],
            type="password",
            help="Your AWS Secret Access Key",
            placeholder="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
        )

        aws_region = st.selectbox(
            "Default AWS Region",
            ["us-east-1", "us-east-2", "us-west-1", "us-west-2",
             "eu-west-1", "eu-west-2", "eu-central-1",
             "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
             "ca-central-1", "sa-east-1"],
            index=0 if not st.session_state.aws_credentials['region'] else
                  ["us-east-1", "us-east-2", "us-west-1", "us-west-2",
                   "eu-west-1", "eu-west-2", "eu-central-1",
                   "ap-southeast-1", "ap-southeast-2", "ap-northeast-1",
                   "ca-central-1", "sa-east-1"].index(st.session_state.aws_credentials['region'])
        )

        col1, col2 = st.columns(2)
        with col1:
            save_aws = st.form_submit_button("💾 Save AWS Credentials", use_container_width=True)
        with col2:
            test_aws = st.form_submit_button("🧪 Test Connection", use_container_width=True)

        if save_aws:
            if not aws_access_key or not aws_secret_key:
                st.error("❌ Please provide both Access Key ID and Secret Access Key")
            else:
                st.session_state.aws_credentials = {
                    'access_key_id': aws_access_key,
                    'secret_access_key': aws_secret_key,
                    'region': aws_region
                }

                # Save to disk if persistence is enabled
                if st.session_state.persist_credentials:
                    try:
                        creds = {
                            'aws_credentials': st.session_state.aws_credentials,
                            'gcp_credentials': st.session_state.gcp_credentials
                        }
                        st.session_state.credential_store.save_credentials(creds)
                        st.success("✅ AWS credentials saved to memory and disk!")
                    except Exception as e:
                        st.error(f"❌ Failed to save to disk: {e}")
                else:
                    st.success("✅ AWS credentials saved to memory!")

                st.rerun()

        if test_aws:
            if not aws_access_key or not aws_secret_key:
                st.error("❌ Please provide credentials first")
            else:
                with st.spinner("Testing AWS connection..."):
                    try:
                        import boto3
                        from botocore.exceptions import ClientError, NoCredentialsError

                        # Create a session with provided credentials
                        session = boto3.Session(
                            aws_access_key_id=aws_access_key,
                            aws_secret_access_key=aws_secret_key,
                            region_name=aws_region
                        )

                        # Test connection by getting caller identity
                        sts = session.client('sts')
                        identity = sts.get_caller_identity()

                        st.success(f"✅ Connection successful!")
                        st.json({
                            "Account": identity['Account'],
                            "UserId": identity['UserId'],
                            "Arn": identity['Arn']
                        })
                    except NoCredentialsError:
                        st.error("❌ Invalid credentials")
                    except ClientError as e:
                        st.error(f"❌ Connection failed: {e}")
                    except Exception as e:
                        st.error(f"❌ Unexpected error: {e}")

    st.markdown("---")

    # Check for environment credentials
    if check_aws_env_credentials():
        st.info("""
        ℹ️ **Environment Credentials Detected**

        AWS credentials are available from your environment (AWS CLI configuration or environment variables).
        The credentials configured here will take precedence over environment credentials.
        """)

# GCP Credentials Tab
with tab2:
    st.header("Google Cloud Platform Credentials Configuration")

    st.info("""
    💡 **How to get GCP credentials:**
    1. Go to GCP Console → IAM & Admin → Service Accounts
    2. Create a service account or select existing one
    3. Create a JSON key
    4. Download the JSON key file
    5. Upload it here or paste the JSON content
    """)

    with st.form("gcp_credentials_form"):
        gcp_project = st.text_input(
            "GCP Project ID",
            value=st.session_state.gcp_credentials['project_id'],
            help="Your GCP project ID",
            placeholder="my-project-id-123456"
        )

        gcp_zone = st.selectbox(
            "Default Zone",
            ["us-central1-a", "us-central1-b", "us-central1-c",
             "us-east1-b", "us-east1-c", "us-east1-d",
             "us-west1-a", "us-west1-b", "us-west1-c",
             "europe-west1-b", "europe-west1-c", "europe-west1-d",
             "asia-east1-a", "asia-east1-b", "asia-east1-c"],
            index=0 if not st.session_state.gcp_credentials['zone'] else
                  ["us-central1-a", "us-central1-b", "us-central1-c",
                   "us-east1-b", "us-east1-c", "us-east1-d",
                   "us-west1-a", "us-west1-b", "us-west1-c",
                   "europe-west1-b", "europe-west1-c", "europe-west1-d",
                   "asia-east1-a", "asia-east1-b", "asia-east1-c"].index(st.session_state.gcp_credentials['zone'])
        )

        st.write("**Service Account Key (JSON)**")

        col1, col2 = st.columns([1, 1])
        with col1:
            uploaded_file = st.file_uploader(
                "Upload JSON Key File",
                type=['json'],
                help="Upload your service account JSON key file"
            )
        with col2:
            json_text = st.text_area(
                "Or Paste JSON Content",
                height=150,
                placeholder='{\n  "type": "service_account",\n  "project_id": "...",\n  ...\n}',
                help="Paste the content of your JSON key file"
            )

        col1, col2 = st.columns(2)
        with col1:
            save_gcp = st.form_submit_button("💾 Save GCP Credentials", use_container_width=True)
        with col2:
            test_gcp = st.form_submit_button("🧪 Test Connection", use_container_width=True)

        if save_gcp:
            if not gcp_project:
                st.error("❌ Please provide GCP Project ID")
            else:
                service_account_data = None

                # Try uploaded file first
                if uploaded_file:
                    try:
                        service_account_data = json.load(uploaded_file)
                    except json.JSONDecodeError:
                        st.error("❌ Invalid JSON file")
                        service_account_data = None
                # Try pasted JSON
                elif json_text:
                    try:
                        service_account_data = json.loads(json_text)
                    except json.JSONDecodeError:
                        st.error("❌ Invalid JSON content")
                        service_account_data = None

                if service_account_data or gcp_project:
                    st.session_state.gcp_credentials = {
                        'project_id': gcp_project,
                        'service_account_json': service_account_data,
                        'zone': gcp_zone
                    }

                    # Save to disk if persistence is enabled
                    if st.session_state.persist_credentials:
                        try:
                            creds = {
                                'aws_credentials': st.session_state.aws_credentials,
                                'gcp_credentials': st.session_state.gcp_credentials
                            }
                            st.session_state.credential_store.save_credentials(creds)
                            st.success("✅ GCP credentials saved to memory and disk!")
                        except Exception as e:
                            st.error(f"❌ Failed to save to disk: {e}")
                    else:
                        st.success("✅ GCP credentials saved to memory!")

                    st.rerun()

        if test_gcp:
            if not gcp_project:
                st.error("❌ Please provide GCP Project ID")
            else:
                with st.spinner("Testing GCP connection..."):
                    try:
                        from google.cloud import compute_v1
                        from google.oauth2 import service_account

                        # Get service account data
                        service_account_data = None
                        if uploaded_file:
                            service_account_data = json.load(uploaded_file)
                        elif json_text:
                            service_account_data = json.loads(json_text)

                        if service_account_data:
                            credentials = service_account.Credentials.from_service_account_info(
                                service_account_data
                            )
                            client = compute_v1.InstancesClient(credentials=credentials)
                        else:
                            # Try default credentials
                            client = compute_v1.InstancesClient()

                        # Test by listing zones (lightweight operation)
                        zones_client = compute_v1.ZonesClient(credentials=credentials if service_account_data else None)
                        zones = list(zones_client.list(project=gcp_project))

                        st.success(f"✅ Connection successful!")
                        st.json({
                            "Project": gcp_project,
                            "Available Zones": len(zones),
                            "Service Account": service_account_data.get('client_email', 'Default') if service_account_data else 'Default'
                        })
                    except Exception as e:
                        st.error(f"❌ Connection failed: {e}")

    st.markdown("---")

    # Check for environment credentials
    if check_gcp_env_credentials():
        st.info("""
        ℹ️ **Environment Credentials Detected**

        GCP credentials are available from your environment (gcloud auth or GOOGLE_APPLICATION_CREDENTIALS).
        The credentials configured here will take precedence over environment credentials.
        """)

# Information Tab
with tab3:
    st.header("About Credential Storage")

    st.markdown("""
    ### 🔒 Security Information

    **Important Security Considerations:**

    - 💾 Credentials can be saved to encrypted file on disk (optional)
    - 🔐 Encryption uses machine-specific key (username + hostname)
    - 📁 Stored in `~/.cloud-automation/credentials.enc` with 0600 permissions
    - 🔄 Without persistence, credentials are lost when you close the browser
    - 🚫 Never share your credentials or commit them to version control
    - ✅ Use IAM roles with minimal required permissions
    - 🔐 Rotate your credentials regularly

    ### 📝 How It Works

    1. **Session Storage**: Credentials are stored in Streamlit's session state
    2. **Optional Persistence**: Enable "Remember credentials" to save encrypted to disk
    3. **Auto-Load**: Saved credentials are automatically loaded on app start
    4. **Machine-Specific**: Encrypted credentials only work on the machine they were created on
    5. **Priority**: UI credentials take precedence over environment credentials
    6. **Fallback**: If UI credentials aren't set, environment credentials are used

    ### 🌍 Environment Variables (Alternative)

    Instead of using the UI, you can set credentials via environment variables:

    **AWS:**
    ```bash
    export AWS_ACCESS_KEY_ID="your-access-key"
    export AWS_SECRET_ACCESS_KEY="your-secret-key"
    export AWS_DEFAULT_REGION="us-east-1"
    ```

    **GCP:**
    ```bash
    export GOOGLE_APPLICATION_CREDENTIALS="/path/to/key.json"
    export GOOGLE_CLOUD_PROJECT="your-project-id"
    ```

    ### 🔧 AWS CLI Configuration

    ```bash
    aws configure
    ```

    ### 🔧 GCP CLI Configuration

    ```bash
    gcloud auth application-default login
    gcloud config set project your-project-id
    ```

    ### 📋 Recommended Permissions

    **AWS IAM Permissions:**
    - `ec2:*` for VM management
    - `s3:*` for storage management

    **GCP IAM Roles:**
    - `Compute Admin` for VM management
    - `Storage Admin` for storage management
    """)

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>⚙️ Settings | Manage your cloud provider credentials securely</p>
    </div>
    """,
    unsafe_allow_html=True
)

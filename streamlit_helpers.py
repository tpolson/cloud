"""Helper functions for Streamlit UI credential management."""

import streamlit as st
import boto3
from google.oauth2 import service_account
from cloud_automation.credential_store import CredentialStore


def initialize_session_state():
    """Initialize session state with credential store and load saved credentials.

    This function should be called at the beginning of each Streamlit page to ensure
    credentials are loaded from disk and available in session state.
    """
    # Initialize credential store
    if 'credential_store' not in st.session_state:
        st.session_state.credential_store = CredentialStore()

    # Initialize AWS credentials - load from disk if available
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

    # Initialize GCP credentials - load from disk if available
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


def get_aws_credentials():
    """Get AWS credentials from session state.

    Returns:
        dict: Kwargs to pass to boto3 client, or empty dict if using defaults
    """
    if 'aws_credentials' not in st.session_state:
        return {}

    creds = st.session_state.aws_credentials

    # Only return credentials if both key and secret are provided
    if creds.get('access_key_id') and creds.get('secret_access_key'):
        return {
            'aws_access_key_id': creds['access_key_id'],
            'aws_secret_access_key': creds['secret_access_key']
        }

    return {}


def get_gcp_credentials():
    """Get GCP credentials from session state.

    Returns:
        google.auth.credentials.Credentials or None: Credentials object or None for default
    """
    if 'gcp_credentials' not in st.session_state:
        return None

    creds = st.session_state.gcp_credentials
    service_account_json = creds.get('service_account_json')

    if service_account_json:
        try:
            return service_account.Credentials.from_service_account_info(
                service_account_json
            )
        except Exception:
            # Fall back to default credentials if there's an error
            return None

    return None


def get_aws_region():
    """Get AWS region from session state.

    Returns:
        str: AWS region or default 'us-east-1'
    """
    if 'aws_credentials' not in st.session_state:
        return 'us-east-1'

    return st.session_state.aws_credentials.get('region', 'us-east-1')


def get_gcp_project_id():
    """Get GCP project ID from session state.

    Returns:
        str: GCP project ID or empty string
    """
    if 'gcp_credentials' not in st.session_state:
        return ''

    return st.session_state.gcp_credentials.get('project_id', '')


def get_gcp_zone():
    """Get GCP zone from session state.

    Returns:
        str: GCP zone or default 'us-central1-a'
    """
    if 'gcp_credentials' not in st.session_state:
        return 'us-central1-a'

    return st.session_state.gcp_credentials.get('zone', 'us-central1-a')

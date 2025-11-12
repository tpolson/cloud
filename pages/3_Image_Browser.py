"""Image Browser Page for Cloud Automation Tool."""

import streamlit as st
from cloud_automation.aws.vm import AWSVMProvisioner
from cloud_automation.gcp.vm import GCPVMProvisioner
from streamlit_helpers import (
    initialize_session_state,
    get_aws_credentials,
    get_gcp_credentials,
    get_aws_region,
    get_gcp_project_id,
    get_gcp_zone
)

# Cached functions for image retrieval
@st.cache_data(ttl=300)  # 5 minute cache for images
def get_cached_aws_popular_images(region: str, access_key_id: str):
    """Cached retrieval of popular AWS images."""
    provisioner = AWSVMProvisioner(
        region=region,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=st.session_state.aws_credentials['secret_access_key']
    )
    return provisioner.get_popular_images()

@st.cache_data(ttl=300)  # 5 minute cache
def get_cached_aws_search(region: str, access_key_id: str, search_term: str, owner: str):
    """Cached AWS image search results."""
    provisioner = AWSVMProvisioner(
        region=region,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=st.session_state.aws_credentials['secret_access_key']
    )
    return provisioner.search_images(search_term, owner=owner)

@st.cache_data(ttl=300)  # 5 minute cache
def get_cached_aws_my_images(region: str, access_key_id: str):
    """Cached retrieval of user's custom AMIs."""
    provisioner = AWSVMProvisioner(
        region=region,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=st.session_state.aws_credentials['secret_access_key']
    )
    return provisioner.list_images(owners=['self'], max_results=50)

@st.cache_data(ttl=300)  # 5 minute cache
def get_cached_aws_all_images(region: str, access_key_id: str, owners: list):
    """Cached retrieval of all available images."""
    provisioner = AWSVMProvisioner(
        region=region,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=st.session_state.aws_credentials['secret_access_key']
    )
    return provisioner.list_images(owners=owners, max_results=100)

@st.cache_data(ttl=300)  # 5 minute cache
def get_cached_gcp_popular_images(project_id: str, zone: str):
    """Cached retrieval of popular GCP images."""
    gcp_creds = get_gcp_credentials()
    provisioner = GCPVMProvisioner(
        project_id=project_id,
        zone=zone,
        credentials=gcp_creds
    )
    return provisioner.get_popular_images()

@st.cache_data(ttl=300)  # 5 minute cache
def get_cached_gcp_search(project_id: str, zone: str, search_term: str, project_filter: str = None):
    """Cached GCP image search results."""
    gcp_creds = get_gcp_credentials()
    provisioner = GCPVMProvisioner(
        project_id=project_id,
        zone=zone,
        credentials=gcp_creds
    )
    return provisioner.search_images(search_term, project=project_filter)

@st.cache_data(ttl=300)  # 5 minute cache
def get_cached_gcp_my_images(project_id: str, zone: str):
    """Cached retrieval of user's custom GCP images."""
    gcp_creds = get_gcp_credentials()
    provisioner = GCPVMProvisioner(
        project_id=project_id,
        zone=zone,
        credentials=gcp_creds
    )
    return provisioner.list_images(project=project_id, max_results=50)

@st.cache_data(ttl=300)  # 5 minute cache
def get_cached_gcp_project_images(project_id: str, zone: str, target_project: str):
    """Cached retrieval of public project images."""
    gcp_creds = get_gcp_credentials()
    provisioner = GCPVMProvisioner(
        project_id=project_id,
        zone=zone,
        credentials=gcp_creds
    )
    return provisioner.list_images(project=target_project, max_results=50)

# Page configuration
st.set_page_config(
    page_title="Image Browser - Cloud Automation",
    page_icon="🖼️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state with credentials
initialize_session_state()

# Initialize selected images in session state
if 'selected_aws_image' not in st.session_state:
    st.session_state.selected_aws_image = None

if 'selected_gcp_image' not in st.session_state:
    st.session_state.selected_gcp_image = None

st.markdown('<h1 class="main-header">🖼️ Image Browser</h1>', unsafe_allow_html=True)
st.info("💡 Browse and select VM images (AMIs for AWS, Images for GCP) to use when provisioning instances")
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

    # Show selected image
    if provider == "AWS" and st.session_state.selected_aws_image:
        st.success("✅ AWS Image Selected")
        st.code(st.session_state.selected_aws_image, language="text")
    elif provider == "GCP" and st.session_state.selected_gcp_image:
        st.success("✅ GCP Image Selected")
        st.code(st.session_state.selected_gcp_image, language="text")
    else:
        st.info("No image selected")

# Main content
if provider == "AWS":
    st.header("🔶 AWS AMI Browser")

    try:
        aws_creds = get_aws_credentials()
        provisioner = AWSVMProvisioner(region=aws_region, **aws_creds)

        # Tabs for different browsing modes
        tab1, tab2, tab3, tab4 = st.tabs(["📚 Popular Images", "🔍 Search Images", "👤 My Images", "📋 All Available"])

        with tab1:
            st.subheader("Popular Pre-configured Images")

            with st.spinner("Loading popular images..."):
                try:
                    popular = get_cached_aws_popular_images(aws_region, aws_creds['access_key_id'])

                    for category, images in popular.items():
                        if images:
                            st.markdown(f"### {category}")
                            for img in images:
                                col1, col2, col3 = st.columns([3, 2, 1])

                                with col1:
                                    st.write(f"**{img['name']}**")
                                    st.caption(img.get('description', 'N/A')[:100])

                                with col2:
                                    st.write(f"AMI: `{img['image_id']}`")
                                    st.caption(f"Created: {img.get('creation_date', 'N/A')[:10]}")

                                with col3:
                                    if st.button("Select", key=f"select_{img['image_id']}"):
                                        st.session_state.selected_aws_image = img['image_id']
                                        st.success(f"✅ Selected {img['image_id']}")
                                        st.rerun()

                            st.markdown("---")
                except Exception as e:
                    st.error(f"❌ Failed to load popular images: {e}")

        with tab2:
            st.subheader("Search AMIs")

            search_term = st.text_input(
                "Search by name",
                placeholder="e.g., ubuntu, amazon-linux, windows",
                help="Search for AMIs by name"
            )

            owner_filter = st.selectbox(
                "Owner",
                ["amazon", "self", "aws-marketplace", "099720109477"],
                help="Filter by image owner (099720109477 = Canonical/Ubuntu)"
            )

            if st.button("🔍 Search", use_container_width=True):
                if search_term:
                    with st.spinner(f"Searching for '{search_term}'..."):
                        try:
                            results = get_cached_aws_search(aws_region, aws_creds['access_key_id'], search_term, owner_filter)

                            if results:
                                st.success(f"Found {len(results)} images")

                                for img in results:
                                    with st.expander(f"{img['name']}", expanded=False):
                                        col1, col2 = st.columns([3, 1])

                                        with col1:
                                            st.write(f"**AMI ID:** `{img['image_id']}`")
                                            st.write(f"**Description:** {img['description'][:150]}")
                                            st.write(f"**Architecture:** {img['architecture']}")
                                            st.write(f"**Platform:** {img['platform']}")
                                            st.write(f"**Created:** {img['creation_date'][:10]}")
                                            st.write(f"**Public:** {'Yes' if img['public'] else 'No'}")

                                        with col2:
                                            if st.button("Select", key=f"search_{img['image_id']}"):
                                                st.session_state.selected_aws_image = img['image_id']
                                                st.success(f"✅ Selected!")
                                                st.rerun()
                            else:
                                st.warning("No images found matching your search")
                        except Exception as e:
                            st.error(f"❌ Search failed: {e}")
                else:
                    st.warning("Please enter a search term")

        with tab3:
            st.subheader("My Custom AMIs")

            if st.button("🔄 Load My Images", use_container_width=True):
                with st.spinner("Loading your custom AMIs..."):
                    try:
                        my_images = get_cached_aws_my_images(aws_region, aws_creds['access_key_id'])

                        if my_images:
                            st.success(f"Found {len(my_images)} custom AMIs")

                            for img in my_images:
                                with st.expander(f"{img['name']}", expanded=False):
                                    col1, col2 = st.columns([3, 1])

                                    with col1:
                                        st.write(f"**AMI ID:** `{img['image_id']}`")
                                        st.write(f"**Description:** {img['description']}")
                                        st.write(f"**Architecture:** {img['architecture']}")
                                        st.write(f"**Created:** {img['creation_date'][:10]}")

                                    with col2:
                                        if st.button("Select", key=f"my_{img['image_id']}"):
                                            st.session_state.selected_aws_image = img['image_id']
                                            st.success(f"✅ Selected!")
                                            st.rerun()
                        else:
                            st.info("No custom AMIs found in your account")
                    except Exception as e:
                        st.error(f"❌ Failed to load custom AMIs: {e}")

        with tab4:
            st.subheader("All Available Images")
            st.warning("⚠️ This may take a moment to load")

            owner_type = st.selectbox(
                "Filter by owner",
                ["Amazon Official", "My Account", "Both"],
                key="all_owner_filter"
            )

            if st.button("📋 Load All Images", use_container_width=True):
                with st.spinner("Loading all available images..."):
                    try:
                        if owner_type == "Amazon Official":
                            owners = ['amazon']
                        elif owner_type == "My Account":
                            owners = ['self']
                        else:
                            owners = ['amazon', 'self']

                        all_images = get_cached_aws_all_images(aws_region, aws_creds['access_key_id'], owners)

                        if all_images:
                            st.success(f"Loaded {len(all_images)} images")

                            # Add pagination
                            items_per_page = 20
                            total_pages = (len(all_images) + items_per_page - 1) // items_per_page

                            if 'page' not in st.session_state:
                                st.session_state.page = 0

                            page = st.selectbox("Page", range(1, total_pages + 1), index=st.session_state.page) - 1
                            st.session_state.page = page

                            start_idx = page * items_per_page
                            end_idx = start_idx + items_per_page

                            for img in all_images[start_idx:end_idx]:
                                with st.expander(f"{img['name']}", expanded=False):
                                    col1, col2 = st.columns([3, 1])

                                    with col1:
                                        st.write(f"**AMI ID:** `{img['image_id']}`")
                                        st.write(f"**Description:** {img['description'][:150]}")
                                        st.write(f"**Architecture:** {img['architecture']}")
                                        st.write(f"**Created:** {img['creation_date'][:10]}")

                                    with col2:
                                        if st.button("Select", key=f"all_{img['image_id']}"):
                                            st.session_state.selected_aws_image = img['image_id']
                                            st.success(f"✅ Selected!")
                                            st.rerun()
                        else:
                            st.info("No images found")
                    except Exception as e:
                        st.error(f"❌ Failed to load images: {e}")

    except Exception as e:
        st.error(f"❌ Error initializing AWS provisioner: {e}")
        st.info("💡 Make sure your AWS credentials are configured in Settings")

# GCP Provider
else:
    st.header("🔷 GCP Image Browser")

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

            # Tabs for different browsing modes
            tab1, tab2, tab3, tab4 = st.tabs(["📚 Popular Images", "🔍 Search Images", "👤 My Images", "🏢 Public Projects"])

            with tab1:
                st.subheader("Popular Pre-configured Images")

                with st.spinner("Loading popular images..."):
                    try:
                        popular = get_cached_gcp_popular_images(gcp_project, gcp_zone)

                        for category, images in popular.items():
                            if images:
                                st.markdown(f"### {category}")
                                for img in images:
                                    col1, col2, col3 = st.columns([3, 2, 1])

                                    with col1:
                                        st.write(f"**{img['name']}**")
                                        st.caption(f"Family: {img['family']}")

                                    with col2:
                                        st.write(f"Image: `{img['image_name']}`")
                                        st.caption(f"Project: {img['project']}")

                                    with col3:
                                        if st.button("Select", key=f"select_{img['family']}_{img['project']}"):
                                            st.session_state.selected_gcp_image = {
                                                'family': img['family'],
                                                'project': img['project']
                                            }
                                            st.success(f"✅ Selected!")
                                            st.rerun()

                                st.markdown("---")
                    except Exception as e:
                        st.error(f"❌ Failed to load popular images: {e}")

            with tab2:
                st.subheader("Search Images")

                search_term = st.text_input(
                    "Search by name",
                    placeholder="e.g., debian, ubuntu, rocky",
                    help="Search for images by name"
                )

                project_filter = st.text_input(
                    "Project (optional)",
                    placeholder="e.g., debian-cloud, ubuntu-os-cloud",
                    help="Filter by specific project"
                )

                if st.button("🔍 Search", use_container_width=True):
                    if search_term:
                        with st.spinner(f"Searching for '{search_term}'..."):
                            try:
                                project_to_search = project_filter if project_filter else None
                                results = get_cached_gcp_search(gcp_project, gcp_zone, search_term, project_to_search)

                                if results:
                                    st.success(f"Found {len(results)} images")

                                    for img in results:
                                        with st.expander(f"{img['name']}", expanded=False):
                                            col1, col2 = st.columns([3, 1])

                                            with col1:
                                                st.write(f"**Name:** {img['name']}")
                                                st.write(f"**Family:** {img['family']}")
                                                st.write(f"**Description:** {img['description'][:150]}")
                                                st.write(f"**Architecture:** {img['architecture']}")
                                                st.write(f"**Size:** {img['disk_size_gb']} GB")
                                                st.write(f"**Created:** {img['creation_timestamp'][:10]}")
                                                st.write(f"**Project:** {img['project']}")

                                            with col2:
                                                if st.button("Select", key=f"search_{img['name']}"):
                                                    st.session_state.selected_gcp_image = {
                                                        'name': img['name'],
                                                        'project': img['project']
                                                    }
                                                    st.success(f"✅ Selected!")
                                                    st.rerun()
                                else:
                                    st.warning("No images found matching your search")
                            except Exception as e:
                                st.error(f"❌ Search failed: {e}")
                    else:
                        st.warning("Please enter a search term")

            with tab3:
                st.subheader("My Custom Images")

                if st.button("🔄 Load My Images", use_container_width=True):
                    with st.spinner("Loading your custom images..."):
                        try:
                            my_images = get_cached_gcp_my_images(gcp_project, gcp_zone)

                            if my_images:
                                st.success(f"Found {len(my_images)} custom images")

                                for img in my_images:
                                    with st.expander(f"{img['name']}", expanded=False):
                                        col1, col2 = st.columns([3, 1])

                                        with col1:
                                            st.write(f"**Name:** {img['name']}")
                                            st.write(f"**Family:** {img['family']}")
                                            st.write(f"**Description:** {img['description']}")
                                            st.write(f"**Size:** {img['disk_size_gb']} GB")
                                            st.write(f"**Created:** {img['creation_timestamp'][:10]}")

                                        with col2:
                                            if st.button("Select", key=f"my_{img['name']}"):
                                                st.session_state.selected_gcp_image = {
                                                    'name': img['name'],
                                                    'project': gcp_project
                                                }
                                                st.success(f"✅ Selected!")
                                                st.rerun()
                            else:
                                st.info("No custom images found in your project")
                        except Exception as e:
                            st.error(f"❌ Failed to load custom images: {e}")

            with tab4:
                st.subheader("Public Project Images")

                common_projects = [
                    "debian-cloud",
                    "ubuntu-os-cloud",
                    "centos-cloud",
                    "rocky-linux-cloud",
                    "rhel-cloud",
                    "windows-cloud",
                    "fedora-coreos-cloud",
                ]

                selected_project = st.selectbox(
                    "Select Public Project",
                    common_projects,
                    help="Browse images from public projects"
                )

                if st.button("📋 Load Images from Project", use_container_width=True):
                    with st.spinner(f"Loading images from {selected_project}..."):
                        try:
                            project_images = get_cached_gcp_project_images(gcp_project, gcp_zone, selected_project)

                            if project_images:
                                st.success(f"Found {len(project_images)} images in {selected_project}")

                                for img in project_images:
                                    with st.expander(f"{img['name']}", expanded=False):
                                        col1, col2 = st.columns([3, 1])

                                        with col1:
                                            st.write(f"**Name:** {img['name']}")
                                            st.write(f"**Family:** {img['family']}")
                                            st.write(f"**Description:** {img['description'][:150]}")
                                            st.write(f"**Size:** {img['disk_size_gb']} GB")
                                            st.write(f"**Created:** {img['creation_timestamp'][:10]}")

                                        with col2:
                                            if st.button("Select", key=f"pub_{img['name']}"):
                                                st.session_state.selected_gcp_image = {
                                                    'name': img['name'],
                                                    'project': selected_project
                                                }
                                                st.success(f"✅ Selected!")
                                                st.rerun()
                            else:
                                st.info(f"No images found in {selected_project}")
                        except Exception as e:
                            st.error(f"❌ Failed to load images: {e}")

        except Exception as e:
            st.error(f"❌ Error initializing GCP provisioner: {e}")
            st.info("💡 Make sure your GCP credentials are configured in Settings")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666;'>
        <p>🖼️ Image Browser | Browse and select VM images for provisioning</p>
        <p>Selected images are saved for use in the Home page when creating VMs</p>
    </div>
    """,
    unsafe_allow_html=True
)

"""Instance Type Browser page for filtering and selecting VM instance types."""

import streamlit as st
from cloud_automation.instance_specs import (
    filter_aws_instances,
    filter_gcp_machines,
    get_instance_categories,
)

# Cached functions for instance type filtering
@st.cache_data(ttl=3600)  # 1 hour cache (instance specs don't change frequently)
def get_cached_aws_instances(min_vcpu: int, max_vcpu: int, min_memory: float, max_memory: float, category: str = None, burstable_only: bool = False):
    """Cached AWS instance type filtering."""
    return filter_aws_instances(
        min_vcpu=min_vcpu,
        max_vcpu=max_vcpu,
        min_memory_gb=min_memory,
        max_memory_gb=max_memory,
        category=category,
        burstable_only=burstable_only
    )

@st.cache_data(ttl=3600)  # 1 hour cache
def get_cached_gcp_machines(min_vcpu: int, max_vcpu: int, min_memory: float, max_memory: float, category: str = None, exclude_shared: bool = False):
    """Cached GCP machine type filtering."""
    return filter_gcp_machines(
        min_vcpu=min_vcpu,
        max_vcpu=max_vcpu,
        min_memory_gb=min_memory,
        max_memory_gb=max_memory,
        category=category,
        exclude_shared_cpu=exclude_shared
    )

@st.cache_data(ttl=3600)  # 1 hour cache
def get_cached_categories():
    """Cached instance categories."""
    return get_instance_categories()

st.set_page_config(page_title="Instance Type Browser", page_icon="🖥️", layout="wide")

st.title("🖥️ Instance Type Browser")
st.markdown("""
Browse and filter VM instance types by specifications. Select an instance type to use it when provisioning VMs.
""")

# Provider selection
provider = st.radio(
    "Cloud Provider",
    options=["AWS", "GCP"],
    horizontal=True,
    key="instance_browser_provider"
)

st.markdown("---")

# Get categories (cached)
categories = get_cached_categories()

if provider == "AWS":
    st.subheader("🔍 Filter AWS Instance Types")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**vCPU Range**")
        min_vcpu = st.slider(
            "Minimum vCPUs",
            min_value=1,
            max_value=96,
            value=1,
            key="aws_min_vcpu"
        )
        max_vcpu = st.slider(
            "Maximum vCPUs",
            min_value=1,
            max_value=96,
            value=96,
            key="aws_max_vcpu"
        )

    with col2:
        st.markdown("**Memory Range (GB)**")
        min_memory = st.slider(
            "Minimum Memory (GB)",
            min_value=0.5,
            max_value=384.0,
            value=0.5,
            step=0.5,
            key="aws_min_memory"
        )
        max_memory = st.slider(
            "Maximum Memory (GB)",
            min_value=0.5,
            max_value=384.0,
            value=384.0,
            step=0.5,
            key="aws_max_memory"
        )

    # Category filter
    category_options = ["All"] + categories["AWS"]
    selected_category = st.selectbox(
        "Category",
        options=category_options,
        key="aws_category"
    )

    # Burstable filter
    burstable_only = st.checkbox(
        "Show only burstable instances (T-series)",
        value=False,
        key="aws_burstable"
    )

    # Filter instances (cached)
    category_filter = None if selected_category == "All" else selected_category
    instances = get_cached_aws_instances(
        min_vcpu=min_vcpu,
        max_vcpu=max_vcpu,
        min_memory=min_memory,
        max_memory=max_memory,
        category=category_filter,
        burstable_only=burstable_only
    )

    st.markdown("---")
    st.subheader(f"📊 Results: {len(instances)} matching instance types")

    if instances:
        # Display in a table format
        for instance in instances:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 2, 1])

                with col1:
                    st.markdown(f"**{instance['instance_type']}**")
                    st.caption(instance['category'])

                with col2:
                    st.metric("vCPUs", instance['vcpu'])

                with col3:
                    st.metric("Memory", f"{instance['memory_gb']} GB")

                with col4:
                    st.text(f"Network: {instance['network']}")
                    if instance.get('burstable'):
                        st.caption("⚡ Burstable")

                with col5:
                    if st.button("Select", key=f"select_aws_{instance['instance_type']}"):
                        st.session_state.selected_aws_instance_type = instance['instance_type']
                        st.success(f"✅ Selected: {instance['instance_type']}")
                        st.info("Go to Home page to provision with this instance type")

                st.markdown("---")
    else:
        st.info("No instance types match your filter criteria. Try adjusting the filters.")

    # Show currently selected instance type
    if 'selected_aws_instance_type' in st.session_state and st.session_state.selected_aws_instance_type:
        st.sidebar.success(f"✅ Selected AWS Instance Type:\n\n**{st.session_state.selected_aws_instance_type}**")

else:  # GCP
    st.subheader("🔍 Filter GCP Machine Types")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**vCPU Range**")
        min_vcpu = st.slider(
            "Minimum vCPUs",
            min_value=1,
            max_value=96,
            value=1,
            key="gcp_min_vcpu"
        )
        max_vcpu = st.slider(
            "Maximum vCPUs",
            min_value=1,
            max_value=96,
            value=96,
            key="gcp_max_vcpu"
        )

    with col2:
        st.markdown("**Memory Range (GB)**")
        min_memory = st.slider(
            "Minimum Memory (GB)",
            min_value=0.5,
            max_value=384.0,
            value=0.5,
            step=0.5,
            key="gcp_min_memory"
        )
        max_memory = st.slider(
            "Maximum Memory (GB)",
            min_value=0.5,
            max_value=384.0,
            value=384.0,
            step=0.5,
            key="gcp_max_memory"
        )

    # Category filter
    category_options = ["All"] + categories["GCP"]
    selected_category = st.selectbox(
        "Category",
        options=category_options,
        key="gcp_category"
    )

    # Shared CPU filter
    exclude_shared = st.checkbox(
        "Exclude shared-core machines (E2-micro, E2-small)",
        value=False,
        key="gcp_exclude_shared"
    )

    # Filter machines (cached)
    category_filter = None if selected_category == "All" else selected_category
    machines = get_cached_gcp_machines(
        min_vcpu=min_vcpu,
        max_vcpu=max_vcpu,
        min_memory=min_memory,
        max_memory=max_memory,
        category=category_filter,
        exclude_shared=exclude_shared
    )

    st.markdown("---")
    st.subheader(f"📊 Results: {len(machines)} matching machine types")

    if machines:
        # Display in a table format
        for machine in machines:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 1, 1, 2, 1])

                with col1:
                    st.markdown(f"**{machine['machine_type']}**")
                    st.caption(machine['category'])

                with col2:
                    st.metric("vCPUs", machine['vcpu'])

                with col3:
                    st.metric("Memory", f"{machine['memory_gb']} GB")

                with col4:
                    st.text(f"Network: {machine['network']}")
                    if machine.get('shared_cpu'):
                        st.caption("🔄 Shared CPU")

                with col5:
                    if st.button("Select", key=f"select_gcp_{machine['machine_type']}"):
                        st.session_state.selected_gcp_machine_type = machine['machine_type']
                        st.success(f"✅ Selected: {machine['machine_type']}")
                        st.info("Go to Home page to provision with this machine type")

                st.markdown("---")
    else:
        st.info("No machine types match your filter criteria. Try adjusting the filters.")

    # Show currently selected machine type
    if 'selected_gcp_machine_type' in st.session_state and st.session_state.selected_gcp_machine_type:
        st.sidebar.success(f"✅ Selected GCP Machine Type:\n\n**{st.session_state.selected_gcp_machine_type}**")

# Help section
with st.sidebar:
    st.markdown("---")
    st.subheader("💡 Instance Type Guide")

    st.markdown("""
    **AWS Categories:**
    - **General Purpose (T, M)**: Balanced compute, memory, networking
    - **Compute Optimized (C)**: High compute performance
    - **Memory Optimized (R)**: Fast performance for memory-intensive workloads
    - **Burstable (T2/T3)**: Baseline performance with burst capability

    **GCP Categories:**
    - **General Purpose (N1, N2, E2)**: Balanced performance
    - **Compute Optimized (C2)**: Highest performance per core
    - **Memory Optimized (M1, M2)**: Ultra high memory
    - **Standard**: Balanced vCPU to memory ratio
    - **High-Memory**: Higher memory per vCPU
    - **High-CPU**: More vCPUs per memory
    """)

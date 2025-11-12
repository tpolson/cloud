"""Cloud Automation Tool - Main Navigation."""

import streamlit as st

# Define pages in desired order
home_page = st.Page("pages/Home.py", title="Home", icon="☁️", default=True)
vm_page = st.Page("pages/VM_Management.py", title="VM Management", icon="🖥️")
instance_page = st.Page("pages/Instance_Type_Browser.py", title="Instance Type Browser", icon="📊")
image_page = st.Page("pages/Image_Browser.py", title="Image Browser", icon="🖼️")
settings_page = st.Page("pages/Settings.py", title="Settings", icon="⚙️")

# Create navigation with pages in desired order
pg = st.navigation([home_page, vm_page, instance_page, image_page, settings_page])

# Run the selected page
pg.run()

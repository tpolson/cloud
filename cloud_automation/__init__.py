"""Cloud Automation - Multi-cloud VM and storage provisioning."""

__version__ = "0.1.0"
__author__ = "tpolson"

from cloud_automation.aws import vm as aws_vm
from cloud_automation.aws import storage as aws_storage
from cloud_automation.gcp import vm as gcp_vm
from cloud_automation.gcp import storage as gcp_storage

__all__ = [
    "aws_vm",
    "aws_storage",
    "gcp_vm",
    "gcp_storage",
]

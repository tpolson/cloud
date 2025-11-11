"""Utility functions for cloud automation."""

import sys
from typing import Any, Dict, List
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)


def print_success(message: str) -> None:
    """Print success message in green.

    Args:
        message: Message to print
    """
    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")


def print_error(message: str) -> None:
    """Print error message in red.

    Args:
        message: Message to print
    """
    print(f"{Fore.RED}✗ {message}{Style.RESET_ALL}", file=sys.stderr)


def print_warning(message: str) -> None:
    """Print warning message in yellow.

    Args:
        message: Message to print
    """
    print(f"{Fore.YELLOW}⚠ {message}{Style.RESET_ALL}")


def print_info(message: str) -> None:
    """Print info message in blue.

    Args:
        message: Message to print
    """
    print(f"{Fore.BLUE}ℹ {message}{Style.RESET_ALL}")


def format_tags(tags: Dict[str, str]) -> List[Dict[str, str]]:
    """Format tags dictionary for AWS format.

    Args:
        tags: Dictionary of tag key-value pairs

    Returns:
        List of tag dictionaries in AWS format
    """
    return [{"Key": k, "Value": v} for k, v in tags.items()]


def format_labels(labels: Dict[str, str]) -> Dict[str, str]:
    """Format labels dictionary for GCP format.

    GCP labels have restrictions: lowercase letters, numbers, hyphens and underscores

    Args:
        labels: Dictionary of label key-value pairs

    Returns:
        Formatted labels dictionary
    """
    formatted = {}
    for k, v in labels.items():
        # Convert to lowercase and replace invalid characters
        key = k.lower().replace(' ', '-').replace('_', '-')
        value = v.lower().replace(' ', '-').replace('_', '-')
        formatted[key] = value
    return formatted


def validate_name(name: str, cloud_provider: str = "aws") -> bool:
    """Validate resource name according to cloud provider rules.

    Args:
        name: Resource name to validate
        cloud_provider: Cloud provider (aws or gcp)

    Returns:
        True if name is valid

    Raises:
        ValueError: If name is invalid
    """
    if not name:
        raise ValueError("Resource name cannot be empty")

    if cloud_provider == "aws":
        # AWS has various naming rules depending on resource type
        # General rules: alphanumeric, hyphens, underscores, periods
        if len(name) > 255:
            raise ValueError("AWS resource name cannot exceed 255 characters")

    elif cloud_provider == "gcp":
        # GCP names: lowercase letters, numbers, hyphens
        # Must start with letter, end with letter or number
        if not name[0].isalpha():
            raise ValueError("GCP resource name must start with a letter")
        if not (name[-1].isalnum()):
            raise ValueError("GCP resource name must end with a letter or number")
        if not all(c.islower() or c.isdigit() or c == '-' for c in name):
            raise ValueError("GCP resource name can only contain lowercase letters, numbers, and hyphens")
        if len(name) > 63:
            raise ValueError("GCP resource name cannot exceed 63 characters")

    return True


def parse_size(size_str: str) -> int:
    """Parse storage size string to GB.

    Args:
        size_str: Size string (e.g., '100GB', '1TB', '512')

    Returns:
        Size in GB
    """
    size_str = str(size_str).upper().strip()

    # If just a number, assume GB
    if size_str.isdigit():
        return int(size_str)

    # Parse with unit
    units = {
        'GB': 1,
        'TB': 1024,
        'PB': 1024 * 1024,
    }

    for unit, multiplier in units.items():
        if size_str.endswith(unit):
            size = float(size_str[:-len(unit)])
            return int(size * multiplier)

    raise ValueError(f"Invalid size format: {size_str}. Use format like '100GB' or '1TB'")


def wait_with_spinner(message: str, condition_fn, timeout: int = 300):
    """Wait for a condition with a spinner animation.

    Args:
        message: Message to display
        condition_fn: Function that returns True when condition is met
        timeout: Maximum time to wait in seconds

    Returns:
        True if condition was met, False if timeout
    """
    import time
    import itertools

    spinner = itertools.cycle(['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏'])
    start_time = time.time()

    while time.time() - start_time < timeout:
        if condition_fn():
            print(f"\r{' ' * 80}\r", end='')  # Clear line
            return True

        print(f"\r{next(spinner)} {message}", end='', flush=True)
        time.sleep(0.1)

    print(f"\r{' ' * 80}\r", end='')  # Clear line
    return False

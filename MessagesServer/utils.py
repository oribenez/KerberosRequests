import ipaddress
from datetime import datetime

from lib.utils import unpack_key_hex, unpack_key_base64


def are_timestamps_close(timestamp1, timestamp2, threshold_seconds=1):
    """
        Checks if two timestamps are close within a specified threshold.

    Parameters:
        - timestamp1 (float): First timestamp.
        - timestamp2 (float): Second timestamp.
        - threshold_seconds (int, optional): Maximum allowed difference (default: 1s).

    Returns:
        - bool: True if timestamps are close, False otherwise.
    """

    # Convert timestamps to datetime objects
    dt1 = datetime.fromtimestamp(timestamp1)
    dt2 = datetime.fromtimestamp(timestamp2)

    # Calculate the absolute difference in seconds
    time_difference = abs((dt2 - dt1).total_seconds())

    # Check if the difference is within the threshold
    return time_difference <= threshold_seconds



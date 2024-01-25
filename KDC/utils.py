import base64
import binascii
import hashlib
import hmac
import json
import sys

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util import number
from Crypto.Util.Padding import pad
from Crypto.Util.number import getPrime
from Crypto.Random import get_random_bytes
from Crypto.Hash import SHA256
import uuid


def generate_random_uuid():
    """
    Generates a random UUID and returns it as 16 bytes.

    Returns:
    - str: 16 bytes of the generated UUID without dashes.
    """
    random_uuid = uuid.uuid4()
    nodash_uuid = str(random_uuid).replace('-', '')
    uuid16bytes = nodash_uuid[:16]

    return uuid16bytes


def read_port_from_file(port_filename="port.info"):
    """
    Reads the port number from a file.

    Params:
    - port_filename (str): The filename containing the port number.

    Returns:
    - int: The port number read from the file or the default port if file not found or invalid.
    """

    default_port = 1256  # default port

    try:
        with open(port_filename, "r") as port_file:
            port_file_txt = port_file.read().strip()

            # Validate
            port = int(port_file_txt)
            if 1 <= port <= 65535:
                return port
            else:
                print("Error: Port number must be between 1 and 65535.")

    except FileNotFoundError:
        print(f"Error: File '{port_filename}' not found.")
    except ValueError:
        print(f"Error: Invalid port number in '{port_filename}'.")

    print(f"Using default port: {default_port}")
    return default_port

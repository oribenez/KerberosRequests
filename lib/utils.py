import base64
import binascii
import json
import socket
import struct
import sys
from itertools import cycle

from lib.config import salt as general_salt, package_dict as general_package_dict
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad


def pack_key_base64(key: bytes):
    """
    Encode a byte sequence using base64 encoding.

    Parameters:
        - key (bytes): The byte sequence to be encoded.

    Returns:
        str: The base64-encoded string representation of the input byte sequence.
    """
    return base64.b64encode(key).decode('utf-8')


def unpack_key_base64(key: bytes):
    """
        Decode a base64-encoded string into a byte sequence.

    Parameters:
        - key (bytes): The base64-encoded string to be decoded.

    Returns:
        bytes: The byte sequence decoded from the input base64-encoded string.
    """
    return base64.b64decode(key)


def pack_key_hex(key: bytes):
    """
        Convert a byte sequence into a hex-encoded string.

    Parameters:
        - key (bytes): The byte sequence to be hex-encoded.

    Returns:
        str: The hex-encoded string representing the input byte sequence.
    """
    return binascii.hexlify(key).decode('utf-8')


def unpack_key_hex(key: bytes):
    """
        Convert a hex-encoded string into a byte sequence.

    Parameters:
        - key (bytes): The hex-encoded string to be converted.

    Returns:
        bytes: The byte sequence representing the input hex-encoded string.
    """
    return binascii.unhexlify(key)


def hash_password(password: str, salt: bytes = general_salt, key_length=32, iterations=1000000):
    """
        Hash a password using PBKDF2 with a specified salt, key length, and number of iterations.

    Parameters:
        - password (str): The password to be hashed.
        - salt (bytes): The salt to be used in the hashing process. Defaults to the general salt.
        - key_length (int): The length of the derived key in bytes. Defaults to 32.
        - iterations (int): The number of iterations for the PBKDF2 algorithm. Defaults to 1,000,000.

    Returns:
        bytes: The hashed password.
    """
    hashed_password = PBKDF2(password, salt, dkLen=key_length, count=iterations)
    return hashed_password


def decrypt_aes_cbc(key: bytes, iv: bytes, encrypted_data: bytes) -> bytes:
    """
    Decrypt data using AES in CBC mode.

    Parameters:
        - key (bytes): The key for AES decryption.
        - iv (bytes): The initialization vector for AES decryption.
        - encrypted_data (bytes): The data to be decrypted.

    Returns:
        bytes: The decrypted data.
    """

    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    deciphered_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)

    return deciphered_data


def encrypt_aes_cbc(key: bytes, data: bytes, iv: bytes = None) -> (bytes, bytes):
    """
        Encrypt data using AES in CBC mode.

    Parameters:
        - key (bytes): The key for AES encryption.
        - data (bytes): The data to be encrypted.
        - iv (bytes, optional): The initialization vector for AES encryption. If not provided, a random vector will be generated.

    Returns:
        Tuple[bytes, bytes]: A tuple containing the initialization vector (iv) and the encrypted data.

    This function uses the AES algorithm in CBC mode to encrypt the provided data using the specified key and initialization vector.
    """

    if iv is None:
        iv = get_random_bytes(16)

    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphered_data = cipher.encrypt(pad(data, AES.block_size))

    # print(f"iv ({len(cipher.iv)}): {cipher.iv}")
    # print(f"ciphertext ({len(ciphered_data)}): ", ciphered_data)
    return cipher.iv, ciphered_data



"""
REQUEST, RESPONSE: str
    Constants representing the types of communication messages - request and response.
"""
REQUEST, RESPONSE = 'request', 'response'


def flatten_dict(data, parent_key=""):
    """
    Flatten a nested dictionary by concatenating keys with a separator.

    Parameters:
    - data (dict): The nested dictionary to be flattened.
    - parent_key (str): The prefix to be added to the keys.

    Returns:
    dict: A flattened dictionary.
    """

    items = []
    for key, value in data.items():
        new_key = f"{parent_key}__{key}" if parent_key else key  # Prefix keys with parent key
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key).items())  # Recurse for nested dictionaries
        else:
            items.append((new_key, value))
    return dict(items)


def unflatten_dict(data):
    """
    Unflatten a dictionary by reversing the flattening process.

    Parameters:
    - data (dict): The flattened dictionary to be unflattened.

    Returns:
    dict: The unflattened nested dictionary.
    """
    nested_dict = {}
    for key, value in data.items():
        parts = key.split("__")  # Split key based on the separator used in flatten_dict
        current_dict = nested_dict
        for part in parts[:-1]:  # Traverse nested levels based on key parts
            if part not in current_dict:
                current_dict[part] = {}
            current_dict = current_dict[part]
        current_dict[parts[-1]] = value  # Assign value to the final leaf key
    return nested_dict


def pack_data(package_dict: dict, packing_type: str, req: dict) -> bytes:
    """
    Pack data into a binary format based on the specified packing type using struct library.

    Parameters:
    - package_dict (dict): Dictionary containing the data packing format.
    - packing_type (str): Type of data packing ('request' or 'response').
    - req (dict): The request or response dictionary to be packed.

    Returns:
    bytes: Packed binary data.
    """

    code = str(req['header']['code'])

    packed_payload = b''
    if package_dict[packing_type]['payload'][code] is not None:
        payload_format = package_dict[packing_type]['payload'][code]['format']
        req['header']['payload_size'] = struct.calcsize(payload_format)

        payload_keys = package_dict[packing_type]['payload'][code]['keys']
        flattened_payload = flatten_dict(req['payload'])

        payload = tuple(flattened_payload.values())
        payload = tuple(value.encode("utf-8") if isinstance(value, str) else value for value in payload)
        payload_format_cycled_per_keys = payload_format[0] + str(payload_format[1:]) * int(
            len(payload) / len(payload_keys))

        if 'is_last_item_has_unknown_size' in package_dict[packing_type]['payload'][code]:
            last_val = payload[-1]
            # assume last value is in bytes type
            payload_format_cycled_per_keys += f'{len(last_val)}s'
        packed_payload = struct.pack(payload_format_cycled_per_keys, *payload)
    else:
        req['header']['payload_size'] = 0

    header = tuple(req['header'].values())
    header = tuple(value.encode("utf-8") if isinstance(value, str) else value for value in header)

    header_format = package_dict[packing_type]['header']['format']
    packed_header = struct.pack(header_format, *header)

    return packed_header + packed_payload


def unpack_data(package_dict: dict, packing_type: str, data: bytes) -> dict:
    """
    Unpack binary data into a dictionary based on the specified packing type using struct library.

    Parameters:
    - package_dict (dict): Dictionary containing the data packing format.
    - packing_type (str): Type of data packing ('request' or 'response').
    - data (bytes): Binary data to be unpacked.

    Returns:
    dict: Unpacked data as a dictionary.
    """

    # unpack header
    header_format = package_dict[packing_type]['header']['format']
    header_types = package_dict[packing_type]['header']['types']
    header_size = struct.calcsize(header_format)
    unpacked_data = struct.unpack(header_format, data[:header_size])
    cleaned_data = []
    for i, value in enumerate(unpacked_data):
        cleaned_value = value

        # if type is str then decode it
        if header_types[i] is str and isinstance(value, bytes):
            cleaned_value = cleaned_value.rstrip(b'\x00').decode('utf-8')

        cleaned_data.append(cleaned_value)
    header_keys = package_dict[packing_type]['header']['keys']
    header = dict(zip(header_keys, tuple(cleaned_data)))

    # unpack payload
    code = str(header['code'])
    if package_dict[packing_type]['payload'][code] is not None:
        payload_types = package_dict[packing_type]['payload'][code]['types']
        payload_format = package_dict[packing_type]['payload'][code]['format']
        payload_size = struct.calcsize(payload_format)

        sliced_data = data[header_size:]
        list_data = []
        payload = {}
        while len(sliced_data):
            # unpack slice
            unpacked_data = struct.unpack(payload_format, sliced_data[:payload_size])

            # if the last item has unknown length then we will unpack it
            # make sure that the last item is not included in the format of the struct
            if 'is_last_item_has_unknown_size' in package_dict[packing_type]['payload'][code]:
                last_item = sliced_data[payload_size:]
                unpacked_data += (last_item,)

            # clean padding from strings
            cleaned_data = []
            for i, value in enumerate(unpacked_data):
                cleaned_value = value

                # if type is str then decode it
                if payload_types[i] is str and isinstance(value, bytes):
                    cleaned_value = cleaned_value.rstrip(b'\x00').decode('utf-8')

                cleaned_data.append(cleaned_value)
            cleaned_data = tuple(cleaned_data)

            # concat keys to values
            payload_keys = package_dict[packing_type]['payload'][code]['keys']
            payload = dict(zip(payload_keys, cleaned_data))

            # unflatten payload
            payload = unflatten_dict(payload)

            # prepare next slice
            list_data += [payload]
            sliced_data = sliced_data[payload_size:]

            # Check if the type of data in payload is list -> return list[...] else dict{...}
            if 'is_list' not in package_dict[packing_type]['payload'][code]:
                break

        if 'is_list' in package_dict[packing_type]['payload'][code]:
            payload = list_data

    else:
        payload = None

    return {'header': header, 'payload': payload}


def send(connection, packing_type: str, data: dict):
    """
    Send packed data to the specified connection.

    Parameters:
    - connection: Connection object.
    - packing_type (str): Type of data packing ('request' or 'response').
    - data (dict): Data to be sent.

    """
    packed_data = pack_data(general_package_dict, packing_type, data)
    send_data(connection, packed_data)


def send_data(connection, data: bytes):
    """
    Send raw data over the specified connection.

    Parameters:
    - connection: Connection object.
    - data (bytes): Data to be sent.
    """
    # Send the size of the data
    data_size = len(data)
    connection.sendall(struct.pack("!I", data_size))

    # Send the data in chunks
    chunk_size = 1024
    for i in range(0, len(data), chunk_size):
        connection.sendall(data[i:i + chunk_size])


def receive_data(connection, timeout=10) -> bytes:
    """
    Receive data from the specified connection.

    Parameters:
    - connection: Connection object.
    - timeout (int): Timeout value for the connection.

    Returns:
    bytes: Received data.
    """

    connection.settimeout(timeout)  # Set a timeout for this connection

    # Receive the size of the data
    size_data = connection.recv(4)
    data_size = struct.unpack("!I", size_data)[0]
    # Receive the data in chunks
    received_data = b""
    while len(received_data) < data_size:
        chunk = connection.recv(min(1024, data_size - len(received_data)))
        if not chunk:
            break
        received_data += chunk

    return received_data


def send_request(ip, port, data: dict) -> dict:
    """
    Send a request to the specified IP and port and receive the response.

    Parameters:
    - ip (str): IP address of the server.
    - port (int): Port number to connect to.
    - data (dict): Data to be sent in the request.

    Returns:
    dict: Response data received from the server.
    """
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Establish connection to server
        connection.connect((ip, port))
        # Send data
        send(connection, REQUEST, data)

        # Get response back
        response = receive_data(connection)
        unpacked_res = unpack_data(general_package_dict, RESPONSE, response)

        return unpacked_res
    except ConnectionRefusedError:
        raise Exception("Error: Connection refused. Ensure that the server is running.")
    except Exception as e:
        raise Exception(f"Error during communication: {e}")

    finally:
        connection.close()


# ANSI escape codes for some colors
RED = "\033[91m"      # Red
GREEN = "\033[92m"    # Green
YELLOW = "\033[93m"   # Yellow
BLUE = "\033[94m"     # Blue
MAGENTA = "\033[95m"  # Magenta
CYAN = "\033[96m"     # Cyan


def color(text, color_code):
    """
    Apply ANSI color escape codes to the given text.

    Args:
        text (str): The text to be colored.
        color_code (str): ANSI escape code for the desired color.

    Returns:
        str: The colored text.
    """
    return f"{color_code}{text}\033[0m"


def bold(text):
    """
    Apply ANSI escape codes for bold formatting to the given text.

    Args:
        text (str): The text to be formatted in bold.

    Returns:
        str: The bold-formatted text.
    """
    return "\033[1m" + text + "\033[0m"

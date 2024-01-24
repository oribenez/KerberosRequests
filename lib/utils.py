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
    return base64.b64encode(key).decode('utf-8')


def unpack_key_base64(key: bytes):
    return base64.b64decode(key)


def pack_key_hex(key: bytes):
    return binascii.hexlify(key).decode('utf-8')


def unpack_key_hex(key: bytes):
    return binascii.unhexlify(key)


def hash_password(password: str, salt: bytes = general_salt, key_length=32, iterations=1000000):
    hashed_password = PBKDF2(password, salt, dkLen=key_length, count=iterations)
    return hashed_password


def decrypt_aes_cbc(key: bytes, iv: bytes, encrypted_data: bytes) -> bytes:
    try:
        cipher = AES.new(key, AES.MODE_CBC, iv=iv)
        deciphered_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)

        return deciphered_data
    except Exception as e:

        print("decrypt_aes_cbc():: ", e)
        print(f"key: {key} | iv: {iv} | encrypted_data: {encrypted_data}")
        print(f"key: {len(key)} | iv: {len(iv)} | encrypted_data: {len(encrypted_data)}")
        raise e


def encrypt_aes_cbc(key: bytes, data: bytes, iv: bytes = None) -> (bytes, bytes):
    print("encrypt_aes_cbc()")
    try:
        if iv is None:
            iv = get_random_bytes(16)

        cipher = AES.new(key, AES.MODE_CBC, iv)
        ciphered_data = cipher.encrypt(pad(data, AES.block_size))

        print(f"iv ({len(cipher.iv)}): {cipher.iv}")
        print(f"ciphertext ({len(ciphered_data)}): ", ciphered_data)
        return cipher.iv, ciphered_data
    except Exception as e:
        print("encrypt_aes_cbc():: ", e)
        print(f"key: {key} \ndata: {iv} \ndata: {data}")

        raise e


REQUEST, RESPONSE = 'request', 'response'


def flatten_dict(data, parent_key=""):
    items = []
    for key, value in data.items():
        new_key = f"{parent_key}__{key}" if parent_key else key  # Prefix keys with parent key
        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key).items())  # Recurse for nested dictionaries
        else:
            items.append((new_key, value))
    return dict(items)


def unflatten_dict(data):
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
    print('pack_data()')
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
        print('payload_format_cycled_per_keys: ', payload_format_cycled_per_keys)
        print('payload: ', payload)

        if 'is_last_item_has_unknown_size' in package_dict[packing_type]['payload'][code]:
            last_val = payload[-1]
            # assume last value is in bytes type
            payload_format_cycled_per_keys += f'{len(last_val)}s'
        packed_payload = struct.pack(payload_format_cycled_per_keys, *payload)
    else:
        req['header']['payload_size'] = 0

    header = tuple(req['header'].values())
    header = tuple(value.encode("utf-8") if isinstance(value, str) else value for value in header)

    print(header)
    header_format = package_dict[packing_type]['header']['format']
    packed_header = struct.pack(header_format, *header)

    return packed_header + packed_payload


def unpack_data(package_dict: dict, packing_type: str, data: bytes) -> dict:
    print('unpack_data()')

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
    print('code: ', code)
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
    packed_data = pack_data(general_package_dict, packing_type, data)
    send_data(connection, packed_data)


def send_data(connection, data: bytes):
    # Send the size of the data
    data_size = len(data)
    connection.sendall(struct.pack("!I", data_size))

    # Send the data in chunks
    chunk_size = 1024
    for i in range(0, len(data), chunk_size):
        connection.sendall(data[i:i + chunk_size])


def receive_data(connection, timeout=10) -> bytes:
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
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"


def color(text, color_code):
    return f"{color_code}{text}\033[0m"


def bold(text):
    return "\033[1m" + text + "\033[0m"

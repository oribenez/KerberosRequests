from Crypto.Random import get_random_bytes

from lib.ServerException import ServerException
from lib.utils import pack_key_base64, send_request, pack_key_hex
from config import (__api_version__,
                    __server_creds_filename__)
import config as cfg


def register_new_server(server_info):
    # Generate a random 256-bit (32-byte) AES key for server and client
    aes_key = get_random_bytes(32)

    # request to server - new connection
    request = {
        'header': {
            'client_id': 'undefined',
            'version': __api_version__,
            'code': 1025
        }, 'payload': {
            'name': server_info['name'],
            'aes_key': aes_key,
            'server_ip': server_info['server_ip'],
            'server_port': server_info['server_port'],
        }
    }

    response = send_request(cfg.__kdc_server_ip__, cfg.__kdc_server_port__, request)
    response_code = response["header"]["code"]
    if response_code == 16000:  # registration success
        print("[SUCCESS] Server registered")
        # save user to file
        with open(__server_creds_filename__, "w") as file:
            server_id = response["payload"]["server_id"]
            server_id_hex = pack_key_hex(server_id.encode('utf-8'))
            aes_key_base64 = pack_key_base64(aes_key)

            # save to file
            file.write(f"{server_info['server_ip']}:{server_info['server_port']}\n{server_info['name']}\n{server_id_hex}\n{aes_key_base64}")

            server_info = {**server_info, **{'server_id': server_id, 'aes_key': aes_key}}
            return server_info

    elif response_code == 1601:  # registration failed
        print("[1601] Registration failed")
        raise ServerException()

    else:  # unknown response
        print("Unknown response from server: ", response)
        raise ServerException()

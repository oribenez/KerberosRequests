from Crypto.Random import get_random_bytes

from lib.ServerException import ServerException
from lib.utils import pack_key_base64, send_request, pack_key_hex
from config import (__api_version__,
                    __server_creds_filename__,
                    __kdc_server_ip__,
                    __kdc_server_port__,
                    __msg_server_port__)


def register_new_server(server_name):
    # Generate a random 256-bit (32-byte) AES key for server and client
    aes_key = get_random_bytes(32)

    # request to server - new connection
    request = {
        'header': {
            'client_id': 'undefined',
            'version': __api_version__,
            'code': 1025
        }, 'payload': {
            'name': server_name,
            'aes_key': aes_key
        }
    }

    response = send_request(__kdc_server_ip__, __kdc_server_port__, request)
    response_code = response["header"]["code"]
    print('response:', response)
    if response_code == 16000:  # registration success
        print("[16000] Registration success")
        # save user to file
        with open(__server_creds_filename__, "w") as file:
            server_id = response["payload"]["server_id"]
            server_id_hex = pack_key_hex(server_id.encode('utf-8'))
            aes_key_base64 = pack_key_base64(aes_key)

            file.write(f"{__msg_server_port__}\n{server_name}\n{server_id_hex}\n{aes_key_base64}")

            server_info = {
                'port': __msg_server_port__, 'name': server_name, 'server_id': server_id, 'aes_key': aes_key
            }
            return server_info

    elif response_code == 1601:  # registration failed
        print("[1601] Registration failed")
        raise ServerException()

    else:  # unknown response
        print("Unknown response from server: ", response)
        raise ServerException()

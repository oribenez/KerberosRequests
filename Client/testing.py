import time

from Crypto.Random import get_random_bytes

from lib.utils import encrypt_aes_cbc, decrypt_aes_cbc


# key = b"\x16\xd4\x98\xca\xe5\x03\xe5&_\xa2\xf9\xeb\xaai\xa5\x08\x90\xaaU\xee'\x13\xc7!8\xda\xb4\xaeWg\x8cv"
# encrypted_data = b'\xb7"\xac7\xc3i!B\xd6\xc9\x1ef\xd1\xe9Iz\xd3^\xa3\x887\xb9\xacE\xf94\xdf3\xe9\x05G\xd0\x8c\xfax\xdf^\x1cY\xe6%\x0c&t\x81Z\x96)'
# iv = b'\t\xaa\xd4%\xcb\xea\xa5\xa1\xbbe\x95\xc4 \xa7\xed\xec'
#
# print(decrypt_aes_cbc(key, iv, encrypted_data))

server_info = {
    'hi': "hi there"
}

server_info = {**server_info, **{'server_id': 'server_id', 'aes_key': 'aes_key'}}
print(server_info)
import base64
import binascii

from Crypto.Random import get_random_bytes

from lib.utils import encrypt_aes_cbc, decrypt_aes_cbc, hash_password
from lib.config import salt

# password = 'Avocado&Salt4Me'
# hash_password = hash_password(password)
#
# message = "hi there!".encode('utf-8')
# iv, encrypted_message = encrypt_aes_cbc(hash_password, message)
# decrypted_message = decrypt_aes_cbc(hash_password, iv, encrypted_message)
#
# print('hash_password: ', hash_password)
# print('iv: ', iv)
# print('decrypted_message: ', decrypted_message)

server_aes_key = b'\x1e\x82k\x08\x06Q\xc5\xb5.\x81t\xf3\xfb\xa5\xa0\t\xd5\xfd\xb6\xfb\xe6k\xbef\xe7n@&?\xa6G4'
auth_iv = b'*ub\xb6T\xc0\xb8\xa0}W\x9f\x00\xa9X\xa2;'
encrypted_version = b'r\x8b\x805\x985\xd3$\xd1ac\xcaj\xa5%\x8b'
encrypted_client_id = b'P%\x84,\xfe\xa3\x9e\xe1EO\xbe\xcdR\xfb\xc6\xdb\x9f\xdfr\x15\xf2d\xbeAM\x0e\xd2\xfd\xac\xd0O9vS\xadO\x93\xd8,\xb0\x8d\xd3\x97\xb1\x9b\xb6\t\xbe'

version = decrypt_aes_cbc(server_aes_key, auth_iv, encrypted_version)
client_id = decrypt_aes_cbc(server_aes_key, auth_iv, encrypted_client_id)
print(version)

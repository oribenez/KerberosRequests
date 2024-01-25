import time

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad

from lib.utils import decrypt_aes_cbc, color, BLUE

#
# def encrypt_aes_cbc(key: bytes, data: bytes) -> (bytes, bytes):
#     cipher = AES.new(key, AES.MODE_CBC)
#     ciphered_data = cipher.encrypt(pad(data, AES.block_size))
#
#     return cipher.iv, ciphered_data
#
#
# key1 = get_random_bytes(32)
# data1 = get_random_bytes(32)
# iv, encrypted_data = encrypt_aes_cbc(key1, data1)
#
# print(color("Lengths:", BLUE))
# print(f"key={len(key1)}")
# print(f"data={len(data1)}")
# print(f"iv={len(iv)}")
# print(f"encrypted_data={len(encrypted_data)}")


for i in range(2):
    print(i)

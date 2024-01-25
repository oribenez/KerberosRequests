"""
Module: keys.py

This module defines the Keys class, which manages the storage and retrieval of symmetric keys for secure communication.
this class give the user an option to send messages without asking for new symmetric key from KDC and using the old one.

Classes:
- Keys: Manages a list of keys associated with Messaging servers.

Methods:
- __init__: Initializes an instance of the Keys class.
- add_key: Adds a new key to the key database, removing any old key with the same server_id.
- remove_key: Removes a key from the key database.
- get_key_by_server_id: Retrieves a key based on the server_id.
"""


class Keys:
    def __init__(self):
        self.keys = []

    def add_key(self, key):

        # remove old key with same server_id if exist
        server_id = key['server_id']
        old_key = self.get_key_by_server_id(server_id)
        if old_key:
            self.remove_key(old_key)

        # add new key to keys db
        self.keys += [key]

    def remove_key(self, key):
        self.keys.remove(key)

    def get_key_by_server_id(self, server_id):
        for key in self.keys:
            if key['server_id'] == server_id:
                return key

        return None









import time


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









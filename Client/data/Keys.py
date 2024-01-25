import time


# def is_expired(key):
#     now = time.time()
#     expiration_time = symmetric_keys['ticket']['expiration_time']
#
#     if now > expiration_time:
#         return True
#
#     return False
#

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
                # FIXME: the expiration_time is in bytes, that is not good we need too decrypt it but we cant so
                # I need to check this how I can know the expiration time of a ticket
                # maybe I need to define the exp_time as global var
                # if not is_expired(ticket_and_key):
                #     self.remove_ticket_and_key(ticket_and_key)
                # else:
                #     return ticket_and_key
                return key

        return None

    # def get_aes_key(self, server_id):
    #     ticket_and_key = self.get_ticket_and_key_by_server_id(server_id)
    #     if is_expired(ticket_and_key):
    #         self.remove_ticket_and_key(ticket_and_key)
    #         return None
    #
    #     aes_key = ticket_and_key['symmetric_key']['aes_key']
    #
    #     return aes_key










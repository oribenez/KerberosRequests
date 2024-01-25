import time


def is_expired(ticket):
    now = time.time()
    expiration_time = ticket['expiration_time']

    if now > expiration_time:
        return True

    return False


class Tickets:
    def __init__(self):
        self.tickets_list = []

    def add_ticket(self, ticket):
        # make sure there is not more tickets for this client
        client_id = ticket['client_id']
        old_ticket = self.get_ticket_by_client_id(client_id)
        if old_ticket:
            self.remove_ticket(old_ticket)

        # add the new ticket
        self.tickets_list += [ticket]

    def remove_ticket(self, ticket):
        self.tickets_list.remove(ticket)

    def get_ticket_by_client_id(self, client_id):
        for ticket in self.tickets_list:
            if ticket['client_id'] == client_id:
                return ticket

        return None

    def get_aes_key(self, client_id):
        ticket = self.get_ticket_by_client_id(client_id)
        if is_expired(ticket):
            self.remove_ticket(ticket)
            return None

        aes_key = ticket['aes_key']

        return aes_key










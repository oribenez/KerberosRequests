import time


def is_expired(ticket):
    """
    Check if the ticket has expired.

    Args:
        ticket (dict): Ticket information.

    Returns:
        bool: True if the ticket has expired, False otherwise.
    """

    now = time.time()
    expiration_time = ticket['expiration_time']

    if now > expiration_time:
        return True

    return False


class Tickets:
    """
        A class representing a collection of tickets for communication sessions.

        Tickets are used to store information related to client-server communication,
        including AES keys and expiration times.

        Attributes:
            tickets_list (list): A list to store ticket information.

        Methods:
            __init__(self): Initializes a Tickets object with an empty list.
            add_ticket(self, ticket): Adds a ticket, replacing any existing ticket for the same client.
            remove_ticket(self, ticket): Removes a ticket from the list.
            get_ticket_by_client_id(self, client_id): Retrieves a ticket based on the client ID.
            get_aes_key(self, client_id): Retrieves the AES key associated with a client ID, checking for expiration.
        """

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










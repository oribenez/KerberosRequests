from MessagesServer.data.Tickets import Tickets

db = {}


def load_db(server_info_init=None):
    """
    Load the database with the initial server information and an empty Tickets object.

    Args:
        server_info_init: Initial server information.
    """

    global db
    db = {
        'server_info': server_info_init.copy(),
        'tickets': Tickets()
    }

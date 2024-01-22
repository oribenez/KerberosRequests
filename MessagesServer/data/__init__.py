from MessagesServer.data.Tickets import Tickets

db = {}


def load_db(server_info_init=None):
    global db
    db = {
        'server_info': server_info_init.copy(),
        'tickets': Tickets()
    }

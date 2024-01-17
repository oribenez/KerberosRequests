from KDC.db.models.Clients import Clients
from KDC.db.models.Servers import Servers

db = {}


def load_db():
    global db
    db = {
        'clients': Clients(),
        'servers': Servers()
    }

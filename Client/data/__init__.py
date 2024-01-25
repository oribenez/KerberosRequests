from Client.data.Keys import Keys

db = {}


def load_db():
    global db
    db = {
        'keys': Keys()
    }

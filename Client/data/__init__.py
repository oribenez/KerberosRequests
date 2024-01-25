from Client.data.Keys import Keys

db = {}


def load_db():
    """
        Initializes the global database (db).

        The database includes:
        - 'keys': An instance of the Keys class for managing symmetric keys.

        """

    global db
    db = {
        'keys': Keys()
    }

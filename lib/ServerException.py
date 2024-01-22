class ServerException(Exception):
    def __init__(self, message="Server responded with an error"):
        self.message = message
        super().__init__(self.message)


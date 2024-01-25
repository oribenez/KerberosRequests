"""
ServerException: Exception
    Custom exception class for handling server-related errors.

Attributes:
    - message (str): Error message associated with the exception.

This exception is raised when the server responds with an error, providing a standardized way to handle server-related issues in the application.
"""


class ServerException(Exception):
    def __init__(self, message="Server responded with an error"):
        self.message = message
        super().__init__(self.message)


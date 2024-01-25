"""
Module: models.py

This module defines a custom exception class, RecordAlreadyExist.
"""


class RecordAlreadyExist(Exception):
    def __init__(self, message="Error: record already exist"):
        self.message = message
        super().__init__(self.message)
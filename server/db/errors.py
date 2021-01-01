"""
File: errors.py
---------------

All of the database errors for the project.
"""
class LockError(ValueError):
    """
    Unable to acquire or release the lock.
    """


class UserExistsError(KeyError):
    """
    The user already exists in the database.
    """
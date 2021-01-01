"""
File: utils.py
--------------

Contains utility classes and functions for database interactions.
"""
from typing import TypedDict


class User(TypedDict):
    display_name: str
    slack_id: str
    first_name: str
    last_name: str


def dict_factory(cursor, row):
    """
    Used to return query results as dictionaries instead of tuples.
    https://stackoverflow.com/questions/3300464/how-can-i-get-dict-from-sqlite-query
    """
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

"""
File: db.py
-----------

Handles interactions with the database.
"""
from flask import current_app
from unqlite import UnQLite

DB_PATH = '{root}/stories.db'
class LockError(ValueError):
    """
    Unable to acquire or release the lock.
    """

def connect():
    """
    Connects to the database and returns the database connection.
    """
    return UnQLite(DB_PATH.format(root=current_app.root_path))


def unlock_id(story_id: int, username: str):
    """
    Unlocks the story with the specified id if it is owned by the specified
    user.

    Arguments
    ---------
    story_id -- The id of the story to unlock.
    username -- The user who currently has locked the story.
    """
    db = connect()

    with db.transaction():
        stories = db.collection('stories')
        target_story = stories.fetch(story_id)

        if target_story['locked']:
            if target_story['locked_by'] == username:
                target_story['locked'] = False
                target_story['locked_by'] = None
            else:
                raise LockError("Can't unlock a story that you didn't lock.")
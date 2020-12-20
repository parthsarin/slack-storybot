"""
File: db.py
-----------

Handles interactions with the database.
"""
from flask import current_app
from unqlite import UnQLite
from typing import Callable

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


def get_stories(filter_criteria: Callable[[dict], bool] = lambda d: True):
    """
    Returns all stories that match the filter criteria.
    """
    db = connect()

    with db.transaction():
        stories = db.collection('stories')
        return stories.filter(filter_criteria)


def lock_story(story, username: str):
    """
    Locks the story that is passed in by the specified user.

    Arguments
    ---------
    story -- The UnQLite story object to lock.
    username -- The user who is locking the story.
    """
    story['locked'] = True
    story['locked_by'] = username


def unlock_story(story):
    """
    Unocks the story that is passed in.

    Arguments
    ---------
    story -- The UnQLite story object to unlock.
    username -- The user who is locking the story.
    """
    story['locked'] = False
    story['locked_by'] = None


def lock_id(story_id: int, username: str):
    """
    Locks the story with the specified id by the specified user.

    Arguments
    ---------
    story_id -- The id of the story to unlock.
    username -- The user who wants to lock the story.
    """
    db = connect()

    with db.transaction():
        stories = db.collection('stories')
        target_story = stories.fetch(story_id)

        if not target_story['locked']:
            lock_story(target_story, username)
        else:
            raise LockError("This story is already locked.")


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
                unlock_story(target_story)
            else:
                raise LockError("Can't unlock a story that you didn't lock.")

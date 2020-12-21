"""
File: db.py
-----------

Handles interactions with the database.
"""
from flask import current_app
from unqlite import UnQLite
from typing import Callable
from datetime import datetime, timedelta

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


def get_story(story_id: int) -> int:
    """
    Returns the story at the given id. 
    """
    db = connect()

    with db.transaction():
        stories = db.collection('stories')
        return stories.fetch(story_id)


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
    story['locked_at'] = datetime.now()


def unlock_story(story):
    """
    Unlocks the story that is passed in.

    Arguments
    ---------
    story -- The UnQLite story object to unlock.
    """
    story['locked'] = False
    story['locked_by'] = None
    story['locked_at'] = None


def lock_id(story_id: int, username: str):
    """
    Locks the story with the specified id by the specified user.

    Arguments
    ---------
    story_id -- The id of the story to unlock.
    username -- The user who wants to lock the story.
    """
    print(f"Locking {story_id} for {username}")
    db = connect()

    with db.transaction():
        stories = db.collection('stories')
        target_story = stories.fetch(story_id)

        if not target_story['locked']:
            lock_story(target_story, username)
            stories.update(story_id, target_story)
        else:
            raise LockError("This story is already locked.")
    
    with db.transaction():
        stories = db.collection('stories')
        target_story = stories.fetch(story_id)
        print(target_story)


def add_line(story_id: int, username: str, line: str):
    """
    Adds the given line to the story_id if the user has locked it.

    Arguments
    ---------
    story_id -- The id of the story that the user is writing in.
    username -- The user who is editing the story.
    line -- The line that the user has written.
    """
    db = connect()

    with db.transaction():
        stories = db.collection('stories')
        story = stories.fetch(story_id)

        if story['locked'] and story['locked_by'] == username:
            story['lines'].append({
                'text': line,
                'author': username
            })
            stories.update(story_id, story)
        else:
            raise LockError("Can't write to a story you haven't locked.")


def create_new_story(max_lines: int, first_line: dict):
    """
    Creates a new story with the specified number of maximum lines and the
    given first line.

    Arguments
    ---------
    max_lines -- The maximum number of lines before this story is posted into
        Slack.
    first_line -- The first line of the story, in the correct format (per
        db_structure.jsonc)
    """
    new_story = {
        'max_lines': max_lines,
        'locked': False,
        'locked_by': None,
        'lines': [
            first_line
        ]
    }

    db = connect()

    with db.transaction():
        stories = db.collection('stories')
        stories.store([new_story])


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
                stories.update(story_id, target_story)
            else:
                raise LockError("Can't unlock a story that you didn't lock.")


def is_locked(story_id: int, sunset_time: timedelta) -> bool:
    """
    Checks if the story is locked (either that it is locked or it has 
    sunsetted). Unlocks the story if it has sunsetted.
    """
    db = connect()

    with db.transaction():
        stories = db.collection('stories')
        story = stories.fetch(story_id)

        if not story['is_locked']:
            return False
        
        # Has the sunset time elapsed?
        if datetime.now() - story['locked_at'] > sunset_time:
            # Unlock the story
            unlock_story(story)
            stories.update(story_id, story)
        
        return story['is_locked']
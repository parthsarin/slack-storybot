"""
File: db.py
-----------

Handles interactions with the database.
"""
from flask import current_app
from unqlite import UnQLite
from typing import Callable, Set, TypedDict
import time

DB_PATH = '{root}/stories.db'
STORY_EDITING_SUNSET = 180 # seconds after which the story will unlock
class LockError(ValueError):
    """
    Unable to acquire or release the lock.
    """

class UserExistsError(KeyError):
    """
    The user already exists in the database.
    """


class User(TypedDict):
    display_name: str
    slack_id: str
    first_name: str
    last_name: str


def connect():
    """
    Connects to the database and returns the database connection.
    """
    return UnQLite(DB_PATH.format(root=current_app.root_path))


def add_user(user: User):
    """
    Writes the user to the database if there's no matching entry.
    """
    db = connect()

    with db.transaction():
        users = db.collection('users')
        same_name = users.filter(
            lambda u: u['display_name'] == user.get('display_name')
        )
        if same_name:
            raise UserExistsError("The user already exists.")
        else:
            users.store([user])


def get_valid_stories(username: str, story_id_history: Set[int]):
    """
    Returns all stories that match the filter criteria.
    """
    db = connect()

    output = []
    with db.transaction():
        stories = db.collection('stories')
        for story in stories.all():
            # Should we include the story?
            in_progress = len(story['lines']) < story['max_lines']
            user_contributed = username in {
                line['author']
                for line in story['lines']
                if 'author' in line
            }
            is_fresh = story['__id'] not in story_id_history

            if not story['locked']:
                is_locked = False
            else:
                # Did I lock this story?
                self_lock = story['locked_by'] == username
                # Has the sunset time elapsed?
                sunset_passed = time.time() - story['locked_at'] \
                                > STORY_EDITING_SUNSET
                
                if self_lock or sunset_passed:
                    # Unlock the story
                    unlock_story(story)
                    stories.update(story['__id'], story)

                is_locked = story['locked']

            include_story = (
                in_progress
                and (not is_locked)
                and (not user_contributed)
                and is_fresh
            )

            if include_story:
                output.append(story)

    return output


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
    story['locked_at'] = time.time()


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
    db = connect()

    with db.transaction():
        stories = db.collection('stories')
        target_story = stories.fetch(story_id)

        if not target_story['locked']:
            lock_story(target_story, username)
            stories.update(story_id, target_story)
        else:
            raise LockError("This story is already locked.")


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
            unlock_story(story)
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

        if not target_story:
            # Maybe id == -1?
            return

        if target_story['locked']:
            if target_story['locked_by'] == username:
                unlock_story(target_story)
                stories.update(story_id, target_story)
            else:
                raise LockError("Can't unlock a story that you didn't lock.")

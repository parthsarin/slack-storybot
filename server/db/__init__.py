"""
File: db.py
-----------

Handles interactions with the database.
"""
from flask import current_app, g
from unqlite import UnQLite
from typing import Callable, Set, Union
from datetime import datetime
import sqlite3

from .errors import *
from .utils import *


DB_PATH = '{root}/stories.db'
STORY_EDITING_SUNSET = 180 # seconds after which the story will unlock


def connect(row_factory=None):
    """
    Connects to the database and returns the database connection.
    """
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(
            DB_PATH.format(root=current_app.root_path)
        )
    if row_factory is not None:
        db.row_factory = row_factory
    return db


def query_db(query, args=(), one=False, row_factory=None):
    """
    Executes a single query on the database.
    """
    cur = connect(row_factory).execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def add_user(user: User):
    """
    Writes the user to the database if there's no matching entry.
    """
    same_name = query_db(
        """
        SELECT * FROM Users WHERE display_name=?
        """,
        (user.get('display_name'),),
        one=True
    )

    if same_name:
        raise UserExistsError("The user already exists.")
    else:
        query_db(
            """
            INSERT INTO Users (display_name, slack_id, first_name, last_name)
            VALUES (?, ?, ?, ?)
            """,
            (
                user.get('display_name'),
                user.get('slack_id'),
                user.get('first_name'),
                user.get('last_name')
            )
        )


def get_user_slack_id(display_name: str) -> Union[str, None]:
    """
    Gets the user's slack id from the database.

    Arguments
    ---------
    display_name -- The display name of the user that is being searched for.
    """
    return query_db(
        """
        SELECT slack_id FROM Users WHERE display_name=?
        """,
        (display_name,),
        one=True
    )


def get_valid_stories(username: str, story_id_history: Set[int]):
    """
    Returns all stories that match the filter criteria.
    """
    author_id = query_db(
        "SELECT id FROM Users WHERE display_name = ?;", 
        (username,),
        one=True
    )[0]

    unfinished_stories = query_db(
        """
        SELECT
            stories.*
        FROM Stories stories
        LEFT JOIN StoryLines lines
            ON stories.id = lines.story
        GROUP BY lines.story
        HAVING COUNT(lines.story) < stories.max_lines;
        """,
        row_factory=dict_factory
    )

    output = []
    for story in unfinished_stories:
        user_contributed = bool(query_db(
            "SELECT * FROM StoryLines WHERE story = ? AND author = ?",
            (story['id'], author_id)
        ))
        is_fresh = story['id'] not in story_id_history

        if not story['locked']:
            is_locked = False
        else:
            # Did I lock this story?
            self_lock = story['locked_by'] == author_id

            # Has the sunset time elapsed?
            date_format = r'%Y-%m-%d %H:%M:%S.%f'
            locked_at = datetime.strptime(story['locked_at'], date_format)
            diff = datetime.now() - locked_at
            sunset_passed = diff.total_seconds() > STORY_EDITING_SUNSET
            
            if self_lock or sunset_passed:
                # Unlock the story
                __unlock_id_nocheck(story['id'])
                is_locked = False
            else:
                is_locked = True

        include_story = (
            (not is_locked)
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
    story = query_db(
        """
        SELECT * FROM Stories WHERE id=?
        """,
        (story_id,),
        one=True,
        row_factory=dict_factory
    )
    if not story:
        return None

    lines = query_db(
        """
        SELECT b.line_idx, b.text, c.display_name, c.slack_id
        FROM Stories a
        LEFT OUTER JOIN StoryLines b
            ON a.id = b.story
        LEFT OUTER JOIN Users c
            ON b.author = c.id
        WHERE a.id = ?;
        """,
        (story_id,),
        row_factory=dict_factory
    )
    
    lines = sorted(lines, key=lambda line: line['line_idx'])
    story['lines'] = lines

    return story


def get_last_line(story_id: int) -> dict:
    """
    Retrieves the last line for the story.

    Arguments
    ---------
    story_id -- The id of the story to fetch the last line for.

    Returns
    -------
    {
        'author': Line author's display name,
        'text': Line text
    }
    """
    return query_db(
        """
        SELECT c.display_name AS username, a.text, a.line_idx
        FROM StoryLines a
        LEFT OUTER JOIN StoryLines b
          ON a.story = b.story AND a.line_idx < b.line_idx
        LEFT JOIN Users c
          ON a.author = c.id
        WHERE b.id is NULL AND a.story = ?;
        """,
        (story_id,),
        one=True,
        row_factory=dict_factory
    )


def lock_id(story_id: int, username: str):
    """
    Locks the story with the specified id by the specified user.

    Arguments
    ---------
    story_id -- The id of the story to unlock.
    username -- The user who wants to lock the story.
    """
    story = query_db(
        "SELECT * FROM Stories WHERE id=?", 
        (story_id,),
        one=True,
        row_factory=dict_factory
    )
    
    if not story:
        return

    if not story['locked']:
        query_db(
            """
            UPDATE Stories
            SET 
                locked=TRUE, 
                locked_by=(SELECT id from Users WHERE display_name=?),
                locked_at=STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')
            WHERE id = ?;
            """,
            (username, story_id)
        )
    else:
        raise LockError("This story is already locked.")


def __unlock_id_nocheck(story_id: int):
    """
    Unlocks the story with the specified id regardless of who has locked it.

    Arguments
    ---------
    story_id -- The id of the story to unlock.
    """
    query_db(
        """
        UPDATE Stories
        SET 
            locked=FALSE,
            locked_by=NULL,
            locked_at=NULL
        WHERE id = ?;
        """,
        (story_id,)
    )


def unlock_id(story_id: int, username: str):
    """
    Unlocks the story with the specified id if it is owned by the specified
    user.

    Arguments
    ---------
    story_id -- The id of the story to unlock.
    username -- The user who currently has locked the story.
    """
    story = query_db(
        """
        SELECT a.locked, b.display_name
        FROM Stories a
        LEFT OUTER JOIN Users b
            ON a.locked_by = b.id
        WHERE a.id = ?;
        """, 
        (story_id,),
        True,
        row_factory=dict_factory
    )

    if not story:
        # Maybe id == -1?
        return

    if story['locked']:
        if story['display_name'] == username:
            __unlock_id_nocheck(story_id)
        else:
            raise LockError("Can't unlock a story that you didn't lock.")


def add_line(story_id: int, username: str, line: str):
    """
    Adds the given line to the story_id if the user has locked it.

    Arguments
    ---------
    story_id -- The id of the story that the user is writing in.
    username -- The user who is editing the story.
    line -- The line that the user has written.
    """
    next_idx = query_db(
        """
        SELECT MAX(b.line_idx)
        FROM Stories a
        LEFT JOIN StoryLines b
            ON a.id = b.story
        GROUP BY b.story
        HAVING
            a.locked = TRUE
            AND a.locked_by = (SELECT id FROM Users WHERE display_name = ?)
            AND a.id = ?;
        """,
        (username, story_id),
        True
    )[0]

    try:
        next_idx += 1
    except TypeError:
        raise LockError("Can't write to a story you haven't locked.")

    query_db(
        """
        INSERT INTO StoryLines (author, story, line_idx, text)
        VALUES ((SELECT id FROM Users WHERE display_name = ?), ?, ?, ?)
        """,
        (username, story_id, next_idx, line)
    )
    unlock_id(story_id, username)


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
    cursor = connect().cursor()
    
    # Insert the story metadata
    cursor.execute(
        """
        INSERT INTO Stories (max_lines, locked, locked_by, locked_at)
        VALUES (?, ?, ?, ?)
        """,
        (max_lines, False, None, None)
    )
    story_id = cursor.lastrowid
    cursor.close()

    # Insert the line
    query_db(
        """
        INSERT INTO StoryLines (author, story, line_idx, text)
        VALUES ((SELECT id FROM Users WHERE display_name = ?), ?, ?, ?)
        """,
        (first_line.get('author'), story_id, 0, first_line['text'])
    )

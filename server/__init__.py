"""
File: __init__.py
-----------------

The Flask application endpoints which integrate with Slack to post the stories
in the #stories channel.
"""
import os
from functools import partial
import random
from typing import TypedDict

from flask import Flask, send_from_directory, request
from .db import unlock_id, lock_id, get_stories

app = Flask(__name__, static_folder='../client/build')
SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')


class LineResponse(TypedDict):
    prevLine: str
    prevAuthor: str
    currIndex: int
    maxLines: int


def valid_user_story(story, username: str) -> bool:
    """
    Determines whether this is a valid story that the user can claim.

    Arguments
    ---------
    story -- The story to check.
    username -- The user who is trying to claim the story.
    """
    is_locked = story['locked']
    user_contributed = username in {
        line['author'] 
        for line in story['lines']
        if 'author' in line
    }

    return (not is_locked) and (not user_contributed)


def prepare_story_response(story) -> LineResponse:
    """
    Prepares the story object to be injected into the state of the client
    application.
    """
    last_line = story['lines'][-1]
    output = {
        'prevLine': last_line['text'],
        'currIndex': len(story['lines']) + 1,
        'maxLines': story['max_lines']
    }

    if 'author' in last_line:
        output['prevAuthor'] = last_line['author']

    return LineResponse(output)


@app.route('/api/get_line', methods=['POST'])
def get_line():
    username = request.json.get('username')
    story_id = request.json.get('storyId')

    # Unlock the story that the user is currently holding
    if story_id:
        unlock_id(story_id, username)
    
    # Pick a story 
    filter_criteria = partial(valid_user_story, username=username)
    story_options = get_stories(filter_criteria)
    try:
        story = random.choice(story_options)
    except IndexError:
        return {'error': 'No more stories left!'}
    
    # Lock the story
    lock_id(story['__id'], username)

    return prepare_story_response(story)

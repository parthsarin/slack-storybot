"""
File: __init__.py
-----------------

The Flask application endpoints which integrate with Slack to post the stories
in the #stories channel.
"""
import os
from functools import partial
import random
from typing import TypedDict, Set, List
import requests
from datetime import timedelta

from flask import Flask, send_from_directory, request
from .db import (
    unlock_id, lock_id, get_stories, add_line, create_new_story, get_story
)

app = Flask(__name__, static_folder='../client/build')
SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')
MAX_LINES = 5
STORY_EDITING_SUNSET = timedelta(minutes=3) # after which the story will unlock

class LineResponse(TypedDict):
    prevLine: str
    prevAuthor: str
    currIndex: int
    maxLines: int
    storyId: int


def valid_user_story(story, username: str, story_id_history: Set[int]) -> bool:
    """
    Determines whether this is a valid story that the user can claim.

    Arguments
    ---------
    story -- The story to check.
    story_id_history -- The past story IDs that the user has seen.
    username -- The user who is trying to claim the story.
    """
    is_locked = story['locked']
    user_contributed = username in {
        line['author'] 
        for line in story['lines']
        if 'author' in line
    }
    is_fresh = story['__id'] not in story_id_history

    return (not is_locked) and (not user_contributed) and is_fresh


def prepare_story_response(story) -> LineResponse:
    """
    Prepares the story object to be injected into the state of the client
    application.
    """
    last_line = story['lines'][-1]
    output = {
        'prevLine': last_line['text'],
        'currIndex': len(story['lines']) + 1,
        'maxLines': story['max_lines'],
        'storyId': story['__id']
    }

    if 'author' in last_line:
        output['prevAuthor'] = last_line['author']

    return LineResponse(output)


def prepare_slack_message(story_lines: List[dict]) -> str:
    """
    Compiles each of the story lines into a multiline string for posting in the
    Slack channel.
    """
    output = []
    for line in story_lines:
        sub_line = f"{line['text']}"
        if 'author' in line:
            sub_line += f" (@{line['author']})"
        output.append(sub_line)
    
    return '\n'.join(output)


@app.route('/api/get_line', methods=['POST'])
def get_line():
    username = request.json.get('username')
    story_id = request.json.get('storyId')
    story_id_history = request.json.get('storyIdHistory', [])
    story_id_history = set(story_id_history) | {story_id}

    # Unlock the story that the user is currently holding
    if story_id:
        unlock_id(story_id, username)
    
    # Pick a story 
    filter_criteria = partial(
        valid_user_story, 
        username=username, 
        story_id_history=story_id_history
    )
    story_options = get_stories(filter_criteria)
    try:
        story = random.choice(story_options)
    except IndexError:
        # Tell the application to write a new story
        return {
            'prevLine': '',
            'prevAuthor': '',
            'currIndex': 1,
            'maxLines': MAX_LINES,
            'writingNewStory': True,
            'storyId': -1
        }
    
    # Lock the story
    lock_id(story['__id'], username)

    return prepare_story_response(story)


@app.route('/api/submit_line', methods=['POST'])
def submit_line():
    username = request.json.get('username')
    story_id = request.json.get('storyId')
    line = request.json.get('line')

    if not isinstance(story_id, int):
        return {'error': 'Malformed request - storyId should be an integer.'}
    
    if story_id == -1:
        # Create new story
        create_new_story(MAX_LINES, {
            'text': line,
            'author': username
        })
        return {'success': True}

    # Add the line and post in the Slack if this was the last line
    add_line(story_id, username, line)
    story = get_story(story_id)
    if story['max_lines'] == len(story['lines']):
        requests.post(
            SLACK_WEBHOOK, 
            data=prepare_slack_message(story['lines']),
            headers={
                'Content-Type': 'application/json'
            }
        )
        return {'success': True}

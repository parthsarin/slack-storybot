"""
File: __init__.py
-----------------

The Flask application endpoints which integrate with Slack to post the stories
in the #stories channel.
"""
import os
from functools import partial
import random
from typing import TypedDict, List, Union
import requests
import sys

from flask import Flask, send_from_directory, request
from .db import (
    unlock_id, lock_id, get_valid_stories, add_line, create_new_story, 
    get_story, User, UserExistsError, add_user, get_user_slack_id
)

app = Flask(__name__, static_folder='../client/build')
SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')
SLACK_AUTH_TOKEN = os.environ.get('SLACK_AUTH_TOKEN')
MAX_LINES = 5

class ClientUser(TypedDict):
    username: str
    profile_image: str
    first_name: str
    last_name: str
    slack_id: str


class LineResponse(TypedDict):
    prevLine: str
    prevAuthor: Union[ClientUser, None]
    currIndex: int
    maxLines: int
    storyId: int


def get_full_user(prev_user_username: Union[str, None]) -> \
    Union[ClientUser, None]:
    """
    Gets a full user object by querying the slack API.
    """
    if not prev_user_username:
        return None

    # Get the slack ID from the database
    slack_id = get_user_slack_id(prev_user_username)

    # Query the slack API
    r = requests.post(
        'https://slack.com/api/users.info',
        data={'user': slack_id},
        headers={
            'Authorization': f'Bearer {SLACK_AUTH_TOKEN}'
        }
    )

    if r.ok and (data := r.json())['ok']:
        slack_match = data['user']

        # Get the profile image if it's custom
        profile_image = None
        if slack_match['profile'].get('is_custom_image', False):
            profile_image = slack_match['profile']['image_192']

        return ClientUser({
            'username': prev_user_username,
            'profile_image': profile_image,
            'first_name': slack_match['profile'].get('first_name'),
            'last_name': slack_match['profile'].get('last_name'),
            'slack_id': slack_match['id']
        })
    else:
        return None



def prepare_story_response(story) -> LineResponse:
    """
    Prepares the story object to be injected into the state of the client
    application.
    """
    last_line = story['lines'][-1] 

    return LineResponse({
        'prevLine': last_line['text'],
        'prevAuthor': get_full_user(last_line.get('author')),
        'currIndex': len(story['lines']) + 1,
        'maxLines': story['max_lines'],
        'storyId': story['__id'],
    })


def prepare_slack_message(story_lines: List[dict]) -> str:
    """
    Compiles each of the story lines into a multiline string for posting in the
    Slack channel.
    """
    output = []
    for line in story_lines:
        sub_line = f"{line['text']}"
        if 'author' in line and (slack_id := get_user_slack_id(line['author'])):
            sub_line += f" (<@{slack_id}>)"
        output.append(sub_line)
    
    return {'text': '\n'.join(output)}


def slack_resp_to_user(slack_match: dict) -> User:
    """
    Repackages the Slack API response into a User object.
    """
    return User({
        'display_name': slack_match['profile'].get('display_name'),
        'slack_id': slack_match['id'],
        'first_name': slack_match['profile'].get('first_name'),
        'last_name': slack_match['profile'].get('last_name'),
    })


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
    story_options = get_valid_stories(username, story_id_history)
    try:
        story = random.choice(story_options)
    except IndexError:
        # Tell the application to write a new story
        return {
            'prevLine': '',
            'prevAuthor': None,
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
            json=prepare_slack_message(story['lines']),
            headers={
                'Content-Type': 'application/json'
            }
        )
    return {'success': True}


@app.route('/api/release_story', methods=['POST'])
def release_story():
    username = request.json.get('username')
    story_id = request.json.get('storyId')

    # Unlock the story that the user is currently holding
    if story_id:
        unlock_id(story_id, username)

    return {'success': True}


@app.route('/api/verify_username', methods=['POST'])
def verify_username():
    username = request.json.get('username')

    # Get information about this user and store it in the database
    all_users = requests.post(
        'https://slack.com/api/users.list',
        headers={
            'Authorization': f'Bearer {SLACK_AUTH_TOKEN}'
        }
    )
    if not all_users.ok:
        return {'error': 'Could not verify user. Try again later.'}, 500
    
    # Filter to the users whose display name matches
    all_users = all_users.json()
    def user_matches(user):
        """
        Returns whether a user matches the queried username.
        """
        if display_name := user['profile'].get('display_name'):
            return display_name == username
        else:
            return user['profile'].get('real_name') == username
    
    matching_users = filter(user_matches, all_users['members'])
    try:
        match = next(matching_users)
    except StopIteration:
        # No matching users
        return {
            'error': ("Hmm... I couldn't find any matching users. Did you "
                      "enter your display name correctly?")
        }
    
    # Write the match to the database
    user = slack_resp_to_user(match)
    try:
        add_user(user)
    except UserExistsError:
        pass
    
    # Reformat to send to user
    user['username'] = user['display_name']
    del user['display_name']
    del user['slack_id']

    return {'success': True, 'user': user}

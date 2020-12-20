"""
File: __init__.py
-----------------

The Flask application endpoints which integrate with Slack to post the stories
in the #stories channel.
"""
import os
from flask import Flask, send_from_directory, request

app = Flask(__name__, static_folder='../client/build')

SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')

@app.route('/api/get_line', methods=['POST'])
def get_line():
    username = request.json.get('username')
    story_id = request.json.get('storyId')
    
    return {
        'prevLine': 'Once upon a time, there was an amazing unicorn named Ruth Bader Ginsburg.',
        'prevAuthor': 'Minerva McGonagall',
        'currIndex': 2,
        'maxLines': 10,
    }
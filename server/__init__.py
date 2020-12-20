"""
File: __init__.py
-----------------

The Flask application endpoints which integrate with Slack to post the stories
in the #stories channel.
"""
import os
from flask import Flask, send_from_directory

app = Flask(__name__, static_folder='../client/build')

SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK')
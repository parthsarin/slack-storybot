"""
File: app.py
------------

The Flask application endpoints which integrate with Slack to post the stories
in the #stories channel.
"""
import os
from flask import Flask

app = Flask(__name__, static_folder='../client/build')

@app.route('/')
def index():
    return app.send_static_file('index.html')
"""
File: add_empty_db.py
---------------------

Adds some initial prompts to the database.
"""
from unqlite import UnQLite

FIRST_LINES = [
    "I write this sitting in the kitchen sink.",
    "'Twas a dark and stormy night.",
    "In my younger and more vulnerable years my father gave me some advice that I've been turning over in my mind ever since.",
    "I am an invisible man."
]
MAX_LINES = 5
DB_FILE = 'stories.db'

def write():
    db = UnQLite(DB_FILE)

    for line in FIRST_LINES:
        with db.transaction():
            stories = db.collection('stories')
            stories.create()

            # Are there stories that have the same first line?
            same_first_line = stories.filter(
                lambda story: story['lines'][0].get('text') == line
            )
            if same_first_line:
                continue
            
            stories.store([
                {
                    "max_lines": MAX_LINES,
                    "locked": False,
                    "locked_by": None,
                    "lines": [
                        {
                            "text": line
                        }
                    ]
                }
            ])


if __name__ == '__main__':
    write()
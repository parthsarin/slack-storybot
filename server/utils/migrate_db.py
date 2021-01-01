"""
File: migrate_db.py
-------------------

Migrates the UnQLite database into a SQLite database.
"""
from unqlite import UnQLite
import sqlite3
import os
from datetime import datetime

UNQLITE_DB = 'stories.unqlite.db'
source_db = UnQLite(UNQLITE_DB)
SQLITE_DB = 'stories.db'

class SQLTransaction:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
    
    def __enter__(self):
        return self.conn.cursor()
    
    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.conn.commit()
    
    def close(self):
        self.conn.close()


try:
    os.remove(SQLITE_DB)
except FileNotFoundError:
    pass


db = SQLTransaction(SQLITE_DB)

def build_schema():
    with db as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Users (
                id           INTEGER PRIMARY KEY,
                display_name varchar(255),
                slack_id     varchar(255),
                first_name   varchar(255),
                last_name    varchar(255)
            );
            """
        )
        
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS Stories (
                id        INTEGER PRIMARY KEY,
                max_lines int DEFAULT 10,
                locked    bool DEFAULT FALSE,
                locked_by int DEFAULT NULL,
                locked_at timestamp DEFAULT(STRFTIME('%Y-%m-%d %H:%M:%f', 'NOW')),
            
                FOREIGN KEY (locked_by) REFERENCES Users(id)
            );
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS StoryLines (
                id       INTEGER PRIMARY KEY,
                author   int,
                story    int,
                line_idx int,
                text     tinytext,

                FOREIGN KEY (author) REFERENCES Users(id),
                FOREIGN KEY (story) REFERENCES Stories(id)
            );
            """
        )


def migrate_users():
    with source_db.transaction():
        users = source_db.collection('users').all()
    
    with db as cursor:
        for user in users:
            cursor.execute(
                """
                INSERT INTO Users (display_name, slack_id, first_name, last_name)
                VALUES (?, ?, ?, ?)
                """,
                (user['display_name'], user['slack_id'], user['first_name'], user['last_name'])
            )


def migrate_stories():
    with source_db.transaction():
        stories = source_db.collection('stories').all()
    
    with db as cursor:
        for story in stories:
            # First add to the stories
            cursor.execute(
                """
                INSERT INTO Stories (max_lines, locked, locked_by, locked_at)
                VALUES (?, ?, (SELECT id FROM Users WHERE display_name=?), ?);
                """,
                (story['max_lines'], story['locked'], story['locked_by'],
                datetime.fromtimestamp(story['locked_at']) \
                    if story['locked_at'] \
                    else None)
            )

            # Next, add the lines
            story_id = cursor.lastrowid
            lines = story['lines']
            for i, line in enumerate(lines):
                cursor.execute(
                    """
                    INSERT INTO StoryLines (author, story, line_idx, text)
                    VALUES (
                        (SELECT id FROM Users WHERE display_name=?),
                        ?,
                        ?,
                        ?
                    );
                    """,
                    (line.get('author'), story_id, i, line['text'])
                )


if __name__ == '__main__':    
    build_schema()
    migrate_users()
    migrate_stories()

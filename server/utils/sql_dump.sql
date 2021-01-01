-- SCHEMA
CREATE TABLE IF NOT EXISTS Users (
  id           INTEGER PRIMARY KEY,
  display_name varchar(255),
  slack_id     varchar(255),
  first_name   varchar(255),
  last_name    varchar(255)
);

CREATE TABLE IF NOT EXISTS Stories (
  id int AUTO_INCREMENT,
  max_lines int DEFAULT 10,
  locked bool   DEFAULT FALSE,
  locked_by int DEFAULT NULL,

  FOREIGN KEY (locked_by) REFERENCES Users(id),
  PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS StoryLines (
  id int AUTO_INCREMENT,
  author int,
  story int,
  line_idx int,
  text tinytext,

  FOREIGN KEY (author) REFERENCES Users(id),
  FOREIGN KEY (story) REFERENCES Stories(id),
  PRIMARY KEY (id)
);


-- Dummy data
INSERT INTO Users (display_name, slack_id) VALUES (NULL, NULL);
INSERT INTO Users (display_name, slack_id) VALUES ('Parth', '12345');
INSERT INTO Users (display_name, slack_id) VALUES ('Kaya', '45678');

INSERT INTO Stories (max_lines) VALUES (3);

INSERT INTO StoryLines (author, story, line_idx, text) VALUES (
    NULL,
    1,
    0,
    'Mary had a little lamb whose fleece was white as wool.'
);
INSERT INTO StoryLines (author, story, line_idx, text) VALUES (
    (SELECT id FROM Users WHERE display_name = 'Parth'),
    1,
    1,
    'And everywhere that Mary went that lamb was sure to go.'
);
INSERT INTO StoryLines (author, story, line_idx, text) VALUES (
    (SELECT id FROM Users WHERE display_name = 'Kaya'),
    1,
    2,
    'Baaaaaa.'
);

--- Operations

-- Get the last line of a story (this is actually wild)
SELECT a.* 
FROM StoryLines a
LEFT OUTER JOIN StoryLines b
  ON a.story = b.story AND a.line_idx < b.line_idx
WHERE b.id is NULL AND a.story = 1;

-- See which author locked the story
SELECT b.*
FROM Stories a
LEFT OUTER JOIN Users b
  ON a.locked_by = b.id
WHERE a.locked AND a.id = 1;

-- Get all lines of a story
SELECT a.id, a.max_lines, b.line_idx, b.text, c.display_name, c.slack_id
FROM Stories a
LEFT OUTER JOIN StoryLines b
  ON a.id = b.story
LEFT OUTER JOIN Users c
  ON b.author = c.id
WHERE a.id = 1;

-- Count number of lines written for a story
SELECT COUNT(line_idx)
FROM StoryLines
WHERE story = 1;
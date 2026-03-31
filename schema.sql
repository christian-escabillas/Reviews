CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE,
    password_hash TEXT
);

CREATE TABLE item (
    id INTEGER PRIMARY KEY,
    title TEXT,
    item_type TEXT CHECK(item_type IN ('movie', 'series', 'game', 'song'))
);

CREATE TABLE review (
    id INTEGER PRIMARY KEY,
    title TEXT,
    thoughts TEXT,
    rating INTEGER,
    user_id INTEGER REFERENCES users(id),
    item_id INTEGER REFERENCES item(id),
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE movie (
    id INTEGER PRIMARY KEY,
    movie_title TEXT,
    release_year INTEGER
);

CREATE TABLE series (
    id INTEGER PRIMARY KEY,
    series_title TEXT,
    release_year INTEGER
);

CREATE TABLE game (
    id INTEGER PRIMARY KEY,
    game_name TEXT,
    release_year INTEGER
);

CREATE TABLE song (
    id INTEGER PRIMARY KEY,
    song_title TEXT,
    singer TEXT
);

CREATE TABLE comments (
    id INTEGER PRIMARY KEY,
    review_id INTEGER REFERENCES review,
    user_id INTEGER REFERENCES users,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    comment TEXT
);
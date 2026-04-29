CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    username_lower TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL
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

CREATE TABLE review_votes (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  review_id INTEGER NOT NULL REFERENCES review(id) ON DELETE CASCADE,
  value INTEGER NOT NULL CHECK (value IN (-1, 1)),
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_id, review_id)
);

CREATE TABLE review_favorites (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  review_id INTEGER NOT NULL REFERENCES review(id) ON DELETE CASCADE,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (user_id, review_id)
);

CREATE INDEX ix_review_votes_review_id ON review_votes(review_id);
CREATE INDEX ix_review_votes_user_id ON review_votes(user_id);
CREATE INDEX ix_review_favs_review_id ON review_favorites(review_id);
CREATE INDEX ix_review_favs_user_id ON review_favorites(user_id);

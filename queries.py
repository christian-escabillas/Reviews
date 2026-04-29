from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Optional
import db

# Index
def get_index_reviews():
    sql = """
    SELECT r.id,
           r.title AS review_title,
           i.item_type,
           i.title AS item_title,
           u.username,
           u.id AS user_id,               -- reviewer user_id
           COUNT(c.id) AS comment_count,
           r.created_at
    FROM review r
    JOIN item i ON r.item_id = i.id
    JOIN users u ON r.user_id = u.id
    LEFT JOIN comments c ON r.id = c.review_id
    GROUP BY r.id, r.title, i.item_type, u.username, u.id
    ORDER BY r.created_at DESC
    """
    reviews = db.query(sql)

    review_list = []
    for review in reviews:
        review_dict = {
            'id': review['id'],
            'review_title': review['review_title'],
            'item_type': review['item_type'],
            'item_title': review['item_title'],
            'username': review['username'],
            'user_id': review['user_id'],  # reviewer’s id
            'comment_count': review['comment_count'],
            'created_at': review['created_at'],
            'comments': []
        }

        comment_sql = """
        SELECT
            c.id AS id,
            c.comment,
            u.username,
            u.id AS user_id
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.review_id = ?
        ORDER BY c.created_at DESC
        LIMIT 2
        """
        recent_comments = db.query(comment_sql, (review['id'],))
        review_dict['comments'] = recent_comments
        review_list.append(review_dict)

    for review_dict in review_list:
        rid = review_dict['id']
        vote_counts = get_review_vote_counts(rid)
        fav_count = get_review_favorite_count(rid)
        review_dict['upvotes'] = vote_counts['upvotes']
        review_dict['downvotes'] = vote_counts['downvotes']
        review_dict['score'] = vote_counts['score']
        review_dict['favorites'] = fav_count['favorites']

    return review_list

# Search
def search_items_and_reviews(item_type: str, query: str):
    sql = """
    SELECT
        i.id AS item_id,
        i.title AS item_title,
        i.item_type,
        r.id AS review_id,
        r.title AS review_title,
        r.rating,
        u.username AS review_username
    FROM item i
    LEFT JOIN review r ON r.item_id = i.id
    LEFT JOIN users u ON r.user_id = u.id
    WHERE i.item_type = ?
      AND (
        LOWER(TRIM(i.title)) LIKE LOWER(?)
        OR LOWER(COALESCE(TRIM(r.title), '')) LIKE LOWER(?)
      )
    ORDER BY i.title, r.id
    """
    params = [item_type, f"%{query}%", f"%{query}%"]
    return db.query(sql, params)

def search_items_and_reviews_all(query: str):
    sql = """
    SELECT i.id AS item_id,
           i.title AS item_title,
           i.item_type,
           r.id AS review_id,
           r.title AS review_title,
           r.rating,
           u.username AS review_username,
           r.created_at
    FROM item i
    LEFT JOIN review r ON r.item_id = i.id
    LEFT JOIN users u ON r.user_id = u.id
    WHERE LOWER(TRIM(i.title)) LIKE LOWER(?)
       OR LOWER(COALESCE(TRIM(r.title), '')) LIKE LOWER(?)
    ORDER BY r.created_at DESC, i.title, r.id
    """
    params = [f"%{query}%", f"%{query}%"]
    return db.query(sql, params)


# Items
def create_item(title: str, item_type: str):
    sql = "INSERT INTO item (title, item_type) VALUES (?, ?)"
    db.execute(sql, [title, item_type])

def get_items_by_type(item_type: str):
    sql = "SELECT id, title FROM item WHERE item_type = ?"
    return db.query(sql, [item_type])

def get_item_id_by_title_and_type(title: str, item_type: str):
    sql = "SELECT id FROM item WHERE LOWER(title) = LOWER(?) AND item_type = ?"
    rows = db.query(sql, [title, item_type])
    return rows[0]["id"] if rows else None

# Reviews
def create_review(title: str, thoughts: str, rating: int, user_id: int, item_id: int, created_at: Optional[str] = None):
    if created_at is None:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sql = """
    INSERT INTO review (title, thoughts, rating, user_id, item_id, created_at)
    VALUES (?, ?, ?, ?, ?, ?)
    """
    db.execute(sql, [title, thoughts, rating, user_id, item_id, created_at])

def update_review(review_id, title, thoughts, rating):
    sql = "UPDATE review SET title = ?, thoughts = ?, rating = ? WHERE id = ?"
    db.execute(sql, [title, thoughts, rating, review_id])

def delete_review(review_id):
    sql = "DELETE FROM review WHERE id = ?"
    db.execute(sql, [review_id])

def get_review_by_id(review_id: int):
    sql = """
    SELECT r.id,
           r.title,
           r.thoughts,
           r.rating,
           r.user_id,
           r.item_id,
           u.username,
           i.title AS item_title
    FROM review r
    JOIN users u ON r.user_id = u.id
    JOIN item i ON r.item_id = i.id
    WHERE r.id = ?
    """
    rows = db.query(sql, [review_id])
    return rows[0] if rows else None

def get_reviews_by_user_id(user_id: int):
    sql = """
    SELECT r.id, r.title, r.rating, r.created_at, i.title AS item_title, i.item_type
    FROM review r
    JOIN item i ON r.item_id = i.id
    WHERE r.user_id = ?
    ORDER BY r.created_at DESC
    """
    return db.query(sql, [user_id])

def get_user_top_item_by_type(user_id: int, item_type: str):
    sql = """
      SELECT i.title AS item_title,
             COALESCE(SUM(rv.value), 0) AS score
      FROM review r
      JOIN item i ON i.id = r.item_id
      LEFT JOIN review_votes rv ON rv.review_id = r.id
      WHERE r.user_id = ?
        AND i.item_type = ?
      GROUP BY i.id, i.title
      ORDER BY score DESC, i.title
      LIMIT 1
    """
    rows = db.query(sql, [user_id, item_type])
    return rows[0] if rows else None

def get_user_reviewed_items_by_type(user_id: int, item_type: str):
    sql = """
      SELECT DISTINCT i.title AS item_title
      FROM review r
      JOIN item i ON i.id = r.item_id
      WHERE r.user_id = ?
        AND i.item_type = ?
      ORDER BY i.title
    """
    return db.query(sql, [user_id, item_type])

# Review interactions

def get_review_vote(user_id: int, review_id: int):
    sql = "SELECT id, value FROM review_votes WHERE user_id = ? AND review_id = ?"
    rows = db.query(sql, [user_id, review_id])
    return rows[0] if rows else None

def insert_review_vote(user_id: int, review_id: int, value: int):
    sql = "INSERT INTO review_votes (user_id, review_id, value) VALUES (?, ?, ?)"
    db.execute(sql, [user_id, review_id, value])

def update_review_vote(user_id: int, review_id: int, value: int):
    sql = "UPDATE review_votes SET value = ? WHERE user_id = ? AND review_id = ?"
    db.execute(sql, [value, user_id, review_id])

def delete_review_vote(user_id: int, review_id: int):
    sql = "DELETE FROM review_votes WHERE user_id = ? AND review_id = ?"
    db.execute(sql, [user_id, review_id])

def is_favorited(user_id: int, review_id: int) -> bool:
    sql = "SELECT 1 FROM review_favorites WHERE user_id = ? AND review_id = ?"
    return bool(db.query(sql, [user_id, review_id]))

def favorite(user_id: int, review_id: int):
    sql = "INSERT INTO review_favorites (user_id, review_id) VALUES (?, ?)"
    db.execute(sql, [user_id, review_id])

def unfavorite(user_id: int, review_id: int):
    sql = "DELETE FROM review_favorites WHERE user_id = ? AND review_id = ?"
    db.execute(sql, [user_id, review_id])

def get_review_vote_counts(review_id: int):
    sql = """
      SELECT
        COALESCE(SUM(CASE WHEN value = 1 THEN 1 ELSE 0 END), 0) AS upvotes,
        COALESCE(SUM(CASE WHEN value = -1 THEN 1 ELSE 0 END), 0) AS downvotes,
        COALESCE(SUM(value), 0) AS score
      FROM review_votes WHERE review_id = ?
    """
    rows = db.query(sql, [review_id])
    return rows[0]

def get_review_favorite_count(review_id: int):
    sql = "SELECT COUNT(*) AS favorites FROM review_favorites WHERE review_id = ?"
    rows = db.query(sql, [review_id])
    return rows[0]

def get_user_votes_for_reviews(user_id: int, review_ids):
    if not review_ids:
        return {}
    placeholders = ",".join(["?"] * len(review_ids))
    sql = f"SELECT review_id, value FROM review_votes WHERE user_id = ? AND review_id IN ({placeholders})"
    rows = db.query(sql, [user_id, *review_ids])
    return {row["review_id"]: row["value"] for row in rows}

def get_user_favorites_for_reviews(user_id: int, review_ids):
    if not review_ids:
        return set()
    placeholders = ",".join(["?"] * len(review_ids))
    sql = f"SELECT review_id FROM review_favorites WHERE user_id = ? AND review_id IN ({placeholders})"
    rows = db.query(sql, [user_id, *review_ids])
    return {row["review_id"] for row in rows}

def get_user_vote_totals(user_id: int):
    sql = """
      SELECT
        COALESCE(SUM(CASE WHEN rv.value = 1 THEN 1 ELSE 0 END), 0) AS upvotes_received,
        COALESCE(SUM(CASE WHEN rv.value = -1 THEN 1 ELSE 0 END), 0) AS downvotes_received,
        COALESCE(SUM(rv.value), 0) AS score_received
      FROM review r
      LEFT JOIN review_votes rv ON rv.review_id = r.id
      WHERE r.user_id = ?
    """
    rows = db.query(sql, [user_id])
    return rows[0]

# Comments

def create_comment(review_id, user_id, comment_text):
    sql = "INSERT INTO comments (review_id, user_id, comment) VALUES (?, ?, ?)"
    db.execute(sql, [review_id, user_id, comment_text])

def get_comments_for_review(review_id):
    sql = """
      SELECT
        c.id AS id,
        c.comment,
        u.username,
        u.id AS user_id
      FROM comments c
      JOIN users u ON c.user_id = u.id
      WHERE c.review_id = ?
      ORDER BY c.created_at DESC
    """
    return db.query(sql, (review_id,))

def get_review_title(review_id):
    sql = "SELECT title FROM review WHERE id = ?"
    row = db.query(sql, (review_id,))
    if row:
        return row[0]['title']

def get_comment_by_id(comment_id: int):
    sql = """
      SELECT c.id, c.review_id, c.user_id, c.comment, c.created_at, u.username
      FROM comments c
      JOIN users u ON u.id = c.user_id
      WHERE c.id = ?
    """
    rows = db.query(sql, [comment_id])
    return rows[0] if rows else None

def update_comment(comment_id: int, new_text: str):
    sql = "UPDATE comments SET comment = ? WHERE id = ?"
    db.execute(sql, [new_text, comment_id])

def delete_comment_by_id(comment_id: int):
    sql = "DELETE FROM comments WHERE id = ?"
    db.execute(sql, [comment_id])

# Users

def create_user(username: str, password: str):
    username = username.strip()
    username_lower = username.lower()

    password_hash = generate_password_hash(password, method="pbkdf2:sha256")

    sql = """
        INSERT INTO users (username, username_lower, password_hash)
        VALUES (?, ?, ?)
    """

    db.execute(sql, [username, username_lower, password_hash])

def get_user_by_username(username: str):
    sql = "SELECT id, password_hash FROM users WHERE username = ?"
    rows = db.query(sql, [username])
    return rows[0] if rows else None

def check_login(username_lower: str, password: str):
    sql = """
        SELECT id, username, password_hash
        FROM users
        WHERE username_lower = ?
    """
    user = db.query(sql, [username_lower])

    if not user:
        return None

    user = user[0]

    if check_password_hash(user["password_hash"], password):
        return user

    return None

def get_user_by_id(user_id: int):
    sql = "SELECT id, username FROM users WHERE id = ?"
    rows = db.query(sql, [user_id])
    return rows[0] if rows else None

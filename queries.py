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
           COUNT(c.id) AS comment_count,
           r.created_at
    FROM review r
    JOIN item i ON r.item_id = i.id
    JOIN users u ON r.user_id = u.id
    LEFT JOIN comments c ON r.id = c.review_id
    GROUP BY r.id, r.title, i.item_type, u.username
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
            'comment_count': review['comment_count'],
            'created_at': review['created_at'],
            'comments': []
        }

        comment_sql = """
        SELECT c.comment, u.username
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.review_id = ?
        ORDER BY c.created_at DESC
        LIMIT 2
        """
        recent_comments = db.query(comment_sql, (review['id'],))
        review_dict['comments'] = recent_comments
        review_list.append(review_dict) 
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

# Comments

def create_comment(review_id, user_id, comment_text):
    sql = "INSERT INTO comments (review_id, user_id, comment) VALUES (?, ?, ?)"
    db.execute(sql, [review_id, user_id, comment_text])

def get_comments_for_review(review_id):
    sql = """
    SELECT c.comment, u.username
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


# Users

def create_user(username: str, password: str):
    password_hash = generate_password_hash(password, method="pbkdf2:sha256")
    sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
    db.execute(sql, [username, password_hash])

def get_user_by_username(username: str):
    sql = "SELECT id, password_hash FROM users WHERE username = ?"
    rows = db.query(sql, [username])
    return rows[0] if rows else None

def check_login(username: str, password: str):
    row = get_user_by_username(username)
    if not row:
        return None
    return row["id"] if check_password_hash(row["password_hash"], password) else None


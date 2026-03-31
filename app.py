import sqlite3
from flask import Flask
from flask import redirect, render_template, request, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import config
import db

app = Flask(__name__)
app.secret_key = config.secret_key

@app.route("/")
def index():
    result = db.query("""
        SELECT r.id, 
                r.title,
                u.username,
                COUNT(c.id) AS comment_count,
                COALESCE(MAX(c.created_at), 'No comments yet') AS last_comment,
                r.created_at
        FROM review r
        JOIN users u ON r.user_id = u.id
        LEFT JOIN comments c ON r.id = c.review_id
        GROUP BY r.id, r.title, u.username
        ORDER BY r.created_at DESC""")
    
    return render_template("index.html", review=result)

@app.route("/search")
def search():
    item_type = request.args.get("item_type")  
    query = (request.args.get("query") or "").strip()

    if not item_type:
        return render_template("search_results.html", results=[], item_type=item_type, query=query)

    sql = """
        SELECT
            i.id   AS item_id,
            i.title AS item_title,
            i.item_type,
            r.id   AS review_id,
            r.title AS review_title,
            r.rating
        FROM item i
        LEFT JOIN review r ON r.item_id = i.id
        WHERE i.item_type = ?
          AND (
            LOWER(TRIM(i.title)) LIKE LOWER(?)
            OR LOWER(COALESCE(TRIM(r.title), '')) LIKE LOWER(?)
          )
        ORDER BY i.title, r.id
    """
    params = [item_type, f"%{query}%", f"%{query}%"]
    results = db.query(sql, params)

    return render_template("search_results.html", results=results, item_type=item_type, query=query)


@app.route("/find_item")
def find_item():
    return render_template("find_item.html")

@app.route("/new_item")
def new_item():
    return render_template("new_item.html")

@app.route("/choose_category")
def choose_category():
    return render_template("choose_category.html")

@app.route("/create_item", methods=["POST"])
def create_item():
    title = request.form["title"]
    item_type = request.form["item_type"]

    sql = "INSERT INTO item (title, item_type) VALUES (?, ?)"
    db.execute(sql, [title, item_type])

    return redirect("/")

@app.route("/new_review/<category_name>")
def new_review(category_name):
    items = db.query("SELECT id, title FROM item WHERE item_type = ?", [category_name])
    return render_template("new_review.html", items=items, category_name=category_name)

@app.route("/create_review", methods=["POST"])
def create_review():
    title = request.form["title"]
    thoughts = request.form["thoughts"]
    rating = request.form["rating"]
    item_title = request.form["item_title"].strip()
    item_type = request.form["item_type"].strip().lower()
    user_id = session["user_id"]

    if item_type == "music":
        item_type = "song"
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    item = db.query(
        "SELECT id FROM item WHERE LOWER(title) = LOWER(?) AND item_type = ?",
        [item_title, item_type]
    )

    if item:
        item_id = item[0]["id"]
    else:
        db.execute(
            "INSERT INTO item (title, item_type) VALUES (?, ?)",
            [item_title, item_type]
        )
        item_id = db.query(
            "SELECT id FROM item WHERE LOWER(title) = LOWER(?) AND item_type = ?",
            [item_title, item_type]
        )[0]["id"]

    db.execute(
        """
        INSERT INTO review (title, thoughts, rating, user_id, item_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [title, thoughts, rating, user_id, item_id, created_at]
    )


    return redirect("/")

@app.route("/review/<int:review_id>")
def show_review(review_id):
    review = db.query("""
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
    """, [review_id])[0]

    return render_template("review.html", review=review)

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/create", methods=["POST"])
def create():
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]
    if password1 != password2:
        return "VIRHE: salasanat eivät ole samat"
    password_hash = generate_password_hash(password1, method="pbkdf2:sha256")

    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
    except sqlite3.IntegrityError:
        return "VIRHE: tunnus on jo varattu"

    return redirect("/")

@app.route("/login", methods=["GET", "POST"])

def login():
    if request.method == "GET":
        return render_template("login.html")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        sql = "SELECT id, password_hash FROM users WHERE username = ?"
        result = db.query(sql, [username])
        if len(result) == 0:
            return "VIRHE: väärä tunnus tai salasana"
        user = result[0]
        user_id = user["id"]
        password_hash = user["password_hash"]

        if check_password_hash(password_hash, password):
            session["user_id"] = user_id
            session["username"] = username
            return redirect("/")
        else:
            return "VIRHE: väärä tunnus tai salasana"

@app.route("/logout")
def logout():
    del session["username"]
    del session["user_id"]
    return redirect("/")
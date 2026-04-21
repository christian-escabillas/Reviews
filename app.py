import sqlite3
from flask import Flask
from flask import redirect, render_template, request, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import config
import db
import queries as q  

app = Flask(__name__)
app.secret_key = config.secret_key

@app.route("/")
def index():
    result = q.get_index_reviews()
    return render_template("index.html", review=result)

@app.route("/new_item")
def new_item():
    return render_template("new_item.html")

@app.route("/choose_category")
def choose_category():
    return render_template("choose_category.html")

# Item creation

@app.route("/create_item", methods=["POST"])
def create_item():
    title = request.form["title"].strip()
    item_type = request.form["item_type"].strip().lower()

    allowed_categories = ["movie", "game", "series", "song"]

    if not title:
        abort(404)

    if len(title) > 100:
        abort(404)

    if item_type not in allowed_categories:
        abort(404)

    q.create_item(title, item_type)
    return redirect("/")

@app.route("/new_review/<category_name>")
def new_review(category_name):
    allowed_categories = ["movie", "game", "series", "song"]

    if category_name not in allowed_categories:
        abort(404)

    items = q.get_items_by_type(category_name)
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

    allowed_categories = ["movie", "game", "series", "song"]

    if not title:
        abort(400)
    if len(title) > 100:
        abort(400)

    if not thoughts:
        abort(400)
    if len(thoughts) > 1000:
        abort(400)

    if not item_title:
        abort(400)
    if len(item_title) > 100:
        abort(400)

    if item_type not in allowed_categories:
        abort(400)

    if not rating.isdigit():
        abort(400)

    rating = int(rating)
    if rating < 1 or rating > 5:
        abort(400)
    
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    item_id = q.get_item_id_by_title_and_type(item_title, item_type)
    if item_id is None:
        q.create_item(item_title, item_type)
        item_id = q.get_item_id_by_title_and_type(item_title, item_type)

    q.create_review(title, thoughts, rating, user_id, item_id, created_at)
    return redirect("/")

# Searching for items

@app.route("/search")
def search():
    query = (request.args.get("q") or request.args.get("query") or "").strip()
    item_type = (request.args.get("item_type") or "all").strip()
    sort = (request.args.get("sort") or "relevance").strip()

    if item_type == "all":
        results = q.search_items_and_reviews_all(query)
    else:
        results = q.search_items_and_reviews(item_type, query)

    return render_template(
        "search_results.html",
        results=results,
        item_type=item_type,
        query=query,
        sort=sort,
    )

@app.route("/review/<int:review_id>")
def show_review(review_id):
    review = q.get_review_by_id(review_id)
    if not review:
        abort(404)

    comments = q.get_comments_for_review(review_id)
    return render_template("review.html", review=review)

# Editing and removing reviews

@app.route("/edit_review/<int:review_id>", methods=["GET", "POST"])
def edit_review(review_id):
    review = q.get_review_by_id(review_id)
    if not review:
        abort(404)

    if review['user_id'] != session.get("user_id"):
        abort(403)

    if request.method == "POST":
        title = request.form["title"]
        thoughts = request.form["thoughts"]
        rating = request.form["rating"]

        if not title or not thoughts or not rating.isdigit():
            abort(400)

        rating = int(rating)
        if rating < 1 or rating > 5:
            abort(400)

        q.update_review(review_id, title, thoughts, rating)
        return redirect(f"/review/{review_id}")

    return render_template("edit_review.html", review=review)

@app.route("/delete_review/<int:review_id>")
def delete_review(review_id):
    review = q.get_review_by_id(review_id)
    if not review:
        abort(404)

    if review['user_id'] != session.get("user_id"):
        abort(403)

    q.delete_review(review_id)
    return redirect("/")

# Comments

@app.route("/comment/<int:review_id>", methods=["POST"])
def comment(review_id):
    if "user_id" not in session:
        return redirect("/login") 

    comment_text = request.form.get("comment")
    user_id = session["user_id"]

    if not comment_text:
        abort(400)

    q.create_comment(review_id, user_id, comment_text)

    return redirect("/")

@app.route("/comments/<int:review_id>")
def show_comments(review_id):

    comments = q.get_comments_for_review(review_id)

    review_title = q.get_review_title(review_id)
    if review_title is None:
        abort(404)

    return render_template("show_comments.html", review_title=review_title, comments=comments)

# Profile page

@app.route("/profile/<int:user_id>")
def profile(user_id):
    user_info = q.get_user_by_id(user_id)

    if user_info is None:
        abort(404)

    user_reviews = q.get_reviews_by_user_id(user_id)

    comments = q.get_comments_for_review(user_reviews[0]['id']) if user_reviews else []
    print(comments)
    return render_template("profile.html", user=user_info, reviews=user_reviews)


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

    return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        user_id = q.check_login(username, password)
        if user_id is None:
            return render_template("login.html", error="VIRHE: väärä tunnus tai salasana")

        session["user_id"] = user_id
        session["username"] = username
        return redirect("/")

@app.route("/logout")
def logout():
    del session["username"]
    del session["user_id"]
    return redirect("/")

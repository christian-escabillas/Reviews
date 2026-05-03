import sqlite3
from flask import Flask
from flask import redirect, render_template, request, session, abort
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import config
import db
import queries as q  
import secrets
import markupsafe

app = Flask(__name__)
app.secret_key = config.secret_key

@app.template_filter()
def show_lines(content):
    content = str(markupsafe.escape(content))
    content = content.replace("\n", "<br />")
    return markupsafe.Markup(content)

def ensure_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)

@app.route("/")
def index():
    result = q.get_index_reviews()

    for r in result:
        vc = q.get_review_vote_counts(r["id"])
        fc = q.get_review_favorite_count(r["id"])
        r["upvotes"] = vc["upvotes"]
        r["downvotes"] = vc["downvotes"]
        r["score"] = vc["score"]
        r["favorites"] = fc["favorites"]

    uid = session.get("user_id")
    if uid:
        review_ids = [r["id"] for r in result]
        votes_map = q.get_user_votes_for_reviews(uid, review_ids)
        favs_set = q.get_user_favorites_for_reviews(uid, review_ids)
        for r in result:
            r["user_vote"] = votes_map.get(r["id"])
            r["favorited"] = (r["id"] in favs_set)
    else:
        for r in result:
            r["user_vote"] = None
            r["favorited"] = False

    return render_template("index.html", reviews=result)

@app.route("/new_item")
def new_item():
    return render_template("new_item.html")

@app.route("/choose_category")
def choose_category():
    return render_template("choose_category.html")

# Item creation

@app.route("/create_item", methods=["POST"])
def create_item():
    check_csrf()
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
    check_csrf()
    title = request.form["title"]
    thoughts = request.form["thoughts"]
    rating = request.form["rating"]
    item_title = request.form["item_title"].strip()
    item_type = request.form["item_type"].strip().lower()
    if "user_id" not in session:
        return redirect("/login")
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

# Review interactions

@app.route("/review/<int:review_id>/vote", methods=["POST"])
def vote_review(review_id):
    if "user_id" not in session:
        return redirect("/login")

    check_csrf()

    user_id = session["user_id"]
    value = request.form.get("value")
    if value not in ("1", "-1"):
        abort(400)
    value = int(value)

    existing = q.get_review_vote(user_id, review_id)
    if existing is None:
        q.insert_review_vote(user_id, review_id, value)
    else:
        if existing["value"] == value:

            q.delete_review_vote(user_id, review_id)
        else:
            q.update_review_vote(user_id, review_id, value)
    return redirect(request.referrer or "/")

@app.route("/review/<int:review_id>/favorite", methods=["POST"])
def favorite_review(review_id):
    if "user_id" not in session:
        return redirect("/login")

    check_csrf()

    user_id = session["user_id"]

    if q.is_favorited(user_id, review_id):
        q.unfavorite(user_id, review_id)
    else:
        q.favorite(user_id, review_id)
    return redirect(request.referrer or "/")

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

    results = [dict(r) for r in results]

    uid = session.get("user_id")
    review_ids = [row["review_id"] for row in results if row["review_id"] is not None]
    if uid and review_ids:
        votes_map = q.get_user_votes_for_reviews(uid, review_ids)
        favs_set = q.get_user_favorites_for_reviews(uid, review_ids)
        for row in results:
            rid = row["review_id"]
            if rid:
                row["user_vote"] = votes_map.get(rid)
                row["favorited"] = (rid in favs_set)
            else:
                row["user_vote"] = None
                row["favorited"] = False
    else:
        for row in results:
            row["user_vote"] = None
            row["favorited"] = False

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

    review = dict(review)

    comments = q.get_comments_for_review(review_id)

    vote_counts = q.get_review_vote_counts(review_id)
    fav_count = q.get_review_favorite_count(review_id)

    review["upvotes"] = vote_counts["upvotes"]
    review["downvotes"] = vote_counts["downvotes"]
    review["favorites"] = fav_count["favorites"]

    if "user_id" in session:
        user_id = session["user_id"]

        existing_vote = q.get_review_vote(user_id, review_id)
        if existing_vote:
            review["user_vote"] = existing_vote["value"]
        else:
            review["user_vote"] = None

        review["favorited"] = q.is_favorited(user_id, review_id)
    else:
        review["user_vote"] = None
        review["favorited"] = False

    return render_template("review.html", review=review, comments=comments)

# Editing and removing reviews

@app.route("/edit_review/<int:review_id>", methods=["GET", "POST"])
def edit_review(review_id):
    review = q.get_review_by_id(review_id)
    if not review:
        abort(404)

    if review['user_id'] != session.get("user_id"):
        abort(403)

    if request.method == "POST":
        check_csrf()
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

@app.route("/delete_review/<int:review_id>", methods=["POST"])
def delete_review(review_id):
    check_csrf()
    review = q.get_review_by_id(review_id)
    if not review:
        abort(404)

    if review['user_id'] != session.get("user_id"):
        abort(403)

    q.delete_review(review_id)
    return redirect("/")

@app.route("/review/<int:review_id>/confirm_delete")
def confirm_delete_review(review_id):
    review = q.get_review_by_id(review_id)

    if not review:
        abort(404)

    if review["user_id"] != session.get("user_id"):
        abort(403)

    return render_template("confirm_delete_review.html", review=review)

# Comments

@app.route("/comment/<int:review_id>", methods=["POST"])
def comment(review_id):
    check_csrf()

    if "user_id" not in session:
        return redirect("/login") 

    comment_text = request.form.get("comment")
    user_id = session["user_id"]

    if not comment_text:
        abort(400)

    q.create_comment(review_id, user_id, comment_text)

    return redirect(f"/review/{review_id}#comments")

@app.route("/comment/<int:comment_id>/edit", methods=["GET", "POST"])
def edit_comment(comment_id):
    comment = q.get_comment_by_id(comment_id)
    if not comment:
        abort(404)

    if comment["user_id"] != session.get("user_id"):
        abort(403)

    if request.method == "POST":
        check_csrf()
        new_text = (request.form.get("comment") or "").strip()
        if not new_text:
            abort(400)
        q.update_comment(comment_id, new_text)

        return redirect(f"/review/{comment['review_id']}")

    return render_template("edit_comment.html", comment=comment)

@app.route("/comment/<int:comment_id>/delete", methods=["POST"])
def delete_comment(comment_id):
    check_csrf()
    comment = q.get_comment_by_id(comment_id)

    if not comment:
        abort(404)

    if comment["user_id"] != session.get("user_id"):
        abort(403)

    q.delete_comment_by_id(comment_id)

    next_page = request.form.get("next")
    if next_page:
        return redirect(next_page)

    return redirect(f"/review/{comment['review_id']}")

@app.route("/comment/<int:comment_id>/confirm_delete")
def confirm_delete_comment(comment_id):
    comment = q.get_comment_by_id(comment_id)

    if not comment:
        abort(404)

    if comment["user_id"] != session.get("user_id"):
        abort(403)

    return render_template("confirm_delete_comment.html", comment=comment)

# Profile page

@app.route("/profile/<int:user_id>")
def profile(user_id):
    user_info = q.get_user_by_id(user_id)
    if user_info is None:
        abort(404)

    favorite_item_type = (request.args.get("favorite_item_type") or "movie").strip().lower()
    allowed = {"all", "movie", "series", "game", "song"}
    if favorite_item_type not in allowed:
        favorite_item_type = "all"

    user_reviews = q.get_reviews_by_user_id(user_id)
    vote_totals = q.get_user_vote_totals(user_id)

    favorite_reviews = q.get_user_favorited_reviews(user_id, None if favorite_item_type == "all" else favorite_item_type)

    return render_template(
        "profile.html",
        user=user_info,
        reviews=user_reviews,
        vote_totals=vote_totals,
        favorite_item_type=favorite_item_type,
        favorite_reviews=favorite_reviews,
        )

@app.route("/register")
def register():
    ensure_csrf_token()
    return render_template("register.html")

@app.route("/create", methods=["POST"])
def create():
    check_csrf()

    username = request.form["username"].strip()
    username_lower = username.lower()

    password1 = request.form["password1"]
    password2 = request.form["password2"]

    if not username or len(username) < 3:
        return "Username must be at least 3 characters long"

    if len(username) > 20:
        return "Username too long"

    if not username.isalnum():
        return "Username can only contain letters and numbers"

    if password1 != password2:
        return "ERROR: Passwords don not match"
    password_hash = generate_password_hash(password1, method="pbkdf2:sha256")

    try:
        sql = "INSERT INTO users (username, username_lower, password_hash) VALUES (?, ?, ?)"
        db.execute(sql, [username, username_lower, password_hash])
    except sqlite3.IntegrityError:
        return "ERROR: Username already in use"

    return render_template("login.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        ensure_csrf_token()
        return render_template("login.html")

    if request.method == "POST":
        check_csrf()
        username = request.form["username"]
        username_lower = username.lower()
        password = request.form["password"]
        
        user = q.check_login(username_lower, password)
        if user is None:
            return render_template("login.html", error="ERROR: invalid username or password")

        session["user_id"] = user["id"]
        session["username"] = user["username"]
        session["csrf_token"] = secrets.token_hex(16)
        return redirect("/")

def check_csrf():
    token_form = request.form.get("csrf_token")
    token_session = session.get("csrf_token")
    if not token_form or not token_session or token_form != token_session:
        abort(403)

@app.route("/logout")
def logout():
    del session["username"]
    del session["user_id"]
    return redirect("/")

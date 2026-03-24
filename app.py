import sqlite3
from flask import Flask
from flask import redirect, render_template, request, session
from werkzeug.security import generate_password_hash, check_password_hash
import config
import db

app = Flask(__name__)
app.secret_key = config.secret_key

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/new_item")
def new_item():
    return render_template("new_item.html")

@app.route("/create_item", methods=["POST"])
def create_item():
    title = request.form["title"]
    item_type = request.form["item_type"]

    sql = "INSERT INTO item (title, item_type) VALUES (?, ?)"
    db.execute(sql, [title, item_type])

    return redirect("/")

@app.route("/new_review")
def new_review():
    items = db.query("SELECT id, title FROM item")
    return render_template("new_review.html", items=items)

@app.route("/create_review", methods=["POST"])
def create_review():
    title = request.form["title"]
    thoughts = request.form["thoughts"]
    rating = request.form["rating"]
    item_id = request.form["item_id"]
    user_id = session["user_id"]

    sql = "INSERT INTO review (title, thoughts, rating, user_id, item_id) VALUES (?, ?, ?, ?, ?)"
    db.execute(sql, [title, thoughts, rating, user_id, item_id])
    
    return redirect("/")



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
    password_hash = generate_password_hash(password1)

    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
    except sqlite3.IntegrityError:
        return "VIRHE: tunnus on jo varattu"

    return "Tunnus luotui"

@app.route("/login", methods=["GET", "POST"])

def login():
    if request.method == "GET":
        return render_template("login.html")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        sql = "SELECT id, password_hash FROM users WHERE username = ?"
        result = db.query(sql, [username])[0]
        user_id = result["id"]
        password_hash =  result["password_hash"]

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
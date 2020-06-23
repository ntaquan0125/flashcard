import os

import matplotlib

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from random import choice
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, plot_stats

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///flashcard.db")


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """List all the current decks"""

    if request.method == "POST":
        # Ensure desk's name was submitted
        if not request.form.get("name"):
            return apology("missing deck's name")
        name = request.form.get("name")

        # Add new deck to database
        new_deck = db.execute("INSERT INTO decks (id, name, learned, total) VALUES (:id, :name, :learned, :total)",
                              id=session["user_id"], name=name, learned=0, total=0)

        # Check if deck already exists
        if not new_deck:
            return apology("this deck already exists")

        # Display a flash message
        flash("Creating deck successfully")

        # Reset the page
        return redirect("/")

    # Return all current decks
    decks = db.execute("SELECT name, learned, total FROM decks WHERE id = :id ORDER BY name", id=session["user_id"])

    return render_template("index.html", decks=decks)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/login")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # Form is submitted via POST
    if request.method == "POST":

        # Ensure username is not empty
        if not request.form.get("username"):
            return apology("must provide username")
        username = request.form.get("username")

        # Ensure password is not empty
        if not request.form.get("password"):
            return apology("missisng password")
        password = request.form.get("password")

        confirmation = request.form.get("confirmation")

        # Check for password confirmation
        if confirmation != password:
            return apology("passwords don't match")

        # Hash the user's password
        hashed_password = generate_password_hash(password)

        # Insert user into users
        new_user_id = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                                 username=username, hash=hashed_password)

        # Check if username already exists
        if not new_user_id:
            return apology("username already exists")

        session["user_id"] = new_user_id

        # Display a flash message
        flash("Registered!")

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/learn/<deck>", methods=["GET", "POST"])
@login_required
def learn(deck):
    """Learn a card"""

    if request.method == "POST":
        # Update card's status if it was learned
        front = request.form.get('card')
        db.execute("UPDATE cards SET learned = :learned WHERE id = :id AND front = :front",
                   learned=1, id=session["user_id"], front=front)
        db.execute("UPDATE decks SET learned = (SELECT COUNT(card_id) FROM cards WHERE id = :id AND deck = :name AND learned = :learned) WHERE id = :id AND name = :name",
                   id=session["user_id"], name=deck, learned=1)

    # Find all non-learned cards
    cards = db.execute("SELECT front, back FROM cards WHERE id = :id AND deck = :deck AND learned = :learned",
                       id=session["user_id"], deck=deck, learned=0)

    # Take out a card randomly
    card = choice(cards) if len(cards) > 0 else None

    return render_template("learn.html", deck=deck, card=card)


@app.route("/review/<deck>", methods=["GET", "POST"])
@login_required
def review(deck):
    """Review a card"""

    if request.method == "POST":
        # Update card's status if it was forgotten
        front = request.form.get('card')
        db.execute("UPDATE cards SET learned = :learned WHERE id = :id AND front = :front",
                   learned=0, id=session["user_id"], front=front)
        db.execute("UPDATE decks SET learned = (SELECT COUNT(card_id) FROM cards WHERE id = :id AND deck = :name AND learned = :learned) WHERE id = :id AND name = :name",
                   id=session["user_id"], name=deck, learned=1)

    # Find all learned cards
    cards = db.execute("SELECT front, back FROM cards WHERE id = :id AND deck = :deck AND learned = :learned",
                       id=session["user_id"], deck=deck, learned=1)

    # Take out a card randomly
    card = choice(cards) if len(cards) > 0 else None

    return render_template("review.html", deck=deck, card=card)


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """Find cards in decks"""

    if request.method == "POST":
        # Ensure search was submitted
        if not request.form.get("search"):
            return apology("missing values")
        search = request.form.get("search")

        # Choose to search in between decks and whole collections
        if not request.form.get("deck") or request.form.get("deck") == "all":
            cards = db.execute("SELECT * FROM cards WHERE id = :id AND (INSTR(LOWER(front), :search) OR INSTR(LOWER(back), :search))",
                               id=session["user_id"], search=search.lower())
        else:
            deck = request.form.get("deck")
            cards = db.execute("SELECT * FROM cards WHERE id = :id AND (INSTR(LOWER(front), :search) OR INSTR(LOWER(back), :search)) AND deck = :deck",
                               id=session["user_id"], search=search.lower(), deck=deck)

        return render_template("searched.html", cards=cards)

    else:
        decks = db.execute("SELECT name FROM decks WHERE id = :id ORDER BY name", id=session["user_id"])

        return render_template("search.html", decks=decks)


@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    """Add cards to decks"""

    if request.method == "POST":
        # Ensure card's information was submitted
        if not (request.form.get("front") and request.form.get("back")):
            return apology("missing card's information")
        deck = request.form.get("deck")
        front = request.form.get("front")
        back = request.form.get("back")

        # Insert card into database
        db.execute("INSERT INTO cards (id, front, back, deck, learned) VALUES (:id, :front, :back, :deck, :learned)",
                   id=session["user_id"], front=front, back=back, deck=deck, learned=0)

        # Update the total number of cards
        db.execute("UPDATE decks SET total = (SELECT COUNT(card_id) FROM cards WHERE id = :id AND deck = :name) WHERE id = :id AND name = :name",
                   id=session["user_id"], name=deck)

        # Display a flash message
        flash("Adding cards successfully")

        # Reset the page
        return redirect("/add")

    else:
        decks = db.execute("SELECT name FROM decks WHERE id = :id ORDER BY name", id=session["user_id"])

        return render_template("add.html", decks=decks)


@app.route("/statistics", methods=["GET", "POST"])
@login_required
def statistics():
    """Plot user's learning statistics"""

    # Choose which deck to plot learning stats
    if not request.form.get("deck") or request.form.get("deck") == "all":
        name = None
        status = db.execute('SELECT SUM(learned) AS "learned", SUM(total) AS "total" FROM decks WHERE id = :id', id=session["user_id"])
    else:
        name = request.form.get("deck")
        status = db.execute("SELECT learned, total FROM decks WHERE id = :id AND name = :name",
                            id=session["user_id"], name=name)

    # Run matplotlib backend
    matplotlib.use("Agg")

    # Prepare data
    x = [status[0]["learned"], status[0]["total"] - status[0]["learned"]]
    labels = "Learned", "Not"

    plot_stats(x, labels)

    decks = db.execute("SELECT name FROM decks WHERE id = :id ORDER BY name", id=session["user_id"])

    return render_template("statistics.html", decks=decks, name=name, url="../static/images/plot.png")


def errorhandler(e):
    """Handle error"""

    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

# Copyright (C) 2020 Jaymin Patel. All Rights Reserved.

import os,requests

from flask import Flask, session, request, abort
from flask import render_template, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests

app = Flask(__name__)


# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine("postgres://flqifujrhvgfqx:60d1e37710fcda3dfc4e3afaac7309817f48992e120b808692d711bf1b6150e2@ec2-18-233-32-61.compute-1.amazonaws.com:5432/d3mb3eorevq7e9")
db = scoped_session(sessionmaker(bind=engine))

# Setup the key for GOODREADS API
KEY = os.getenv("GOODREADS_KEY")

# The home page
@app.route("/")
def index():
    return render_template("index.html")


# Account creation page.
# Also checks if a username already exists.
@app.route("/account-creation", methods = ["GET", "POST"])
def new_account():

    if request.method == "GET":
        return render_template("account_error.html", message="LOGIN AGAIN")

    username = request.form.get("username")
    password = request.form.get("password")

    if username is '':
        return render_template("account_error.html", message = "USERNAME OR PASSWORD IS EMPTY")

    if password is '':
        return render_template("account_error.html", message = "USERNAME OR PASSWORD IS EMPTY")

    if username == "guest":
        return render_template("account_error.html", message = "\"guest\" is not available as an username")

    if db.execute('SELECT * FROM users WHERE username = :username', {'username':username}).rowcount == 0:
        db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", 
        {"username": username, "password": password})
        db.commit()
        return render_template("account_creation_success.html")
    else:
        return render_template("account_error.html", message = "USERNAME ALREADY EXISTS")


# The books search page.
# Also checks for login information.
@app.route("/search", methods = ["GET", "POST"])
def search_books():

    if request.method == "GET":
        return render_template("account_error.html", message="LOGIN AGAIN")

    username = request.form.get("username")
    password = request.form.get("password")

    if username is '':
        return render_template("account_error.html", message = "CHECK USERNAME AND PASSWORD")

    if password is '':
        return render_template("account_error.html", message = "CHECK USERNAME AND PASSWORD")

    try:
        password_from_database = db.execute("SELECT password FROM users WHERE username = :username",
        {"username":username}).fetchone()

        password_from_database = password_from_database.password

    except:
        password_from_database = None


    if (password_from_database == password):
        session["username"] = username

    else:
        return render_template("account_error.html", message = "PASSWORD NOT CORRECT")

    try:
        username = session["username"]
    except:
        return render_template("account_error.html", message="LOGIN AGAIN")

    books = db.execute("SELECT * FROM books ORDER BY title").fetchall()
    return render_template("search.html", username = session["username"], books = books)


# Returns the list of books that match the given input for search.
@app.route("/searched-books", methods = ["GET", "POST"])
def search_result():

    try:
        username = session["username"]
    except:
        return render_template("account_error.html", message="LOGIN AGAIN")

    search_type = request.form.get("search_type")
    search_value = request.form.get("search_value")

    search_value = str(search_value)

    if search_type == "isbn":
        booklist = db.execute("SELECT * FROM books WHERE isbn LIKE :search_value",
        {"search_value": "%" + search_value + "%"}).fetchall()

    if search_type == "title":
        booklist = db.execute("SELECT * FROM books WHERE title LIKE :search_value",
        {"search_value": "%" + search_value + "%"}).fetchall()

    if search_type == "author":
        booklist = db.execute("SELECT * FROM books WHERE author LIKE :search_value",
        {"search_value": "%" + search_value + "%"}).fetchall()

    if search_type == "year":
        booklist = db.execute("SELECT * FROM books WHERE year = :search_value",
        {"search_value":search_value}).fetchall()

    return render_template("search-result.html", username = session["username"], books = booklist)


# Shows the selected book's information.
@app.route("/book/<string:isbn>")
def book(isbn):

    try:
        username = session["username"]
    except:
        return render_template("account_error.html", message="LOGIN AGAIN")


    book_info = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn":isbn}).fetchone()

    goodreads = "GOODSREADS API"
    status = True
    other_review_num = True

    connection_established = True

    guest = False

    if db.execute("SELECT * FROM reviews WHERE username = :username AND isbn = :isbn",
        {"username":username, "isbn":isbn}).rowcount == 0:
        status = False

    if db.execute("SELECT * FROM reviews WHERE isbn = :isbn",
        {"isbn":isbn}).rowcount == 0:
        other_review_num = False

    others_review = db.execute("SELECT username, review, rating FROM reviews WHERE isbn = :isbn",
    {"isbn":isbn}).fetchall()

    try:
        res = requests.get("https://www.goodreads.com/book/review_counts.json",
        params={"key": KEY, "isbns": isbn}).json()["books"][0]
    except:
        connection_established = False

    if connection_established:
        goodreads_ratings_count = res["ratings_count"]
        goodreads_average_rating = res["average_rating"]
    else:
        goodreads_ratings_count = 0
        goodreads_average_rating = 0

    if session["username"] == "guest":
        status = True
        guest = True

    return render_template("book.html", username = session["username"], message = book_info, 
    goodreads_ratings_count = goodreads_ratings_count, status = status, reviews = others_review, 
    other_review_num = other_review_num, goodreads_average_rating = goodreads_average_rating,
    guest = guest)


# Registers a review of a book submitted by a user.
# Also checks if review already exists for the book by a user.
@app.route("/review", methods = ["GET", "POST"])
def review():

    try:
        username = session["username"]
    except:
        return render_template("account_error.html", message="LOGIN AGAIN")

    isbn_review = request.form.get('book_isbn_review')
    review = request.form.get("review-data")
    review_status = False
    rating = request.form.get("rating")

    if session["username"] == "guest":
        error = "Guests cannot submit a review."
        return render_template("review_submitted.html", book_id = isbn_review, review_status=review_status
        , message = error)

    if db.execute("SELECT * FROM reviews WHERE username = :username AND isbn = :isbn",
        {"username":username, "isbn":isbn_review}).rowcount != 0:
        error = "Review already submitted. Review cannot be submitted again."
        return render_template("review_submitted.html", book_id = isbn_review, review_status=review_status
        , message = error)

    if len(review) == 0:
        error = "Review is empty."
        return render_template("review_submitted.html", book_id = isbn_review, review_status=review_status
        , message = error)

    if rating not in ("1","2","3","4","5"):
        error = "Rating not in range."
        return render_template("review_submitted.html", book_id = isbn_review, review_status=review_status
        , message = error)

    db.execute("INSERT INTO reviews (username, isbn, review, rating) VALUES (:username, :isbn, :review, :rating)", 
    {"username":username, "isbn":isbn_review, "review":review, "rating":rating})
    db.commit()

    review_status = True
    return render_template("review_submitted.html", book_id = isbn_review, review_status=review_status)


# Logs out the user.
@app.route("/logout", methods = ["POST"])
def logout():
    session.pop("username")
    return render_template("logout.html")


# API access to database for a book's information.
@app.route("/api/<string:isbn>", methods = ["GET"])
def api(isbn):
    count = 0
    score = 0
    ratings_total = 0

    book_info = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn":isbn}).fetchone()

    if book_info is None:
        abort(404)

    count = db.execute("SELECT * FROM reviews WHERE isbn = :isbn", {"isbn":isbn}).rowcount
    reviews = db.execute("SELECT rating FROM reviews WHERE isbn = :isbn", {"isbn":isbn}).fetchall()

    if count == 0:
        score = 0
    else:
        for review in reviews:
            ratings_total += review.rating
        score = ratings_total/count

    return jsonify({
        "title":book_info.title,
        "author":book_info.author,
        "year":book_info.year,
        "isbn":book_info.isbn,
        "review_count":count,
        "average_score":score
    })

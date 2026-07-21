"""
Reputal — AI review-response app for restaurants.

Run locally:
    pip install -r requirements.txt
    python app.py
Then open http://localhost:5000
"""
import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

import models
from integrations import claude_api, zernio

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-change-this-in-production")

models.init_db()


def current_restaurant():
    rid = session.get("restaurant_id")
    if not rid:
        return None
    return models.get_restaurant_by_id(rid)


def login_required(view):
    def wrapped(*args, **kwargs):
        if not current_restaurant():
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    wrapped.__name__ = view.__name__
    return wrapped


# ---------- Auth ----------

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"].strip()
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        if models.get_restaurant_by_email(email):
            flash("An account with that email already exists.")
            return redirect(url_for("signup"))

        password_hash = generate_password_hash(password)
        restaurant_id = models.create_restaurant(name, email, password_hash)
        session["restaurant_id"] = restaurant_id
        return redirect(url_for("dashboard"))

    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        restaurant = models.get_restaurant_by_email(email)

        if restaurant and check_password_hash(restaurant["password_hash"], password):
            session["restaurant_id"] = restaurant["id"]
            return redirect(url_for("dashboard"))

        flash("Incorrect email or password.")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- Dashboard ----------

@app.route("/")
@login_required
def dashboard():
    restaurant = current_restaurant()
    reviews = models.get_reviews_for_restaurant(restaurant["id"])
    return render_template("dashboard.html", restaurant=restaurant, reviews=reviews)


@app.route("/connect-google")
@login_required
def connect_google():
    redirect_uri = url_for("zernio_callback", _external=True)
    connect_url = zernio.get_connect_url(redirect_uri)
    return redirect(connect_url)


@app.route("/zernio-callback")
@login_required
def zernio_callback():
    zernio_account_id = request.args.get("accountId")
    restaurant = current_restaurant()

    if zernio_account_id:
        models.set_zernio_account(restaurant["id"], zernio_account_id)
        flash("Google Business Profile connected.")
    else:
        flash("Something went wrong connecting your account. Please try again.")

    return redirect(url_for("dashboard"))


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    restaurant = current_restaurant()
    if request.method == "POST":
        tone = request.form["tone"].strip()
        auto_post = "auto_post" in request.form
        models.update_restaurant_settings(restaurant["id"], tone, auto_post)
        flash("Settings saved.")
        return redirect(url_for("settings"))

    return render_template("settings.html", restaurant=restaurant)


@app.route("/reviews/<int:review_id>/approve", methods=["POST"])
@login_required
def approve_reply(review_id):
    restaurant = current_restaurant()
    review = models.get_review_by_id(review_id)

    if not review or review["restaurant_id"] != restaurant["id"]:
        flash("Review not found.")
        return redirect(url_for("dashboard"))

    zernio.post_reply(
        restaurant["zernio_account_id"],
        review["external_review_id"],
        review["drafted_reply"],
    )
    models.mark_posted(review_id

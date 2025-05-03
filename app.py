from flask import Flask, flash, render_template, redirect, url_for, request, session
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from bson.json_util import dumps
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "supersecret")
app.permanent_session_lifetime = timedelta(hours=12)

# --- MongoDB setup ---
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["darkhorse_data"]
users_col = db["users"]
config_col = db["config"]
live_col = db["live_entries"]

# --- Ensure default admin user exists ---
def create_default_admin():
    admin_password = os.getenv("ADMIN_PASSWORD", "admin")
    existing_admin = users_col.find_one({"username": "admin"})
    if not existing_admin:
        users_col.insert_one({
            "username": "admin",
            "password_hash": generate_password_hash(admin_password)
        })
    else:
        # Optional: Reset password if ADMIN_PASSWORD changes
        new_hash = generate_password_hash(admin_password)
        users_col.update_one(
            {"username": "admin"},
            {"$set": {"password_hash": new_hash}}
        )

create_default_admin()

# --- Routes ---
@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = users_col.find_one({"username": username})
        if user and check_password_hash(user["password_hash"], password):
            session["user"] = username
            session.permanent = True
            return redirect(url_for("dashboard"))
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    config = config_col.find_one() or {"min_profit_dollars": 12.0, "min_percent": 2.0}

    if request.method == "POST":
        min_dollars = float(request.form.get("min_profit_dollars", 12.0))
        min_percent = float(request.form.get("min_percent", 2.0))
        config_col.delete_many({})
        config_col.insert_one({
            "_id": "thresholds",
            "min_profit_dollars": min_dollars,
            "min_percent": min_percent
        })
        config = {"min_profit_dollars": min_dollars, "min_percent": min_percent}
        print(f"🔧 Updated filter thresholds: ${min_dollars} / {min_percent}%")
        flash("✅ Filters updated successfully!", "success")


    sort_by = request.args.get("sort", "time_posted")
    direction = request.args.get("dir", "desc")
    direction_value = -1 if direction == "desc" else 1

    valid_fields = {"time_posted", "profit_dollars", "profit_percent"}
    if sort_by not in valid_fields:
        sort_by = "time_posted"

    entries = list(live_col.find().sort(sort_by, direction_value))
    return render_template("dashboard.html", entries=entries, config=config, sort_by=sort_by, direction=direction)


@app.route("/api/entries")
def api_entries():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    entries = list(live_col.find().sort("time_posted", -1))
    return dumps(entries)

if __name__ == "__main__":
    app.run(debug=True)

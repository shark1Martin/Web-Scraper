from flask import Flask, flash, render_template, redirect, url_for, request, session
from werkzeug.security import generate_password_hash
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta
from bson.json_util import dumps
from dotenv import load_dotenv
from functools import wraps
from bson import ObjectId
from flask import abort
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os

load_dotenv()

app = Flask(__name__, template_folder="templates")
app.secret_key = os.getenv("FLASK_SECRET", "supersecret")
app.permanent_session_lifetime = timedelta(hours=12)

# --- MongoDB setup ---
MONGO_URI = os.getenv("MONGO_URI")
client = MongoClient(MONGO_URI)
db = client["darkhorse_data"]
users_col = db["users"]
config_col = db["config"]
live_col = db["live_entries"]
entries_col = db["entries_V4"]

# --- Ensure default admin user exists ---
def create_default_admin():
    admin_password = os.getenv("ADMIN_PASSWORD", "admin")
    existing_admin = users_col.find_one({"username": "admin"})
    if not existing_admin:
        users_col.insert_one({
            "username": "admin",
            "password_hash": generate_password_hash(admin_password),
            "role": "admin"
        })
    else:
        # Optional: Reset password if ADMIN_PASSWORD changes
        new_hash = generate_password_hash(admin_password)
        users_col.update_one(
            {"username": "admin"},
            {"$set": {"password_hash": new_hash, "role": "admin"}}
        )

create_default_admin()

# CHECKS FOR ROLE ACCESS

def requires_any_role(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if "user" not in session or session.get("role") not in roles:
                return abort(403)
            return f(*args, **kwargs)
        return decorated
    return wrapper


# --- Routes ---
@app.route("/")
def home():
    if "user" in session:
        role = session.get("role", "user")
        if role in ["admin", "head_admin"]:
            return redirect(url_for("dashboard"))
        else:
            return redirect(url_for("viewer_dashboard"))
    return redirect(url_for("login"))


# LOG-IN-PAGE

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        user = users_col.find_one({"username": username})
        if user and check_password_hash(user["password_hash"], password):
            session["user"] = username
            session["role"] = user.get("role", "user")
            session.permanent = True

            if session["role"] in ["admin", "head_admin"]:
                return redirect(url_for("dashboard"))
            else:
                return redirect(url_for("viewer_dashboard"))

        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

#LOGOUT-PAGE

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# SIGNUP-PAGE

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]
        confirm = request.form["confirm_password"]
        keycode = request.form["keycode"].strip()

        if password != confirm:
            return render_template("signup.html", error="Passwords do not match")

        if users_col.find_one({"username": username}):
            return render_template("signup.html", error="Username already taken")

        role = None
        if keycode == os.getenv("ADMIN_KEYCODE"):
            role = "admin"
        elif keycode == os.getenv("USER_KEYCODE"):
            role = "user"
        else:
            return render_template("signup.html", error="Invalid key code")

        users_col.insert_one({
            "username": username,
            "password_hash": generate_password_hash(password),
            "role": role
        })

        session["user"] = username
        session["role"] = role
        session.permanent = True

        if role == "admin":
            return redirect(url_for("dashboard"))
        else:
            return redirect(url_for("viewer_dashboard"))

    return render_template("signup.html")

# ADMIN-DASHBOARD

from zoneinfo import ZoneInfo
from datetime import datetime, timedelta

@app.route("/dashboard", methods=["GET", "POST"])
@requires_any_role("admin", "head_admin")
def dashboard():
    # --- Use Eastern Time ---
    now = datetime.now(ZoneInfo("America/Toronto"))
    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_yesterday = start_today - timedelta(days=1)

    # --- Count entries in EST ---
    count_today = entries_col.count_documents({
        "time_posted": {"$gte": start_today}
    })

    count_yesterday = entries_col.count_documents({
        "time_posted": {"$gte": start_yesterday, "$lt": start_today}
    })

    past_week_counts = []
    past_week_labels = []
    # Past 7 full days (yesterday to 6 days ago)
    for i in range(7):
        est_day_start = start_today - timedelta(days=i)
        est_day_end = est_day_start + timedelta(days=1)
        utc_day_start = est_day_start.astimezone(ZoneInfo("UTC"))
        utc_day_end = est_day_end.astimezone(ZoneInfo("UTC"))

        count = entries_col.count_documents({
            "time_posted": {"$gte": utc_day_start, "$lt": utc_day_end}
        })

        past_week_counts.insert(0, count)
        past_week_labels.insert(0, est_day_start.strftime("%a"))



    # --- Config thresholds ---
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
        flash("✅ Filters updated successfully!", "success")

    sort_by = request.args.get("sort", "time_posted")
    direction = request.args.get("dir", "desc")
    direction_value = -1 if direction == "desc" else 1
    valid_fields = {"time_posted", "profit_dollars", "profit_percent"}
    if sort_by not in valid_fields:
        sort_by = "time_posted"

    entries = list(live_col.find().sort(sort_by, direction_value))

    return render_template("dashboard.html",
                           entries=entries,
                           config=config,
                           sort_by=sort_by,
                           direction=direction,
                           count_today=count_today,
                           count_yesterday=count_yesterday,
                           past_week_counts=past_week_counts,
                           past_week_labels=past_week_labels)


# VIEWER-DASHBOARD

@app.route("/viewer_dashboard")
def viewer_dashboard():
    if "user" not in session or session.get("role") not in ["user", "admin", "head_admin"]:
        return redirect(url_for("login"))

    now = datetime.now(ZoneInfo("America/Toronto"))
    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
    start_yesterday = start_today - timedelta(days=1)

    count_today = entries_col.count_documents({"time_posted": {"$gte": start_today}})
    count_yesterday = entries_col.count_documents({"time_posted": {"$gte": start_yesterday, "$lt": start_today}})

    past_week_counts = []
    for i in range(6, -1, -1):
        day_start = start_today - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        count = entries_col.count_documents({"time_posted": {"$gte": day_start, "$lt": day_end}})
        past_week_counts.append(count)

    entries = list(live_col.find().sort("profit_dollars", -1))

    return render_template("viewer_dashboard.html",
                           entries=entries,
                           count_today=count_today,
                           count_yesterday=count_yesterday,
                           past_week_counts=past_week_counts)


# INSIGHTS & USERS 

@app.route("/insights")
@requires_any_role("admin", "head_admin")
def insights():
    entries = list(live_col.find().sort("profit_dollars", -1))
    config = config_col.find_one() or {"min_profit_dollars": 12.0, "min_percent": 2.0}
    return render_template("insights.html", entries=entries, config=config)

@app.route("/users")
@requires_any_role("admin", "head_admin")
def view_users():
    users = list(users_col.find().sort([("role", 1), ("username", 1)]))
    return render_template("users.html", users=users)

# EDIT USERS

@app.route("/edit_user/<user_id>", methods=["POST"])
@requires_any_role("admin", "head_admin")
def edit_user(user_id):
    target_user = users_col.find_one({"_id": ObjectId(user_id)})
    if not target_user:
        flash("User not found.", "danger")
        return redirect(url_for("view_users"))

    current_role = session.get("role")
    target_role = target_user.get("role")

    # Regular admins can only edit users
    if current_role == "admin" and target_role != "user":
        flash("Permission denied: Cannot modify another admin.", "danger")
        return redirect(url_for("view_users"))

    new_username = request.form["username"].strip()
    new_password = request.form.get("password")

    update_data = {"username": new_username}
    if new_password:
        update_data["password_hash"] = generate_password_hash(new_password)

    users_col.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    flash(f"✅ Updated '{new_username}'", "success")
    return redirect(url_for("view_users"))

# DELETE USERS

@app.route("/delete_user/<user_id>", methods=["POST"])
@requires_any_role("admin", "head_admin")
def delete_user(user_id):
    target_user = users_col.find_one({"_id": ObjectId(user_id)})
    if not target_user:
        flash("User not found.", "danger")
        return redirect(url_for("view_users"))

    current_role = session.get("role")
    target_role = target_user.get("role")

    # Regular admins can't delete other admins
    if current_role == "admin" and target_role != "user":
        flash("Permission denied: Cannot delete another admin.", "danger")
        return redirect(url_for("view_users"))

    users_col.delete_one({"_id": ObjectId(user_id)})
    flash(f"🗑️ Deleted '{target_user.get('username')}'", "success")
    return redirect(url_for("view_users"))

# CHECKS IF USER IS ACTIVE, OTHERWISE DOESN'T DISPLAY ENTRIES

@app.route("/api/entries")
def api_entries():
    if "user" not in session:
        return {"error": "Unauthorized"}, 401
    entries = list(live_col.find().sort("time_posted", -1))
    return dumps(entries)

if __name__ == "__main__":
    app.run(debug=True)

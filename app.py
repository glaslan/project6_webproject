""" This module is the main entry point for the Flask app """
import os
from datetime import timedelta
from uuid import uuid4

from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_from_directory,
)
from flask_jwt_extended import JWTManager
from flask_jwt_extended.utils import decode_token
from werkzeug.security import generate_password_hash, check_password_hash

from constants import (
    DATABASE_PATH,
    USER_ID,
    USERNAME,
    PASSWORD,
    POST_ID,
    IMAGE_EXT,
    CONTENT,
    DATE,
    GET,
    PUT,
    POST,
    PATCH,
    DELETE,
    OPTIONS,
)
from database_access_layer import Database
from auth_controller import AuthController
from post_controller import PostController

APP_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(APP_DIR, "images")

app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY", "default_secret_key")
app.config["JWT_SECRET_KEY"] = os.environ.get(
    "JWT_SECRET_KEY", "default_jwt_secret_key"
)
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=12)

os.makedirs(os.path.join(APP_DIR, "images"), exist_ok=True)

jwt = JWTManager(app)

# Controllers
db = Database(DATABASE_PATH)


def _unwrap(v):
    return v[0] if isinstance(v, tuple) and len(v) == 1 else v


def _unwrap_sql_value(v):
    """
    Unwraps a SQL value that may be wrapped in a tuple
    Args:
    v: The value to unwrap
    Returns:
    The unwrapped value
    """
    if isinstance(v, tuple) and len(v) == 1:
        return v[0]
    return v


def _normalise_user(user: dict | None) -> dict | None:
    """
    Normalises a user dictionary by unwrapping any SQL values
    Args:
    user: The user dictionary to normalise
    Returns:
    The normalised user dictionary
    """
    if not user:
        return None
    if USER_ID in user:
        user[USER_ID] = _unwrap_sql_value(user[USER_ID])
    if PASSWORD in user:
        user[PASSWORD] = _unwrap_sql_value(user[PASSWORD])
    if USERNAME in user:
        user[USERNAME] = _unwrap_sql_value(user[USERNAME])
    return user


def _normalise_post(post: dict | None) -> dict | None:
    """Normalises a post dictionary by unwrapping any SQL values
    Args:    post: The post dictionary to normalise
    Returns:    The normalised post dictionary
    """
    for k in (POST_ID, USER_ID, IMAGE_EXT, CONTENT, DATE):
        if k in post:
            post[k] = _unwrap_sql_value(post[k])
    return post


def get_current_user_id() -> int | None:
    """
    Gets the current user ID from the session token
    Returns:    The current user ID, or None if the token is invalid or not present
    """
    token = session.get("access_token")
    if not token:
        return None
    try:
        decoded_token = decode_token(token)
        return decoded_token.get("sub")
    except Exception as e:
        print(f"Error decoding token: {e}")
        return None


def get_current_user() -> dict | None:
    """
    Gets the current user from the database using the user ID from the session token
    Returns:    The current user dictionary, or None if the user is not found or the token is invalid
    """
    uid = get_current_user_id()
    if uid is None:
        return None
    u = db.get_user_by_id(uid)
    u = _normalise_user(u)
    return u


@app.route("/", methods=[GET, POST])
def home():
    """
    Docstring for home
    Default route for the home page, also handles post creation
    Returns:   template: The home page html template, with the list of posts and the current user (if logged in)
    """

    posts = PostController(DATABASE_PATH)

    user = get_current_user()

    if request.method == POST:
        if not user:
            flash("You must be logged in to create a post", "error")
            return redirect(url_for("login"))

        content = (request.form.get(CONTENT) or "").strip()
        if not content:
            flash("Post content cannot be empty", "error")
            return redirect(url_for("home"))

        post_id = uuid4().int & 0x7FFFFFFFFFFFFFFF  # Generate a random post ID

        image_ext = None
        file = request.files.get("image")
        if file and file.filename:
            if "." in file.filename:
                image_ext = file.filename.rsplit(".", 1)[1].lower()
                safe_name = f"{post_id}.{image_ext}"
                file.save(os.path.join(UPLOAD_DIR, safe_name))
            else:
                flash("Invalid image file", "error")
                image_ext = None
                return redirect(url_for("home"))
        post_obj = {
            POST_ID: int(post_id),
            USER_ID: str(user[USER_ID]),
            CONTENT: content,
            IMAGE_EXT: image_ext,
        }

        ok = posts.create_post(post_obj)
        if ok:
            flash("Post created successfully", "success")
        else:
            flash("Failed to create post", "error")
        return redirect(url_for("home"))

    all_posts = posts.get_posts()
    all_posts = [_normalise_post(p) for p in all_posts]

    for p in all_posts:
        try:
            author = db.get_user_by_id(_unwrap_sql_value(p.get(USER_ID)))
            author = _normalise_user(author)
            p["author_username"] = author[USERNAME] if author else "Unknown"
        except Exception:
            p["author_username"] = None

    return render_template("html/home.html", user=get_current_user(), posts=all_posts)


@app.route("/register", methods=[GET, POST, OPTIONS])
def register():
    """
    Docstring for register
    Default route for the registration page, also handles registration form submission
    Returns:
    template: The registration page html template, with the current user (if logged in)
    """

    auth = AuthController(DATABASE_PATH)

    if request.method == OPTIONS:
        resp = app.make_response(("", 204))
        resp.headers["Allow"] = "GET, POST, OPTIONS"
        return resp

    if request.method == POST:
        username = (request.form.get(USERNAME) or "").strip()
        password = request.form.get(PASSWORD) or ""

        potential_new_user = {USERNAME: username, PASSWORD: password}
        created = auth.register(potential_new_user)
        if not created:
            flash(
                "Registration failed. Username may be taken or invalid input.", "error"
            )
            return redirect(url_for("register"))

        token = auth.login(potential_new_user)
        if token:
            session["access_token"] = token

        flash("Account created successfully.", "success")
        return redirect(url_for("home"))

    return render_template("html/register.html")


@app.route("/login", methods=[GET, POST, OPTIONS])
def login():
    """
    Default route for the login page, also handles login form submission
    Returns:
    template: The login page html template, with the current user (if logged in)
    """

    auth = AuthController(DATABASE_PATH)

    if request.method == OPTIONS:
        resp = app.make_response(("", 204))
        resp.headers["Allow"] = "GET, POST, OPTIONS"
        return resp

    user = get_current_user()
    if user:
        flash("You are already logged in", "info")
        return redirect(url_for("home"))

    if request.method == POST:
        username = (request.form.get(USERNAME) or "").strip()
        password = request.form.get(PASSWORD) or ""

        token = auth.login({USERNAME: username, PASSWORD: password})
        if token:
            session["access_token"] = token
            flash("Login successful", "success")
            return redirect(url_for("home"))
        else:
            flash("Invalid username or password", "error")

    return render_template("html/login.html")


@app.route("/profile", methods=[GET, POST, PUT, PATCH, DELETE, OPTIONS])
def profile():
    """
    Default route for the profile page, shows the current user's profile information and their posts
    Returns:
    template: The profile page html template, with the current user (if logged in) and their posts
    """

    auth = AuthController(DATABASE_PATH)
    posts = PostController(DATABASE_PATH)

    if request.method == OPTIONS:
        resp = app.make_response(("", 204))
        resp.headers["Allow"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        return resp

    user = get_current_user()
    user = _normalise_user(user)

    if not user:
        if request.method == GET:
            flash("Please log in first.", "error")
            return redirect(url_for("login"))
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    if request.method == GET:
        all_posts = db.get_all_posts()
        my_posts = [p for p in all_posts if str(p.get(USER_ID)) == str(user[USER_ID])]

        return render_template("html/profile.html", user=user, posts=my_posts)

    if request.method == POST:
        action = request.form.get("action")

        if action == "logout":
            session.pop("access_token", None)
            flash("Logged out.", "success")

            return redirect(url_for("home"))

        if action == "delete_post":
            date = request.form.get(DATE)
            if not date:
                flash("Missing post date.", "error")
                return redirect(url_for("profile"))

            ok = db.delete_post(str(user[USER_ID]), date)
            if ok:
                db.connection.commit()
            flash(
                "Post deleted." if ok else "Failed to delete post.",
                "success" if ok else "error",
            )
            return redirect(url_for("profile"))

        flash("Unknown action.", "error")
        return redirect(url_for("profile"))

    data = request.get_json(silent=True) or {}

    if request.method == PATCH:
        req_type = (data.get("type") or "user").lower()

        if req_type == "user":
            new_username = data.get(USERNAME)
            new_password = data.get(PASSWORD)

            if not new_username and not new_password:
                return (
                    jsonify(
                        {
                            "ok": False,
                            "error": "PATCH user requires username and/or password",
                        }
                    ),
                    400,
                )

            edited = {
                USER_ID: int(user[USER_ID]),
                USERNAME: new_username if new_username else user[USERNAME],
                PASSWORD: generate_password_hash(new_password)
                if new_password
                else _unwrap(user[PASSWORD]),
            }

            ok = db.update_user(user, edited)
            if ok:
                db.connection.commit()
            return jsonify({"ok": ok, "updated": "user"}), (200 if ok else 400)

        if req_type == POST:
            post_id = data.get(POST_ID)
            if post_id is None:
                return (
                    jsonify({"ok": False, "error": "PATCH post requires post_id"}),
                    400,
                )

            old_post = db.get_post_by_id(int(post_id))
            if not old_post:
                return jsonify({"ok": False, "error": "post not found"}), 404

            new_content = data.get(CONTENT)
            new_image_ext = data.get(IMAGE_EXT)

            if not new_content and not new_image_ext:
                return (
                    jsonify(
                        {
                            "ok": False,
                            "error": "PATCH post requires content and/or image_ext",
                        }
                    ),
                    400,
                )

            author = _unwrap(old_post.get(USER_ID))
            if str(author) != str(user[USER_ID]):
                return jsonify({"ok": False, "error": "forbidden"}), 403

            if new_content:
                db.connection.execute(
                    "UPDATE posts SET json = json_set(json, '$.content', ?) WHERE post_id = ?",
                    (new_content, int(post_id)),
                )
            if new_image_ext:
                db.connection.execute(
                    "UPDATE posts SET json = json_set(json, '$.image_ext', ?) WHERE post_id = ?",
                    (new_image_ext, int(post_id)),
                )

            db.connection.commit()
            return jsonify({"ok": True, "updated": POST}), 200

        return jsonify({"ok": False, "error": "unknown type"}), 400

    if request.method == PUT:
        req_type = (data.get("type") or "user").lower()

        if req_type == "user":
            new_username = (data.get(USERNAME) or "").strip()
            new_password = data.get(PASSWORD) or ""

            if not new_username or not new_password:
                return (
                    jsonify(
                        {
                            "ok": False,
                            "error": "PUT user requires username and password",
                        }
                    ),
                    400,
                )

            edited = {
                USER_ID: int(user[USER_ID]),
                USERNAME: new_username,
                PASSWORD: generate_password_hash(new_password),
            }

            ok = db.update_user(user, edited)
            if ok:
                db.connection.commit()
            return jsonify({"ok": ok, "replaced": "user"}), (200 if ok else 400)

        if req_type == POST:
            post_id = data.get(POST_ID)
            content = data.get(CONTENT)
            image_ext = data.get(IMAGE_EXT, "NONE")

            if post_id is None or content is None:
                return (
                    jsonify(
                        {"ok": False, "error": "PUT post requires post_id and content"}
                    ),
                    400,
                )

            old_post = db.get_post_by_id(int(post_id))
            if not old_post:
                return jsonify({"ok": False, "error": "post not found"}), 404

            author = _unwrap(old_post.get(USER_ID))
            if str(author) != str(user[USER_ID]):
                return jsonify({"ok": False, "error": "forbidden"}), 403

            db.connection.execute(
                "UPDATE posts SET json = json_set(json, '$.content', ?) WHERE post_id = ?",
                (content, int(post_id)),
            )
            db.connection.execute(
                "UPDATE posts SET json = json_set(json, '$.image_ext', ?) WHERE post_id = ?",
                (image_ext, int(post_id)),
            )
            db.connection.commit()
            return jsonify({"ok": True, "replaced": POST}), 200

        return jsonify({"ok": False, "error": "unknown type"}), 400

    if request.method == DELETE:
        req_type = (data.get("type") or "user").lower()

        if req_type == POST:
            date = data.get(DATE)
            if not date:
                return jsonify({"ok": False, "error": "DELETE post requires date"}), 400

            ok = db.delete_post(str(user[USER_ID]), date)
            if ok:
                db.connection.commit()
            return jsonify({"ok": ok, "deleted": POST}), (200 if ok else 400)

        if req_type == "user":
            db.connection.execute(
                "DELETE FROM posts WHERE json_extract(json, '$.user_id') LIKE ?",
                (["%" + str(user[USER_ID]) + "%"]),
            )
            ok = db.delete_user(str(user[USER_ID]))
            if ok:
                db.connection.commit()
                session.pop("access_token", None)
            return jsonify({"ok": ok, "deleted": "user"}), (200 if ok else 400)

        return jsonify({"ok": False, "error": "unknown type"}), 400


# I am not sure what to do with this.
@app.route("/health")
def health():
    """
    Default route for checking that the website is up and reachable
    Returns:
    json: A json object indicating whether the website is healthy
    """
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=4000)

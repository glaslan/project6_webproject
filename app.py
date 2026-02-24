""" This module is the main entry point for the Flask app """
import os
from datetime import timedelta
from tracemalloc import start
from uuid import uuid4
import traceback

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
from flask import send_from_directory, abort
from flask_jwt_extended import JWTManager
from werkzeug.security import generate_password_hash, check_password_hash

from src.constants import (
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

from src.auth_controller import AuthController
from src.post_controller import PostController
from src.database_access_layer import Database

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
    Gets the current user ID from the session
    Returns:    The current user ID, or None if the token is invalid or not present
    """
    return session.get(USER_ID)


def get_current_user(auth: AuthController = None) -> dict | None:
    """
    Gets the current user from the database using the user ID from the session token
    Args:
        auth: Optional existing AuthController to reuse (avoids creating new connection)
    Returns:    The current user dictionary, or None if the user is not found or the token is invalid
    """
    uid = get_current_user_id()
    if uid is None:
        return None

    if auth is not None:
        user = auth.db.get_user_by_id(uid)
        return _normalise_user(user)

    with AuthController(DATABASE_PATH) as auth:
        user = auth.db.get_user_by_id(uid)
        return _normalise_user(user)


@app.route("/", methods=[GET, POST])
def home():
    """
    Docstring for home
    Default route for the home page, also handles post creation
    Returns:   template: The home page html template, with the list of posts and the current user (if logged in)
    """

    with Database(DATABASE_PATH) as db:
        with AuthController(db=db) as auth:
            with PostController(db=db) as posts:

                user = get_current_user(auth)

                if request.method == POST:
                    if not user:
                        flash("You must be logged in to create a post", "error")
                        return redirect(url_for("login"))

                    content = (request.form.get(CONTENT) or "").strip()
                    if not content:
                        flash("Post content cannot be empty", "error")
                        return redirect(url_for("home"))

                    post_id = posts.generate_uuid()

                    image_ext = None
                    file = request.files.get("image")
                    if file and file.filename:
                        image_ext = posts.upload_image(file, post_id, UPLOAD_DIR)
                        if not image_ext:
                            flash("Invalid image file", "error")
                            return redirect(url_for("home"))

                    post_obj = {
                        POST_ID: str(post_id),
                        USER_ID: str(user[USER_ID]),
                        CONTENT: content,
                        IMAGE_EXT: f".{image_ext}" if image_ext else "NONE",
                    }

                    print(post_obj[IMAGE_EXT])
                    print(posts.get_filename(post_obj))

                    ok = posts.create_post(post_obj)
                    if ok:
                        flash("Post created successfully", "success")
                    else:
                        flash("Failed to create post", "error")
                    return redirect(url_for("home"))

                PAGE_SIZE = 10
                try:
                    page = int(request.args.get("page", "1"))
                except ValueError:
                    page = 1
                page = max(page, 1)

                page_posts, has_more = posts.get_posts(page, PAGE_SIZE)
                page_posts = [_normalise_post(p) for p in page_posts]

                return render_template(
                    "html/home.html",
                    user=user,
                    posts=page_posts,
                    post_controller=posts,
                    page=page,
                    has_more=has_more,
                    max_chars=1024,
                )


@app.route("/get_image/<filename>")
def serve_image(filename: str):
    """
    Serves an image file from the UPLOAD_DIR, ensuring that the filename is safe and does not allow directory traversal
    Args:
        filename: The name of the image file to serve
    Returns:
        The image file if it exists and is safe, or a 400/404 error if the filename is invalid or the file does not exist
    """
    safe_path = os.path.normpath(filename)
    if safe_path.startswith("..") or os.path.isabs(safe_path):
        abort(400)

    full_path = os.path.join(UPLOAD_DIR, safe_path)
    if not os.path.isfile(full_path):
        abort(404)

    return send_from_directory(UPLOAD_DIR, safe_path)


@app.route("/register", methods=[GET, POST, OPTIONS])
def register():
    """
    Docstring for register
    Default route for the registration page, also handles registration form submission
    Returns:
    template: The registration page html template, with the current user (if logged in)
    """

    with AuthController(DATABASE_PATH) as auth:

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
                    "Registration failed. Username may be taken or invalid input.",
                    "error",
                )
                return redirect(url_for("register"))

            user_id = auth.login(potential_new_user)
            if user_id:
                session[USER_ID] = user_id

            flash("Account created successfully.", "success")
            return redirect(url_for("home"))

        return render_template("html/register.html")


@app.route("/logout", methods=[GET, POST])
def logout():
    """
    Logs the user out and clears their session.
    Returns:
        redirect: Redirects to home page for browser requests
        json: JSON response for API requests
    """
    with AuthController(DATABASE_PATH) as auth:

        session.pop(USER_ID, None)
        result = auth.logout()

        if request.headers.get("Accept") == "application/json":
            return jsonify(result)

        flash(result["data"]["message"].capitalize(), "success")
        return redirect(url_for("home"))


@app.route("/login", methods=[GET, POST, OPTIONS])
def login():
    """
    Default route for the login page, also handles login form submission
    Returns:
    template: The login page html template, with the current user (if logged in)
    """

    with AuthController(DATABASE_PATH) as auth:

        if request.method == OPTIONS:
            resp = app.make_response(("", 204))
            resp.headers["Allow"] = "GET, POST, OPTIONS"
            return resp

        user = get_current_user(auth)
        if user:
            flash("You are already logged in", "info")
            return redirect(url_for("home"))

        if request.method == POST:
            username = (request.form.get(USERNAME) or "").strip()
            password = request.form.get(PASSWORD) or ""

            user_id = auth.login({USERNAME: username, PASSWORD: password})
            print(f"user_id: {user_id}")
            if user_id:
                session[USER_ID] = user_id
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

    with Database(DATABASE_PATH) as db:
        with AuthController(db=db) as auth:
            with PostController(db=db) as posts:

                if request.method == OPTIONS:
                    resp = app.make_response(("", 204))
                    resp.headers["Allow"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
                    return resp

                user = get_current_user(auth)
                user = _normalise_user(user)

                data = request.get_json(silent=True) or {}

                method = request.method
                if request.form.get("method"):

                    override_method = request.form.get("method")
                    if override_method == "PATCH":
                        method = PATCH
                    elif override_method == "PUT":
                        method = PUT
                    elif override_method == "DELETE":
                        method = DELETE

                    if request.method == OPTIONS:
                        resp = app.make_response(("", 204))
                        resp.headers["Allow"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
                        return resp

                    user = get_current_user(auth)
                    user = _normalise_user(user)

                if method == GET:
                    all_posts = db.get_all_posts()
                    my_posts = [
                        p for p in all_posts if str(p.get(USER_ID)) == str(user[USER_ID])
                    ]

                    method = request.method
                    if request.form.get("method"):

                        override_method = request.form.get("method")
                        if override_method == "PATCH":
                            method = PATCH
                        elif override_method == "PUT":
                            method = PUT
                        elif override_method == "DELETE":
                            method = DELETE

                    print(method)

                    if not user:
                        if method == GET:
                            flash("Please log in first.", "error")
                            return redirect(url_for("login"))
                        return jsonify({"ok": False, "error": "unauthorized"}), 401

                    if method == GET:
                        my_posts = posts.get_user_posts(str(user[USER_ID]))

                        return render_template(
                            "html/profile.html",
                            user=user,
                            posts=my_posts,
                            post_controller=posts,
                        )
                        return redirect(url_for("profile"))

                    flash("Unknown action.", "error")
                    return redirect(url_for("profile"))

                if method == PATCH:

                    action = request.form.get("action")
                    print(action)

                    if action == "edit_post":

                        date = request.form.get(DATE)
                        post_id = request.form.get(POST_ID)

                        old_post = posts.get_post_by_id(post_id)

                        edited_post = old_post.copy()
                        edited_post[CONTENT] = request.form.get(CONTENT)

                        posts.edit_post(old_post, edited_post, old_post[USER_ID])

                        print("edit")

                        return redirect(url_for("profile"))

                    req_type = (data.get("type") or "user").lower()

                    if req_type == "user":
                        new_username = request.form.get(USERNAME)
                        new_password = request.form.get(PASSWORD)

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

                    if method == POST:
                        action = request.form.get("action")

                        author = _unwrap(old_post.get(USER_ID))
                        if str(author) != str(user[USER_ID]):
                            return jsonify({"ok": False, "error": "forbidden"}), 403

                        edited_post = old_post.copy()
                        edited_post[CONTENT] = new_content
                        edited_post[IMAGE_EXT] = new_image_ext

                        posts.edit_post(old_post, edited_post, old_post[USER_ID])
                        return jsonify({"ok": True, "updated": POST}), 200

                    return jsonify({"ok": False, "error": "unknown type"}), 400

                if method == PUT:
                    new_username = (request.form.get(USERNAME) or user[USERNAME]).strip()
                    new_password = request.form.get(PASSWORD) or user[PASSWORD]

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
                        USER_ID: (user[USER_ID]),
                        USERNAME: new_username,
                        PASSWORD: generate_password_hash(new_password),
                    }

                    ok = auth.db.update_user(user, edited)
                    return redirect(url_for("profile"))

                        if action == "delete_post":
                            date = request.form.get(DATE)
                            if not date:
                                flash("Missing post date.", "error")
                                return redirect(url_for("profile"))

                            ok = posts.delete_post(str(user[USER_ID]), date)
                            flash(
                                "Post deleted." if ok else "Failed to delete post.",
                                "success" if ok else "error",
                            )
                            return redirect(url_for("profile"))

                        flash("Unknown action.", "error")
                        return redirect(url_for("profile"))

                    if method == PATCH:
                        req_type = (data.get("type") or "user").lower()

                        if req_type == "user":
                            new_username = request.form.get(USERNAME)
                            new_password = request.form.get(PASSWORD)

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

                            ok = auth.db.update_user(user, edited)
                            return jsonify({"ok": ok, "updated": "user"}), (200 if ok else 400)

                        if req_type == POST:
                            post_id = data.get(POST_ID)
                            if post_id is None:
                                return (
                                    jsonify(
                                        {"ok": False, "error": "PATCH post requires post_id"}
                                    ),
                                    400,
                                )

                            old_post = posts.get_post_by_id(int(post_id))
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

                            edited_post = old_post.copy()
                            edited_post[CONTENT] = new_content
                            edited_post[IMAGE_EXT] = new_image_ext

                            posts.edit_post(old_post, edited_post, old_post[USER_ID])
                            return jsonify({"ok": True, "updated": POST}), 200

                        return jsonify({"ok": False, "error": "unknown type"}), 400

                    if method == PUT:
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

                            ok = auth.db.update_user(user, edited)
                            return jsonify({"ok": ok, "replaced": "user"}), (200 if ok else 400)

                        if req_type == POST:
                            post_id = data.get(POST_ID)
                            content = data.get(CONTENT)
                            image_ext = data.get(IMAGE_EXT, "NONE")

                            if post_id is None or content is None:
                                return (
                                    jsonify(
                                        {
                                            "ok": False,
                                            "error": "PUT post requires post_id and content",
                                        }
                                    ),
                                    400,
                                )

                            old_post = db.get_post_by_id(int(post_id))
                            if not old_post:
                                return jsonify({"ok": False, "error": "post not found"}), 404

                            author = _unwrap(old_post.get(USER_ID))
                            if str(author) != str(user[USER_ID]):
                                return jsonify({"ok": False, "error": "forbidden"}), 403

                            edited_post = old_post.copy()
                            edited_post[CONTENT] = new_content
                            edited_post[IMAGE_EXT] = new_image_ext

                            posts.edit_post(old_post, edited_post, old_post[USER_ID])

                            return jsonify({"ok": True, "replaced": POST}), 200

                        return jsonify({"ok": False, "error": "unknown type"}), 400

                    if method == DELETE:
                        req_type = (data.get("type") or "user").lower()

                        if req_type == POST:
                            date = data.get(DATE)
                            if not date:
                                return (
                                    jsonify(
                                        {"ok": False, "error": "DELETE post requires date"}
                                    ),
                                    400,
                                )

                            ok = posts.delete_post(str(user[USER_ID]), date)
                            return jsonify({"ok": ok, "deleted": POST}), (200 if ok else 400)

                        if req_type == "user":
                            db.delete_user_posts(user[USER_ID])
                            ok = db.delete_user(str(user[USER_ID]))
                            if ok:
                                session.pop(USER_ID, None)
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
    from waitress import serve
    from src.image_queue import start_worker

    # Start background image processing worker
    start_worker()

    serve(
        app,
        host="0.0.0.0",
        port=4000,
        threads=16,             # Up from default 4
        connection_limit=200,   # Max concurrent connections
        channel_timeout=120,    # Request timeout in seconds
        recv_bytes=65536,       # Larger receive buffer
    )

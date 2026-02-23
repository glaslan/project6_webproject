""" Module for managing posts """
from flask import jsonify, flash
from datetime import datetime
import os
from uuid import uuid4
from werkzeug.utils import secure_filename
import datetime

from src.database_access_layer import Database
from src.constants import *

UPLOAD_FOLDER = "./images/"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
APP_DIR = os.path.abspath(os.path.dirname(__file__))


class PostController:
    """Post controller class"""

    def __init__(self, database_path: str = None, db: Database = None) -> None:
        """Constructor for the PostController class"""
        if db is not None:
            self.db = db
            self._owns_db = False
        else:
            self.db = Database(database_path)
            self._owns_db = True

    # No __del__ - context managers handle cleanup deterministically

    def __enter__(self):
        """Enter context manager to return self for use in 'with' block"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager to close database connection"""
        if getattr(self, '_owns_db', False):
            self.db.close()
        return False

    def create_post(self, post: dict) -> bool:
        """Creates a new post in the database"""

        if post.get(IMAGE_EXT) == None:
            post[IMAGE_EXT] = "NONE"

        post[DATE] = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return self.db.insert_post(post)

    def get_posts(self, page: int = None, page_size: int = 10) -> tuple[list[dict], bool]:
        """Returns a list of posts in the database, optionally paginated, with usernames included.

        Returns:
            tuple: (list of posts, has_more boolean)
        """

        post_collection = []
        query = """
            SELECT
                p.post_id,
                json_extract(p.json, '$.user_id'),
                json_extract(p.json, '$.image_ext'),
                json_extract(p.json, '$.content'),
                json_extract(p.json, '$.date'),
                COALESCE(json_extract(u.json, '$.username'), '[deleted]')
            FROM posts p
            LEFT JOIN users u ON json_extract(p.json, '$.user_id') = CAST(u.user_id AS TEXT)
            ORDER BY json_extract(p.json, '$.date') DESC
        """
        if page is not None:
            # Fetch one extra to check if there are more pages
            query += f" LIMIT {page_size + 1} OFFSET {(page-1)*page_size}"

        posts = self.db.connection.execute(query).fetchall()

        # Check if there are more posts than page_size
        has_more = len(posts) > page_size if page is not None else False
        # Only return up to page_size posts
        posts = posts[:page_size] if page is not None else posts

        for post_id, user_id, image_ext, content, date, username in posts:
            structured_post = {}
            structured_post[POST_ID] = validate_value(post_id)
            structured_post[USER_ID] = validate_value(user_id)
            structured_post[IMAGE_EXT] = validate_value(image_ext)
            structured_post[CONTENT] = validate_value(content)
            structured_post[DATE] = validate_value(date)
            structured_post[USERNAME] = validate_value(username) or "[deleted]"
            post_collection.append(structured_post)

        return post_collection, has_more

    def get_user_posts(self, user_id: str) -> list[dict]:
        """Returns all posts for a specific user, with username included"""

        post_collection = []
        query = """
            SELECT
                p.post_id,
                json_extract(p.json, '$.user_id'),
                json_extract(p.json, '$.image_ext'),
                json_extract(p.json, '$.content'),
                json_extract(p.json, '$.date'),
                COALESCE(json_extract(u.json, '$.username'), '[deleted]')
            FROM posts p
            LEFT JOIN users u ON json_extract(p.json, '$.user_id') = CAST(u.user_id AS TEXT)
            WHERE json_extract(p.json, '$.user_id') = ?
            ORDER BY json_extract(p.json, '$.date') DESC
        """
        posts = self.db.connection.execute(query, (user_id,)).fetchall()

        for post_id, uid, image_ext, content, date, username in posts:
            structured_post = {}
            structured_post[POST_ID] = validate_value(post_id)
            structured_post[USER_ID] = validate_value(uid)
            structured_post[IMAGE_EXT] = validate_value(image_ext)
            structured_post[CONTENT] = validate_value(content)
            structured_post[DATE] = validate_value(date)
            structured_post[USERNAME] = validate_value(username) or "[deleted]"
            post_collection.append(structured_post)

        return post_collection

    def get_post(self, date) -> dict:
        """Returns a specific post from the database"""

        return self.db.get_post_by_date(date)

    def get_post_by_id(self, id) -> dict:
        """Returns a specific post from the database"""

        return self.db.get_post_by_id(id)

    def edit_post(self, old_post: dict, edited_post: dict, user_id) -> bool:
        """Edits a specific post in the database"""
        return self.db.update_post(old_post, edited_post, user_id)

    def delete_post(self, user_id: int, date: str) -> bool:
        """Deletes a specific post from the database"""
        return self.db.delete_post(user_id, date)

    def generate_uuid(self) -> int:

        # using uuid4 for fully random uuid
        while True:
            uuid = uuid4()

            # if getting a post based on post_id does return None
            # then the id does not exist and can be used to
            # generate a new post
            # (this should almost never not be None but just in case)
            if self.db.get_post_by_id(uuid) == None:
                return uuid

    def get_filename(self, post: dict):
        """
        TODO
        """
        if post[IMAGE_EXT] == "NONE":
            return None
        return f"{post[POST_ID]}{post[IMAGE_EXT]}"

    def get_username(self, post: dict):
        user = self.db.get_user_by_id(post.get(USER_ID))
        if user is None:
            return "[deleted]"
        return user.get(USERNAME)

    def allowed_file(filename) -> bool:
        """Check if the uploaded image has an acceptable extension"""
        return (
            "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
        )

    def upload_image(self, file, post_id, upload_dir) -> bool:
        """
        Opens file, checks to ensure it is an image then saves it to the uploads folder.
        Image resizing is done asynchronously in a background thread to avoid blocking.
        """
        if "." not in file.filename:
            return None

        image_ext = file.filename.rsplit(".", 1)[1].lower()

        if image_ext not in ALLOWED_EXTENSIONS:
            return None

        safe_name = f"{post_id}.{image_ext}"
        file_path = os.path.join(upload_dir, safe_name)
        file.save(file_path)

        # Queue resize in background instead of blocking the request
        from src.image_queue import queue_resize
        queue_resize(file_path)

        return image_ext


def validate_value(value):

    if not value:
        return value
    if isinstance(value, tuple):
        return value[0]
    return value


# db = Database("test.db")
# pc = PostController(db)
# pc.create_post(
#     {USER_ID: "1342", IMAGE_EXT: None, CONTENT: "im a post", POST_ID: 324354676576}
# )
# pc.create_post({USER_ID: "678", IMAGE_EXT: None, CONTENT: "test", POST_ID: 2435453})

# print(db.get_all_posts())

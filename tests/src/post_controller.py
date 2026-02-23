""" Module for managing posts """
from flask import jsonify, flash
from datetime import datetime
import os
from uuid import uuid4
from werkzeug.utils import secure_filename
import datetime
from PIL import Image

from src.database_access_layer import Database
from src.constants import *

UPLOAD_FOLDER = "./images/"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
APP_DIR = os.path.abspath(os.path.dirname(__file__))


class PostController:
    """Post controller class"""

    def __init__(self, database_path: str) -> None:
        """Constructor for the PostController class"""
        self.db = Database(database_path)

    def __del__(self) -> None:
        """Destructor for the PostController class"""
        self.db.close()

    def __enter__(self):
        """Enter context manager to return self for use in 'with' block"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager to close database connection"""
        self.db.close()
        return False

    def create_post(self, post: dict) -> bool:
        """Creates a new post in the database"""

        if post.get(IMAGE_EXT) == None:
            post[IMAGE_EXT] = "NONE"

        post[DATE] = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return self.db.insert_post(post)

    def get_posts(self, page) -> list[dict]:
        """Returns a list of all posts in the database"""

        # for each post insert the id into the json so the entire object is represented in a json
        post_collection = []
        posts = self.db.connection.execute(
            f"SELECT post_id, json_extract(json, '$.user_id'), json_extract(json, '$.image_ext'), json_extract(json, '$.content'), json_extract(json, '$.date') FROM posts ORDER BY json_extract(json, '$.date') DESC LIMIT 10 OFFSET {(page-1)*10}"
        ).fetchall()

        # this might be the most cursed for loop i've ever written
        for post_id, user_id, image_ext, content, date in posts:

            structured_post = {}
            structured_post[POST_ID] = validate_value(post_id)
            structured_post[USER_ID] = validate_value(user_id)
            structured_post[IMAGE_EXT] = validate_value(image_ext)
            structured_post[CONTENT] = validate_value(content)
            structured_post[DATE] = validate_value(date)
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
        return self.db.get_user_by_id(post.get(USER_ID)).get(USERNAME)

    def allowed_file(filename) -> bool:
        """Check if the uploaded image has an acceptable extension"""
        return (
            "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
        )

    def upload_image(self, file, post_id, upload_dir) -> bool:
        """
        Opens file, checks to ensure it is an image then saves it to the uploads folder
        """
        if "." in file.filename:
            image_ext = file.filename.rsplit(".", 1)[1].lower()
            safe_name = f"{post_id}.{image_ext}"
            file.save(os.path.join(upload_dir, safe_name))
            image = Image.open(os.path.join(upload_dir, safe_name))
            try:
                scaled_image = image.resize((256, 256))
                scaled_image.save(os.path.join(upload_dir, safe_name))
            finally:
                image.close()
            return image_ext
        return None


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

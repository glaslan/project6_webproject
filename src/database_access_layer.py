import sqlite3 as sql
import datetime
import traceback
import threading

from src.constants import *

# Global lock for SQLite write operations - SQLite only allows one writer at a time
_db_write_lock = threading.Lock()


class Database:

    # On initilization, connect/create the database and create the
    # tables if they do not exist
    def __init__(self, path: str):
        """
        Constructor for the Database class, this will create a connection to the database file and/or
        create the file if it does not exist, as well as create the users and posts tables if they
        also do not exist in the database.

        Parameters:
            None

        Returns:
            None

        Raises:
            None

        """

        # create the connection, also creates the database file if it does not exist
        if not path.endswith(".db"):
            path += ".db"

        self._lock = threading.Lock()
        self.connection = sql.connect(path, timeout=60)
        self._closed = False

        # create the user and posts tables if they do not exist
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, json TEXT)"
        )
        self.connection.execute(
            "CREATE TABLE IF NOT EXISTS posts (post_id TEXT PRIMARY KEY, json TEXT)"
        )

        # create indexes on frequently queried JSON fields for performance
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_posts_date ON posts(json_extract(json, '$.date'))"
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(json_extract(json, '$.user_id'))"
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(json_extract(json, '$.username'))"
        )
        self.connection.commit()



    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def insert_user(self, user: dict) -> bool:
        """
        This function will insert a new user into the users tables of the database.

        Parameters:
            user (dict): a dictionary containing the json information of the
                         user to be insereted

        Returns:
            bool: if user was successfully inserted or not

        Raises:
            None
        """

        username = validate_value(user.get("username"))
        password = validate_value(user.get("password"))
        user_id = validate_value(user.get("user_id", None))

        json = '{"username": "' + username + '", "password": "' + password + '"}'

        # insert the user_id with the user if it was passed (primarliy for the update user function)
        with _db_write_lock:
            try:
                if user_id:
                    self.connection.execute(
                        "INSERT INTO users (user_id, json) VALUES (?, ?)", ([user_id, json])
                    )
                    self.connection.commit()
                else:
                    self.connection.execute("INSERT INTO users (json) VALUES (?)", ([json]))
                    self.connection.commit()
                return True
            except sql.IntegrityError:
                print("Integrity Violated")
                return False

    def insert_post(self, post: dict) -> bool:
        """
        This function inserts a post into the post table of the database, the
        post object should contain user_id, image_extension, and content.

        Parameters:
            post (dict): a dictionary containing the json information of the
                         post to be insereted

        Returns:
            bool: if user was successfully inserted or not

        Raises:
            None
        """

        # extract the values out of the post object/dictionary
        post_id = validate_value(post.get(POST_ID))
        content = validate_value(post.get(CONTENT))
        image_ext = validate_value(post.get(IMAGE_EXT))
        date = validate_value(post.get(DATE))
        user_id = validate_value(post.get(USER_ID))

        # construct the json object
        json = (
            '{"user_id": "'
            + user_id
            + '", "content": "'
            + content
            + '", "image_ext": "'
            + image_ext
            + '", "date": "'
            + date
            + '"}'
        )

        # insert the post into the databse
        with _db_write_lock:
            try:
                self.connection.execute(
                    "INSERT INTO posts (post_id, json) VALUES (?, ?)",
                    ([str(post_id), json]),
                )
                self.connection.commit()
                return True
            except sql.IntegrityError:
                traceback.print_exc()
                return False

    def get_user_by_username(self, username: str) -> dict | None:
        """
        This function will return a user object/dict based on the username
        passed to the function

        Parameters:
            username: username of the user object to get

        Returns:
            dict: user object that has the specified username
            None: if there is no user with the specfiied username

        Raises:
            None
        """

        user = {}

        user_id = self.connection.execute(
            "SELECT user_id FROM users WHERE json_extract(json, '$.username') LIKE ?",
            (["%" + username + "%"]),
        ).fetchone()
        password = self.connection.execute(
            "SELECT json_extract(json, '$.password') FROM users WHERE json_extract(json, '$.username') LIKE ?",
            (["%" + username + "%"]),
        ).fetchone()

        if user_id is not None:
            user[USERNAME] = validate_value(username)
            user[PASSWORD] = validate_value(password)
            user[USER_ID] = validate_value(user_id)
            return user

        return None

    def get_user_by_id(self, user_id: int) -> dict | None:
        """
        This function will return a user object/dict based on the user_id
        passed to the function

        Parameters:
            user_id: user_id of the user object to get

        Returns:
            dict: user object that has the specified user_id
            None: if there is no user with the specfiied user_id

        Raises:
            None
        """

        user = {}

        username = self.connection.execute(
            "SELECT json_extract(json, '$.username') FROM users WHERE user_id LIKE ?",
            (["%" + str(user_id) + "%"]),
        ).fetchone()
        password = self.connection.execute(
            "SELECT json_extract(json, '$.password') FROM users WHERE user_id LIKE ?",
            (["%" + str(user_id) + "%"]),
        ).fetchone()

        if username is not None:
            user[USERNAME] = validate_value(username)
            user[PASSWORD] = validate_value(password)
            user[USER_ID] = validate_value(user_id)
            return user

        return None

    def get_post_by_date(self, date: str) -> dict | None:
        """
        This function will return a post object/dict based on the date
        passed to the function

        Parameters:
            date: date of the post object to get

        Returns:
            dict: post object that has the specified date
            None: if there is no post with the specfiied date

        Raises:
            None
        """

        post = {}

        # extract the individual values of each post
        user_id = self.connection.execute(
            "SELECT json_extract(json, '$.user_id') FROM posts WHERE json_extract(json, '$.date') LIKE ?",
            (["%" + date + "%"]),
        ).fetchone()
        image_ext = self.connection.execute(
            "SELECT json_extract(json, '$.image_ext') FROM posts WHERE json_extract(json, '$.date') LIKE ?",
            (["%" + date + "%"]),
        ).fetchone()
        content = self.connection.execute(
            "SELECT json_extract(json, '$.content') FROM posts WHERE json_extract(json, '$.date') LIKE ?",
            (["%" + date + "%"]),
        ).fetchone()
        post_id = self.connection.execute(
            "SELECT post_id FROM posts WHERE json_extract(json, '$.date') LIKE ?",
            (["%" + date + "%"]),
        ).fetchone()

        # put the post object together if it exists in the database
        if user_id is not None:
            post[USER_ID] = validate_value(user_id)
            post[IMAGE_EXT] = validate_value(image_ext)
            post[CONTENT] = validate_value(content)
            post[DATE] = validate_value(date)
            post[POST_ID] = validate_value(post_id)
            return post

        # if the post object was not found then return None
        return None

    def get_post_by_id(self, post_id: int) -> dict | None:
        """
        This function will return a post object/dict based on the post_id
        passed to the function

        Parameters:
            post_id: post_id of the post object to get

        Returns:
            dict: post object that has the specified date
            None: if there is no post with the specfiied date

        Raises:
            None
        """

        post = {}

        # extract the individual values of each post
        user_id = self.connection.execute(
            "SELECT json_extract(json, '$.user_id') FROM posts WHERE post_id = ?",
            [str(post_id)],
        ).fetchone()
        image_ext = self.connection.execute(
            "SELECT json_extract(json, '$.image_ext') FROM posts WHERE post_id = ?",
            [str(post_id)],
        ).fetchone()
        content = self.connection.execute(
            "SELECT json_extract(json, '$.content') FROM posts WHERE post_id = ?",
            [str(post_id)],
        ).fetchone()
        date = self.connection.execute(
            "SELECT json_extract(json, '$.date') FROM posts WHERE post_id = ?",
            [str(post_id)],
        ).fetchone()

        # put the post object together if it exists in the database
        if user_id is not None:
            post[USER_ID] = validate_value(user_id)
            post[IMAGE_EXT] = validate_value(image_ext)
            post[CONTENT] = validate_value(content)
            post[DATE] = validate_value(date)
            post[POST_ID] = validate_value(post_id)
            return post

        # if the post object was not found then return None
        return None

    def get_all_posts(self) -> list[dict]:
        """
        This function will return all the post objects in the database

        Parameters:
            None

        Returns:
            list[dict]: list of every post object, list will be empty if no posts exists

        Raises:
            None
        """

        post_collection = []
        posts = self.connection.execute(
            "SELECT post_id, json_extract(json, '$.user_id'), json_extract(json, '$.image_ext'), json_extract(json, '$.content'), json_extract(json, '$.date') FROM posts ORDER BY json_extract(json, '$.date') DESC"
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

    def get_post_count(self) -> int:
        """ """
        return self.connection.execute("SELECT COUNT(*) FROM posts").fetchone()[0]

    def update_post(self, old_post: dict, edited_post: dict, user_id: int) -> bool:
        """
        This function updates a posts content and image_ext atomically

        Parameters:
            useer_id: the id of the logged in user
            old_post: the post to be edited
            edited_post: the post with the edited contents to update

        Returns:
            bool: True if post can/was updated, False if it could not be

        Raises:
            None
        """

        # double check user_id of logged in user is the same as the original post
        author = old_post.get(USER_ID)

        if author != user_id:
            return False

        post_id = old_post.get(POST_ID)
        content = edited_post.get(CONTENT)
        image = edited_post.get(IMAGE_EXT)

        with _db_write_lock:
            try:
                # Single atomic update for both fields
                self.connection.execute(
                    "UPDATE posts SET json = json_set(json, '$.content', ?, '$.image_ext', ?) WHERE post_id = ?",
                    [content, image, str(post_id)],
                )
                self.connection.commit()
                return True
            except Exception:
                return False

    def update_user(self, old_user: dict, edited_user: dict) -> bool:
        """
        This function updates a user object in the database atomically

        Parameters:
            old_user: the logged in user object
            edited_user: the user object with the edited username and password

        Returns:
            bool: True if user can/was updated, False if it could not be

        Raises:
            None
        """

        # make sure both users have the same user_id
        if old_user.get(USER_ID) != edited_user.get(USER_ID):
            return False

        user_id = edited_user.get(USER_ID)
        username = validate_value(edited_user.get("username"))
        password = validate_value(edited_user.get("password"))
        json_str = '{"username": "' + username + '", "password": "' + password + '"}'

        with _db_write_lock:
            try:
                # Use atomic UPDATE instead of DELETE + INSERT
                self.connection.execute(
                    "UPDATE users SET json = ? WHERE user_id = ?",
                    [json_str, user_id],
                )
                self.connection.commit()
                return True
            except Exception:
                return False

    def delete_user(self, user_id: int) -> bool:
        """
        This function deletes a user object from the database

        Parameters:
            user_id: the user_id of the logged in user to delete

        Returns:
            bool: True if user can/was deleted, False if it could not be

        Raises:
            None
        """

        with _db_write_lock:
            try:
                data = self.connection.execute(
                    "DELETE FROM users WHERE user_id LIKE ?", ["%" + str(user_id) + "%"]
                )
                self.connection.commit()
                return data is not None
            except Exception:
                return False

    def delete_post(self, user_id: int, date: str):
        """
        This function will delete the specified post

        Parameters:
            user_id: id of the user that made the post, must match the logged in user
            date: the date at which the post was made

        Returns:
            bool: true if the deletion was successful, false if not
        """
        with _db_write_lock:
            try:
                data = self.connection.execute(
                    "DELETE FROM posts WHERE json_extract(json, '$.user_id') LIKE ? and json_extract(json, '$.date') LIKE ?",
                    ["%" + str(user_id) + "%", "%" + date + "%"],
                )
                self.connection.commit()
                return data is not None
            except Exception:
                return False

    def delete_user_posts(self, user_id: int) -> bool:
        """
        Delete all posts by a user

        Parameters:
            user_id: the user_id whose posts should be deleted

        Returns:
            bool: True if deletion was successful, False if not
        """
        with _db_write_lock:
            try:
                self.connection.execute(
                    "DELETE FROM posts WHERE json_extract(json, '$.user_id') = ?",
                    [str(user_id)],
                )
                self.connection.commit()
                return True
            except Exception:
                return False

    def close(self) -> None:
        """
        Closes the conntection to the database

        Parameters:
            None

        Returns:
            None

        Raises:
            None
        """
        with self._lock:
            if not self._closed:
                self._closed = True
                try:
                    self.connection.close()
                except Exception:
                    pass  # Connection may already be closed

    def reset_tables(self) -> None:
        """
        **ONLY USE IN TESTS ON TEST DATABASE DO NOT WIPE OUR USERS DATA WE CAN SELL IT**
        """

        with _db_write_lock:
            # remvoe old tables
            self.connection.execute("DROP TABLE IF EXISTS users")
            self.connection.execute("DROP TABLE IF EXISTS posts")

            # recreate the tables
            self.connection.execute(
                "CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, json TEXT)"
            )
            self.connection.execute(
                "CREATE TABLE IF NOT EXISTS posts (post_id INTEGER PRIMARY KEY, json TEXT)"
            )

            self.connection.commit()


def validate_value(value):

    if not value:
        return value
    if isinstance(value, tuple):
        return value[0]
    return value

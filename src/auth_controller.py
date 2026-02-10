"""Module for validating user authentication"""


import traceback
from flask import jsonify
from flask_login import logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token

from src.database_access_layer import Database
from src.constants import *


class AuthController:
    """Auth controller class meant to handle user sessions and authentication"""

    min_password_length = 8

    def __init__(self, database_path: str):
        self.db = Database(database_path)

    def register(self, user: dict) -> dict | None:
        """
        Registers a new user given the user's information.
        Returns:
        dict: the validated user information
        None: when an error occurs or the provided info is invalid
        """
        local_user = user.copy()
        is_taken = self.db.get_user_by_username(local_user.get(USERNAME))
        if is_taken:
            print("Username Taken")
            return None
        if len(local_user[PASSWORD]) < self.min_password_length:
            print("Password too short")
            return None

        # Hash the password before storing
        local_user[PASSWORD] = self._hash_password(local_user[PASSWORD])

        if self.db.insert_user(local_user):
            return local_user
        return None

    def login(self, user) -> str | None:
        """
        Attempt to log a user into the site.
        Returns:
        str: user_id on successful login
        None: login failed
        """
        print(user)
        if self._verify_password(user[USERNAME], user[PASSWORD]):
            # Retrieve full user data from database for token generation
            user = self.db.get_user_by_username(user[USERNAME])
            if user:
                return user.get(USER_ID, None)
        return None

    def logout(self):
        """
        Attempt to log the user out of the site.
        Returns:
        json: message indicating logout
        """
        logout_user()
        return jsonify({"result": 200, "data": {"message": "logout success"}})

    def _hash_password(self, password) -> str:
        """
        Hashes the given user password string to be sent to the database.
        This is useless abstraction.
        Returns:
        str: the hashed password
        """
        hashed_password = generate_password_hash(password)
        return hashed_password

    def _verify_password(self, username, password) -> bool:
        """
        Talks with the database to verify that the password for the user exists.
        Looks up the user in the database, pulls the hashed password and
        compares it to the hash of the given password.
        Returns:
        bool: True means that the information matches, false means that it doesn't
        """
        user = self.db.get_user_by_username(username)
        if user is None:
            return False
        user_password = user[PASSWORD]
        return check_password_hash(user_password, password)

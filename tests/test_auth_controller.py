import pytest
from auth_controller import AuthController
from database_access_layer import Database
from werkzeug.security import check_password_hash, generate_password_hash


def auth_controller():
    db_path = "tests/test_database.db"
    controller = AuthController(db_path)
    yield controller
    controller.db.connection.close()


class TestAuthController:
    user = {
        "username": "test_user",
        "password": "test_password",
    }

    def test_register(self, auth_controller):
        auth_controller.register(TestAuthController.user)
        user_in_db = auth_controller.db.get_user_by_username(self.user["username"])
        assert user_in_db is not None
        print(user_in_db)
        assert user_in_db["username"] == self.user["username"]
        if type(user_in_db["password"]) is tuple:
            (password, *_) = user_in_db["password"]
        else:
            password = user_in_db["password"]
        print(password)
        print(type(password))
        assert check_password_hash(password, self.user["password"])

    def test_login(self, auth_controller):
        assert auth_controller.login(self.user) is not None

    def test_logout(self, auth_controller):
        """
        Tests that the logout function returns a JSON response with result 200
        and a message indicating logout success after a user has been logged in.
        """
        auth_controller.login(self.user)
        assert auth_controller.logout() == {
            "result": 200,
            "data": {"message": "logout success"},
        }

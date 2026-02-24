import pytest
from src.auth_controller import AuthController
from src.database_access_layer import Database
from werkzeug.security import check_password_hash, generate_password_hash
from src.constants import *


def auth_controller():
    db_path = "tests/test_database.db"
    controller = AuthController(db_path)
    yield controller
    controller.db.connection.close()


class TestAuthController:
    user = {
        "user_id": "1234",
        "username": "test_user",
        "password": "test_password",
    }

    # TEST-AC-FUNC-0001
    def test_hash_password(self):

        ac = AuthController(TEST_DATABASE_PATH)
        ac.db.reset_tables()

        ac.register(self.user)

        assert ac._hash_password(self.user[PASSWORD]) is not self.user[PASSWORD]

    # TEST-AC-FUNC-0002
    def test_logout(self):

        ac = AuthController(TEST_DATABASE_PATH)
        ac.db.reset_tables()

        result = ac.logout()

        assert result == {"result": 200, "data": {"message": "logout success"}}

    # TEST-AC-ITGR-0001
    def test_register(self):

        ac = AuthController(TEST_DATABASE_PATH)
        ac.db.reset_tables()

        ac.register(self.user)

        result = ac.db.get_user_by_username(self.user[USERNAME])

        assert result is not None

        assert result[USERNAME] == self.user[USERNAME]
        assert ac._verify_password(result[USERNAME], self.user[PASSWORD])

    # TEST-AC-ITGR-0002
    def test_register_invalid(self):

        ac = AuthController(TEST_DATABASE_PATH)
        ac.db.reset_tables()

        ac.register(self.user)
        result = ac.register(self.user)

        assert result is None

    # TEST-AC-ITGR-0003
    def test_register_short_password(self):

        ac = AuthController(TEST_DATABASE_PATH)
        ac.db.reset_tables()

        user = {
            "username": "test_user",
            "password": "test",
        }

        result = ac.register(user)

        assert result is None

    # TEST-AC-ITGR-0004
    def test_login(self):

        ac = AuthController(TEST_DATABASE_PATH)
        ac.db.reset_tables()

        ac.register(self.user)

        result = ac.login(self.user)

        assert result == self.user[USER_ID]

    # TEST-AC-ITGR-0005
    def test_login_invalid(self):

        ac = AuthController(TEST_DATABASE_PATH)
        ac.db.reset_tables()

        user = {
            "username": "test_user",
            "password": "wrong_password",
        }

        ac.register(self.user)

        result = ac.login(user)

        assert result == None

    # TEST-AC-ITGR-0006
    def test_verify_password(self):

        ac = AuthController(TEST_DATABASE_PATH)
        ac.db.reset_tables()

        ac.register(self.user)

        result = ac._verify_password(self.user[USERNAME], self.user[PASSWORD])

        assert result == True

    # TEST-AC-ITGR-0007
    def test_verify_password_invalid(self):

        ac = AuthController(TEST_DATABASE_PATH)
        ac.db.reset_tables()

        ac.register(self.user)

        result = ac._verify_password(self.user[USERNAME], "invalid_password")

        assert result == False

    # def test_register(self, auth_controller):
    #     auth_controller.register(TestAuthController.user)
    #     user_in_db = auth_controller.db.get_user_by_username(self.user["username"])
    #     assert user_in_db is not None
    #     print(user_in_db)
    #     assert user_in_db["username"] == self.user["username"]
    #     if type(user_in_db["password"]) is tuple:
    #         (password, *_) = user_in_db["password"]
    #     else:
    #         password = user_in_db["password"]
    #     print(password)
    #     print(type(password))
    #     assert check_password_hash(password, self.user["password"])

    # def test_login(self, auth_controller):
    #     assert auth_controller.login(self.user) is not None

    # def test_logout(self, auth_controller):
    #     """
    #     Tests that the logout function returns a JSON response with result 200
    #     and a message indicating logout success after a user has been logged in.
    #     """
    #     auth_controller.login(self.user)
    #     assert auth_controller.logout() == {
    #         "result": 200,
    #         "data": {"message": "logout success"},
    #     }

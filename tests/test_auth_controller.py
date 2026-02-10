import pytest
from src.auth_controller import AuthController
from src.DatabaseAccessLayer import Database
from werkzeug.security import generate_password_hash


@pytest.fixture
def auth_controller():
    db_path = "tests/test_database.db"
    db = Database(db_path)
    controller = AuthController(db)
    yield controller
    controller.db.connection.close()


class TestAuthController:
    def test_register(self, auth_controller):
        user = {
            "username": "test_user",
            "password": "test_password",
        }
        assert auth_controller.register(user) == user
        user_in_db = auth_controller.db.get_user_by_username(user["username"])
        assert user_in_db is not None
        print(user_in_db)
        assert user_in_db["username"] == user["username"]
        assert user_in_db["password"] == generate_password_hash(
            user["password"]
        )

    def test_login(self, auth_controller):
        user = {
            "username": "test_user",
            "password": "test_password",
        }
        auth_controller.register(user)

        assert auth_controller.login(user) is not None

    def test_logout(self, auth_controller):
        user = {
            "username": "test_user",
            "password": "test_password",
        }
        auth_controller.register(user)
        auth_controller.login(user)
        assert auth_controller.logout(user) == {
            "result": 200,
            "data": {"message": "logout success"},
        }

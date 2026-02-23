import pytest
from src.auth_controller import AuthController
from src.database_access_layer import Database
from src.constants import *


@pytest.fixture
class TestDatabase:

    # TEST-DB-FUNC-0001
    def test_insert_user(self):

        # initialize
        db = Database(TEST_DATABASE_PATH)
        db.reset_tables()
        user = {
            USERNAME: "test_user",
            PASSWORD: "test_password",
        }

        # compute
        result = db.insert_user(user)

        # assert
        assert result is True

    # TEST-DB-FUNC-0002
    def test_insert_taken_user(self):

        # initialize
        db = Database(TEST_DATABASE_PATH)
        db.reset_tables()
        user = {USERNAME: "test_user", PASSWORD: "test_password", USER_ID: "1234"}

        # compute
        result1 = db.insert_user(user)
        result2 = db.insert_user(user)

        # assert
        assert result1 is True
        assert result2 is False

    # TEST-DB-FUNC-0003
    def test_insert_post(self):

        # initialize
        db = Database(TEST_DATABASE_PATH)
        db.reset_tables()
        post = {
            POST_ID: "123456789",
            USER_ID: "1234",
            CONTENT: "test",
            IMAGE_EXT: "NONE",
            DATE: "2026",
        }

        # compute
        result = db.insert_post(post)

        # assert
        assert result is True

    # TEST-DB-FUNC-0004
    def test_insert_taken_post(self):

        # initialize
        db = Database(TEST_DATABASE_PATH)
        db.reset_tables()
        post = {
            POST_ID: "123456789",
            USER_ID: "1234",
            CONTENT: "test",
            IMAGE_EXT: "NONE",
            DATE: "2026",
        }

        # compute
        result1 = db.insert_post(post)
        result2 = db.insert_post(post)

        # assert
        assert result1 is True
        assert result2 is False

    # TEST-DB-FUNC-0005
    def test_get_user_by_username(self):

        # initialize
        db = Database(TEST_DATABASE_PATH)
        db.reset_tables()
        user = {USERNAME: "test_user", PASSWORD: "test_password", USER_ID: "123"}

        # compute
        result1 = db.get_user_by_username(user[USERNAME])

        db.insert_user(user)

        result2 = db.get_user_by_username(user[USERNAME])

        # assert
        assert result1 is None
        assert result2[USER_ID] == "123"
        assert result2[USERNAME] == "test_user"
        assert result2[PASSWORD] == "test_password"

    # TEST-DB-FUNC-0006
    def test_get_user_by_id(self):

        # initialize
        db = Database(TEST_DATABASE_PATH)
        db.reset_tables()
        user = {USERNAME: "test_user", PASSWORD: "test_password", USER_ID: "123"}

        # compute
        result1 = db.get_user_by_id(user[USER_ID])

        db.insert_user(user)

        result2 = db.get_user_by_id(user[USER_ID])

        # assert
        assert result1 is None
        assert result2[USER_ID] == "123"
        assert result2[USERNAME] == "test_user"
        assert result2[PASSWORD] == "test_password"

    # TEST-DB-FUNC-0007
    def test_get_post_by_date(self):

        # initialize
        db = Database(TEST_DATABASE_PATH)
        db.reset_tables()
        post = {
            POST_ID: "123456789",
            USER_ID: "1234",
            CONTENT: "test",
            IMAGE_EXT: "NONE",
            DATE: "2026-02-15",
        }

        # compute
        result1 = db.get_post_by_date(post[DATE])

        db.insert_post(post)

        result2 = db.get_post_by_date(post[DATE])

        # assert
        assert result1 is None
        assert result2[USER_ID] == "123"
        assert result2[POST_ID] == "123456789"
        assert result2[DATE] == "2026-02-15"
        assert result2[IMAGE_EXT] == "NONE"
        assert result2[CONTENT] == "test"

    # TEST-DB-FUNC-0008
    def test_get_post_by_id(self):

        # initialize
        db = Database(TEST_DATABASE_PATH)
        db.reset_tables()
        post = {
            POST_ID: "123456789",
            USER_ID: "1234",
            CONTENT: "test",
            IMAGE_EXT: "NONE",
            DATE: "2026-02-15",
        }

        # compute
        result1 = db.get_post_by_id(post[POST_ID])

        db.insert_post(post)

        result2 = db.get_post_by_id(post[POST_ID])

        # assert
        assert result1 is None
        assert result2[USER_ID] == "123"
        assert result2[POST_ID] == "123456789"
        assert result2[DATE] == "2026-02-15"
        assert result2[IMAGE_EXT] == "NONE"
        assert result2[CONTENT] == "test"

    # TEST-DB-FUNC-0009
    def test_get_all_posts(self):

        # initialize
        db = Database(TEST_DATABASE_PATH)
        db.reset_tables()
        post1 = {
            POST_ID: "123456789",
            USER_ID: "1234",
            CONTENT: "test1",
            IMAGE_EXT: "NONE",
            DATE: "2026-02-15",
        }
        post2 = {
            POST_ID: "987654321",
            USER_ID: "4321",
            CONTENT: "test2",
            IMAGE_EXT: ".png",
            DATE: "2026-02-16",
        }

        # compute
        result1 = db.get_all_posts()

        db.insert_post(post1)
        db.insert_post(post2)

        result2 = db.get_all_posts()

        # assert
        assert len(result1) == 0

        assert result2[0][USER_ID] == "1234"
        assert result2[0][POST_ID] == "123456789"
        assert result2[0][DATE] == "2026-02-15"
        assert result2[0][IMAGE_EXT] == "NONE"
        assert result2[0][CONTENT] == "test1"

        assert result2[1][USER_ID] == "4321"
        assert result2[1][POST_ID] == "987654321"
        assert result2[1][DATE] == "2026-02-16"
        assert result2[1][IMAGE_EXT] == ".png"
        assert result2[1][CONTENT] == "test2"

    # TEST-DB-FUNC-0010
    def test_update_post(self):

        # initialize
        db = Database(TEST_DATABASE_PATH)
        db.reset_tables()
        old_post = {
            POST_ID: "123456789",
            USER_ID: "1234",
            CONTENT: "old",
            IMAGE_EXT: "NONE",
            DATE: "2026-02-15",
        }
        new_post = {
            POST_ID: "123456789",
            USER_ID: "1234",
            CONTENT: "edit",
            IMAGE_EXT: ".jpg",
            DATE: "2026-02-15",
        }

        # compute

        db.insert_post(old_post)
        db.update_post(old_post, new_post, old_post[USER_ID])
        result = db.get_post_by_id("123456789")

        # assert
        assert result[USER_ID] == "1234"
        assert result[POST_ID] == "123456789"
        assert result[DATE] == "2026-02-15"
        assert result[IMAGE_EXT] == ".jpg"
        assert result[CONTENT] == "edit"

    # TEST-DB-FUNC-0011
    def test_update_user(self):

        # initialize
        db = Database(TEST_DATABASE_PATH)
        db.reset_tables()
        old_user = {USERNAME: "old_user", PASSWORD: "old_password", USER_ID: "1234"}
        new_user = {USERNAME: "new_user", PASSWORD: "new_password", USER_ID: "1234"}

        # compute

        db.insert_user(old_user)
        db.update_user(old_user, new_user, old_user[USER_ID])
        result = db.get_user_by_id("1234")

        # assert
        assert result[USER_ID] == "1234"
        assert result[USERNAME] == "new_user"
        assert result[PASSWORD] == "new_password"

    # TEST-DB-FUNC-0012
    def test_delete_user(self):

        # initialize
        db = Database(TEST_DATABASE_PATH)
        db.reset_tables()
        user = {USERNAME: "user", PASSWORD: "password", USER_ID: "1234"}

        # compute

        db.insert_user(user)
        result1 = db.get_user_by_username("username")
        db.delete_user(user[USER_ID])
        result2 = db.get_user_by_username("username")

        # assert
        assert result1[USER_ID] == "1234"
        assert result1[USERNAME] == "user"
        assert result1[PASSWORD] == "password"
        assert result2 is None

    # TEST-DB-FUNC-0013
    def test_delete_post(self):

        # initialize
        db = Database(TEST_DATABASE_PATH)
        db.reset_tables()
        post = {
            POST_ID: "123456789",
            USER_ID: "1234",
            CONTENT: "test",
            IMAGE_EXT: "NONE",
            DATE: "2026-02-15",
        }

        # compute

        db.insert_post(post)
        result1 = db.get_post_by_id(post[POST_ID])
        db.delete_post(post[USER_ID], post[DATE])
        result2 = db.get_post_by_id(post[POST_ID])

        # assert
        assert result1[USER_ID] == "1234"
        assert result1[POST_ID] == "123456789"
        assert result1[DATE] == "2026-02-15"
        assert result1[IMAGE_EXT] == "NONE"
        assert result1[CONTENT] == "test"
        assert result2 is None

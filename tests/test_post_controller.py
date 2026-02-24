import pytest
from src.post_controller import PostController
from src.database_access_layer import Database
from src.constants import *
from werkzeug.security import check_password_hash, generate_password_hash


class TestPostController:

    # TEST-PC-FUNC-0001
    def test_generate_uuid(self):

        # initialize
        pc = PostController(TEST_DATABASE_PATH)
        pc.db.reset_tables()

        # compute
        result = pc.generate_uuid()

        # assert
        assert result is not None

    # TEST-PC-FUNC-0002
    def test_get_filename(self):

        # initialize
        pc = PostController(TEST_DATABASE_PATH)
        pc.db.reset_tables()

        post = {
            POST_ID: "123456789",
            USER_ID: "1234",
            IMAGE_EXT: ".png",
            CONTENT: "post1",
            DATE: "2026-02-15 12:30:28",
        }

        # compute
        result = pc.get_filename(post)

        # assert
        assert result == f"123456789.png"

    # TEST-PC-FUNC-0003
    def test_get_filename_no_extension(self):

        # initialize
        pc = PostController(TEST_DATABASE_PATH)
        pc.db.reset_tables()

        post = {
            POST_ID: "123456789",
            USER_ID: "1234",
            IMAGE_EXT: "NONE",
            CONTENT: "post1",
            DATE: "2026-02-15 12:30:28",
        }

        # compute
        result = pc.get_filename(post)

        # assert
        assert result == None

    # TEST-PC-ITGR-0001
    def test_create_post(self):

        # initialize
        pc = PostController(TEST_DATABASE_PATH)
        pc.db.reset_tables()

        post = {
            POST_ID: "123456789",
            USER_ID: "1234",
            IMAGE_EXT: None,
            CONTENT: "post1",
        }

        # compute
        result1 = pc.create_post(post)
        result2 = pc.db.get_post_by_id("123456789")

        # assert
        assert result1 == True
        assert result2[IMAGE_EXT] == "NONE"
        assert result2[DATE] is not None

    # TEST-PC-ITGR-0002
    def test_create_post_invalid_post(self):

        # initialize
        pc = PostController(TEST_DATABASE_PATH)
        pc.db.reset_tables()

        post = {
            POST_ID: "123456789",
            USER_ID: "1234",
            IMAGE_EXT: None,
            CONTENT: "post1",
        }

        # compute
        result1 = pc.create_post(post)
        result2 = pc.create_post(post)

        # assert
        assert result1 == True
        assert result2 == False

    # TEST-PC-ITGR-0003
    def test_get_posts(self):

        # initialize
        pc = PostController(TEST_DATABASE_PATH)
        pc.db.reset_tables()

        post1 = {
            POST_ID: "123456789",
            USER_ID: "1234",
            IMAGE_EXT: "NONE",
            CONTENT: "post1",
            DATE: "2026-02-15 12:30:28",
        }
        post2 = {
            POST_ID: "987654321",
            USER_ID: "4321",
            IMAGE_EXT: "NONE",
            CONTENT: "post2",
            DATE: "2026-02-12 10:24:56",
        }
        post3 = {
            POST_ID: "64352761",
            USER_ID: "3632",
            IMAGE_EXT: "NONE",
            CONTENT: "post3",
            DATE: "2026-01-07 17:38:26",
        }

        # compute
        pc.create_post(post1)
        pc.create_post(post2)
        pc.create_post(post3)

        result, _ = pc.get_posts(1)

        # assert
        assert len(result) == 3

    # TEST-PC-ITGR-0004
    def test_get_username(self):

        # initialize
        pc = PostController(TEST_DATABASE_PATH)
        pc.db.reset_tables()

        post = {
            POST_ID: "123456789",
            USER_ID: "1234",
            IMAGE_EXT: "NONE",
            CONTENT: "post1",
            DATE: "2026-02-15 12:30:28",
        }
        user = {USERNAME: "user", PASSWORD: "password", USER_ID: "1234"}

        # compute
        pc.db.insert_user(user)
        pc.create_post(post)
        result = pc.get_username(post)

        # assert
        assert result == "user"

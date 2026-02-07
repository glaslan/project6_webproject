import sqlite3 as sql
import datetime

from constants import *

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

        self.connection = sql.connect(path)
        
        # create the user and posts tables if they do not exist
        self.connection.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, json TEXT)")
        self.connection.execute("CREATE TABLE IF NOT EXISTS posts (post_id INTEGER PRIMARY KEY, json TEXT)")

    def __del__(self):
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

        username = user.get("username")
        password = user.get("password")
        user_id = user.get("user_id", None)

        json = ('{"username": "' + username + '", "password": "' + password + '"}')

        # insert the user_id with the user if it was passed (primarliy for the update user function)
        try:
            if user_id:
                self.connection.execute("INSERT INTO users (user_id, json) VALUES (?, ?)", ([user_id, json]))
            else:
                self.connection.execute("INSERT INTO users (json) VALUES (?)", ([json]))
            return True
        except sql.IntegrityError:
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
        post_id = post.get(POST_ID)
        content = post.get(CONTENT)
        image_ext = post.get(IMAGE_EXT)
        if image_ext is None:
            image_ext = "NONE"
        user_id = post.get(USER_ID)
        date = str(datetime.datetime.now()) #@Dylan, is this my job or your job? 

        # construct the json object
        json = ('{"user_id": "' + user_id + '", "content": "' + content + '", "image_ext": "' + image_ext + '", "date": "' + date + '"}')

        # insert the post into the databse
        try:
            self.connection.execute("INSERT INTO posts (post_id, json) VALUES (?, ?)", ([post_id, json]))
            return True
        except sql.IntegrityError:
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

        user_id = self.connection.execute("SELECT user_id FROM users WHERE json_extract(json, '$.username') LIKE ?", (["%"+username+"%"])).fetchone()
        password = self.connection.execute("SELECT json_extract(json, '$.password') FROM users WHERE json_extract(json, '$.username') LIKE ?", (["%"+username+"%"])).fetchone()

        if user_id is not None:
            user[USERNAME] = username
            user[PASSWORD] = password
            user[USER_ID] = user_id
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

        username = self.connection.execute("SELECT json_extract(json, '$.username') FROM users WHERE user_id LIKE ?", (["%"+user_id+"%"])).fetchone()
        password = self.connection.execute("SELECT json_extract(json, '$.password') FROM users WHERE user_id LIKE ?", (["%"+user_id+"%"])).fetchone()

        if username is not None:
            user[USERNAME] = username
            user[PASSWORD] = password
            user[USER_ID] = user_id
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
        user_id = self.connection.execute("SELECT json_extract(json, '$.user_id') FROM posts WHERE json_extract(json, '$.date') LIKE ?", (["%"+date+"%"])).fetchone()
        image_ext = self.connection.execute("SELECT json_extract(json, '$.image_ext') FROM posts WHERE json_extract(json, '$.date') LIKE ?", (["%"+date+"%"])).fetchone()
        content = self.connection.execute("SELECT json_extract(json, '$.content') FROM posts WHERE json_extract(json, '$.date') LIKE ?", (["%"+date+"%"])).fetchone()
        post_id = self.connection.execute("SELECT post_id FROM posts WHERE json_extract(json, '$.date') LIKE ?", (["%"+date+"%"])).fetchone()

        # put the post object together if it exists in the database
        if user_id is not None:
            post[USER_ID] = user_id
            post[IMAGE_EXT] = image_ext
            post[CONTENT] = content
            post[DATE] = date
            post[POST_ID] = post_id
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
        user_id = self.connection.execute("SELECT json_extract(json, '$.user_id') FROM posts WHERE post_id = ?", [post_id]).fetchone()
        image_ext = self.connection.execute("SELECT json_extract(json, '$.image_ext') FROM posts WHERE post_id = ?", [post_id]).fetchone()
        content = self.connection.execute("SELECT json_extract(json, '$.content') FROM posts WHERE post_id = ?", [post_id]).fetchone()
        date = self.connection.execute("SELECT json_extract(json, '$.date') FROM posts WHERE post_id = ?", [post_id]).fetchone()

        # put the post object together if it exists in the database
        if user_id is not None:
            post[USER_ID] = user_id
            post[IMAGE_EXT] = image_ext
            post[CONTENT] = content
            post[DATE] = date
            post[POST_ID] = post_id
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
        posts = self.connection.execute("SELECT post_id, json_extract(json, '$.user_id'), json_extract(json, '$.image_ext'), json_extract(json, '$.content'), json_extract(json, '$.date') FROM posts").fetchall()

        # this might be the most cursed for loop i've ever written
        for post_id, user_id, image_ext, content, date in posts:

            structured_post = {}
            structured_post[POST_ID] = post_id
            structured_post[USER_ID] = user_id
            structured_post[IMAGE_EXT] = image_ext
            structured_post[CONTENT] = content
            structured_post[DATE] = date
            post_collection.append(structured_post)

        return post_collection


    def update_post(self, old_post: dict, edited_post: dict, user_id: int) -> bool:
        """
        This function updates a posts content and image_ext 

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
        
        content = edited_post.get(CONTENT)
        image = edited_post.get(IMAGE_EXT)

        try:
            self.connection.execute("UPDATE posts SET json = json_set(json, '$.content', ?) WHERE json_extract(json, '$.user_id') LIKE ?", ([content, "%"+user_id+"%"]))
            self.connection.execute("UPDATE posts SET json = json_set(json, '$.image_ext', ?) WHERE json_extract(json, '$.user_id') LIKE ?", ([content, "%"+image+"%"]))
            return True
        except sql.IntegrityError:
            return False


    def update_user(self, old_user: dict, edited_user: dict) -> bool:
        """
        This function updates a user object in the database

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
        
        return self.delete_user(edited_user.get(USER_ID)) and self.insert_user(edited_user)
        

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

        try:
            return self.connection.execute("DELETE FROM users WHERE user_id LIKE ?", (["%"+user_id+"%"])) is not None
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
        try:
            return self.connection.execute("DELETE FROM posts WHERE json_extract(json, '$.user_id') LIKE ? and json_extract(json, '$.date') LIKE ?", (["%"+user_id+"%", "%"+date+"%"])) is not None
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
        self.connection.close()

    def reset_tables(self) -> None:
        """
        **ONLY USE IN TESTS ON TEST DATABASE DO NOT WIPE OUR USERS DATA WE CAN SELL IT**
        """

        # remvoe old tables
        self.connection.execute("DROP TABLE IF EXISTS users")
        self.connection.execute("DROP TABLE IF EXISTS posts")

        # recreate the tables
        self.connection.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, json TEXT)")
        self.connection.execute("CREATE TABLE IF NOT EXISTS posts (post_id INTEGER PRIMARY KEY, json TEXT)")
        

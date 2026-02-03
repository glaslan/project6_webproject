import sqlite3 as sql
import datetime


class Database:

    # On initilization, connect/create the database and create the 
    # tables if they do not exist 
    def __init__(self):
        '''
        Constructor for the Database class, this will create a connection to the database file and/or
        create the file if it does not exist, as well as create the users and posts tables if they
        also do not exist in the database.

        Parameters:
            None

        Returns:
            None        
        
        Raises:
            None
        
        '''''

        # create the connection, also creates the database file if it does not exist 
        self.connection = sql.connect("database.db")
        
        # create the user and posts tables if they do not exist
        self.connection.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, json TEXT)")
        self.connection.execute("CREATE TABLE IF NOT EXISTS posts (post_id INTEGER PRIMARY KEY, json TEXT)")

    def insert_user(self, user: dict) -> bool:
        '''
        This function will insert a new user into the users tables of the database.

        Parameters:
            user (dict): a dictionary containing the json information of the 
                         user to be insereted
            
        Returns:
            bool: if user was successfully inserted or not

        Raises: 
            None
        '''

        username = user.get("username")
        password = user.get("password")
        user_id = user.get("user_id", None)

        json = ('\{"username": "{:}", "password": "{:}"\}'.format(username, password))

        # insert the user_id with the user if it was passed (primarliy for the update user function)
        if user_id:
            self.connection.execute("INSERT INTO users (user_id, json) VALUES (?, ?)", ([user_id, json]))
        else:
            self.connection.execute("INSERT INTO users (json) VALUES (?)", ([json]))

    def insert_post(self, post: dict) -> bool:
        '''
        This function inserts a post into the post table of the database, the
        post object should contain user_id, image_extension, and content.
        
        Parameters:
            post (dict): a dictionary containing the json information of the 
                         post to be insereted
            
        Returns:
            bool: if user was successfully inserted or not

        Raises: 
            None
        '''

        # extract the values out of the post object/dictionary
        post_id = 1 # PostController.generate_uuid()
        content = post.get("content")
        image_ext = post.get("image_ext")
        user_id = post.get("user_id")
        date = datetime.datetime.now() #@Dylan, is this my job or your job? 

        # construct the json object
        json = ('\{"user_id": "{:}", "content": "{:}", "image_ext": "{:}", "date": "{:}"\}'.format(user_id, content, image_ext, date))

        # insert the post into the databse
        self.connection.execute("INSERT INTO posts (post_id, json) VALUES (?, ?)", ([post_id, json]))
        

    def get_user_by_username(self, username: str) -> dict | None:

        return self.connection.execute("SELECT * FROM users WHERE json_extract(json, '$.username') in '?'", ([username])).fetchone()
        

    def get_user_by_id(self, user_id: int) -> dict | None:
        
        return self.connection.execute("SELECT * FROM users WHERE user_id in '?'", ([user_id])).fetchone()

    def get_post_by_date(self, date: str) -> dict | None:

        return self.connection.execute("SELECT * FROM posts WHERE json_extract(json, '$.date') in '?'", ([date])).fetchone()

    def get_all_post(self) -> list[dict]:

        return self.connection.execute("SELECT * FROM posts").fetchall()

    def update_post(self, old_post: dict, edited_post: dict, user_id: int) -> bool:

        # double check user_id of logged in user is the same as the original post
        author = old_post.get("user_id")

        if author != user_id:
            return False
        
        content = edited_post.get("content")
        image = edited_post.get("image_ext")

        
        self.connection.execute("UPDATE posts SET json = json_set(json, '$.content', ?) WHERE json_extract(json, '$.user_id') in '?'", ([content, user_id]))
        self.connection.execute("UPDATE posts SET json = json_set(json, '$.image_ext', ?) WHERE json_extract(json, '$.user_id') in '?'", ([content, image]))


    def update_user(self, old_user: dict, edited_user: dict) -> bool:

        # make sure both users have the same user_id
        if old_user.get("user_id") != edited_user.get("user_id"):
            return False
        
        self.delete_user(edited_user.get("user_id"))
        self.insert_user(edited_user)

    def delete_user(self, user_id: int) -> bool:

        return self.connection.execute("DELETE FROM users WHERE user_id in '?'", ([user_id]))

    def close(self):
        self.connection.close()
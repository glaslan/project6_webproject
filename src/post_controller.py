""" Module for managing posts """
from flask import jsonify
from uuid import uuid4

from DatabaseAccessLayer import Database
from constants import *



class PostController():
    """ Post controller class """

    def __init__(self, database: Database) -> None:
        """ Constructor for the PostController class """
        self.db = database
    
    def __del__(self) -> None:
        """ Destructor for the PostController class """
        self.db.close()
    
    def create_post(self, post: dict) -> bool:
        """ Creates a new post in the database """

        if self.db.insert_post(post):
            return True
        return False

    def get_posts(self) -> list[dict]:
        """ Returns a list of all posts in the database """

        # for each post insert the id into the json so the entire object is represented in a json 
        posts = self.db.get_all_posts()
        
        json_posts = []
        for id, post in posts:
            print(post)
            print(isinstance(post, str))
            print(id)
            new_post = post
            post[POST_ID] = id
            json_posts.append(post)
        return json_posts
    
    def get_post(self, date) -> dict:
        """ Returns a specific post from the database """

        id, post = self.db.get_post_by_date(date)
        post[POST_ID] = id
        return post

    
    def edit_post(self, old_post: dict, edited_post: dict, user_id) -> bool:
        """ Edits a specific post in the database """
        return self.db.update_post(old_post, edited_post, user_id)

    def delete_post(self, user_id: int, date: str) -> bool:
        """ Deletes a specific post from the database """
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
            
    def get_image(self):
        """
        TODO
        """
        # not sure how this ones gonna work yet

    def get_username(self, post: dict):

        return self.db.get_user_by_id(post.get(USER_ID)).get(USERNAME)
    
    def get_date(self, post: dict):
        """
        Purpose of this is to convert the date stored into the format
        that will be displyed on the ui
        TODO
        """
        
        # convert date to human readable format 

    def upload_image(self, image_data):
        """
        TODO
        """

        # get image content

        # change filename to post_id

        # save the image in the images folder 

db = Database("test.db")
pc = PostController(db)
pc.create_post({
    USER_ID: '1342',
    IMAGE_EXT: None,
    CONTENT: "im a post",
    POST_ID: 324354676576
})
pc.create_post({
    USER_ID: '678',
    IMAGE_EXT: None,
    CONTENT: "test",
    POST_ID: 2435453
})

print(db.get_all_posts())
""" Module for managing posts """

from src.DatabaseAccessLayer import Database

class PostController():
    """ Post controller class """

    def __init__(self, database_path) -> None:
        """ Constructor for the PostController class """
        self.db = Database("database_path")
    
    def __del__(self) -> None:
        """ Destructor for the PostController class """
        self.db.close()
    
    def create_post(self, post: dict) -> bool:
        """ Creates a new post in the database """

        if self.db.insert_post(post)
            return True
        return False

    def get_posts(self) -> list[dict]:
        """ Returns a list of all posts in the database """
        return self.db.get_all_posts()
    
    def get_post(self, post_id, date) -> dict:
        """ Returns a specific post from the database """
        return self.db.get_post(post_id)
    
    def edit_post(self, post_id: str, date, post_dict: dict) -> bool:
        """ Edits a specific post in the database """
        if self.db.delete_post(post_id):
            return self.db.insert_post(post_dict)

    def delete_post(self, post_id: str) -> bool:
        """ Deletes a specific post from the database """
        return self.db.delete_post(post_id)

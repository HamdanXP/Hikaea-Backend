import logging

from pymongo import MongoClient
from pymongo.database import Database, Collection


class MongoManager:
    client: MongoClient = None
    db: Database = None
    admin_lists: Collection = None
    blogs: Collection = None
    categories: Collection = None
    comments: Collection = None
    controls: Collection = None
    logs: Collection = None
    notifications: Collection = None
    reports: Collection = None
    shorts: Collection = None
    stories: Collection = None
    bookstats: Collection = None
    users: Collection = None

    def connect_to_database(self, path: str):
        logging.info("Connecting to MongoDB.")
        self.client = MongoClient(path)
        self.db = self.client['Hikaya']
        self.admin_lists = self.db['AdminLists']
        self.blogs = self.db['Blog']
        self.categories = self.db['Category']
        self.comments = self.db['Comments']
        self.controls = self.db['Control']
        self.logs = self.db['Log']
        self.notifications = self.db['Notification']
        self.reports = self.db['Report']
        self.shorts = self.db['Short']
        self.stories = self.db['Story']
        self.bookstats = self.db['BookStats']
        self.users = self.db['User']
        logging.info("Connected to MongoDB.")

    def close_database_connection(self):
        logging.info("Closing connection with MongoDB.")
        self.client.close()
        logging.info("Closed connection with MongoDB.")

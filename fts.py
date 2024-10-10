import sqlite3
import os
import hashlib
from config import Config

config = Config()


class FTS:
    def __init__(self, allowed_extensions=[".md"]):
        """docstring for fname"""
        self.current_dir = os.getcwd()
        self.set_db_path()
        self.load_database()
        self.allowed_extensions = allowed_extensions

    def set_db_path(self, extension="sqlite3"):
        # Hash the content to generate a unique filename
        hash_object = hashlib.sha256(self.current_dir.encode("utf-8"))
        hash_hex = hash_object.hexdigest()
        db_name = f"{hash_hex}.{extension}"
        self.db_path = config.data_home / db_name

    def load_database(self):
        """docstring for fname"""
        if not self.db_path.exists():
            self.create_database()
        else:
            self.db = sqlite3.connect(self.db_path)

    def create_database(self):
        """docstring for fname"""
        self.db = sqlite3.connect(self.db_path)
        self.db.execute(
            "CREATE VIRTUAL TABLE fts USING fts5(title, body, tokenize = 'porter')"
        )

    def walk_files(self):
        """docstring for fname"""
        all_files = []
        for root, dirs, files in os.walk(self.current_dir):
            for file in files:
                if file.endswith(tuple(self.allowed_extensions)):
                    all_files.append(os.path.join(root, file))
        return all_files

    def index_current_dir(self, title, body):
        """docstring for fname"""
        all_files = self.walk_files()
        for file in all_files:
            with open(file, "r") as f:
                body = f.read()
                self.db.execute(
                    "INSERT INTO fts(title, body) VALUES (?, ?)", (title, body)
                )

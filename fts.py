import sqlite3
import sys
from tqdm import tqdm
import os
import hashlib
from config import Config
from typing import Optional, List

config = Config()


class FTS:
    def __init__(
        self,
        allowed_extensions: Optional[List[str]] = None,
        current_dir: Optional[str] = None,
    ):
        """
        Initializes the full-text search class.

        Args:
            allowed_extensions (Optional[List[str]]): List of file extensions to include.
                Defaults to [".md"] if None is provided.
            current_dir (Optional[str]): The directory to index. Defaults to the current working directory.
        """
        if allowed_extensions is None:
            allowed_extensions = [".md"]
        self.allowed_extensions = allowed_extensions
        self.current_dir = current_dir or os.getcwd()
        self.set_db_path()
        self.load_database()

    def set_db_path(self, extension: str = "sqlite3") -> None:
        """
        Sets the path for the database file based on the current directory.

        Args:
            extension (str): The file extension for the database file. Defaults to 'sqlite3'.
        """
        # Hash the content to generate a unique filename
        hash_object = hashlib.sha256(self.current_dir.encode("utf-8"))
        hash_hex = hash_object.hexdigest()
        db_name = f"{hash_hex}.{extension}"
        self.db_path = (
            config.data_home / db_name
        )  # Assuming config.data_home is a Path object

    def load_database(self) -> None:
        """
        Loads the database if it exists; otherwise, creates a new one.
        """
        if not self.db_path.exists():
            self.create_database()
        else:
            self.db = sqlite3.connect(self.db_path)

    def create_database(self) -> None:
        """
        Creates a new FTS database with the required schema.
        """
        self.db = sqlite3.connect(self.db_path)
        self.db.execute(
            "CREATE VIRTUAL TABLE fts USING fts5(title, body, tokenize = 'porter')"
        )

    def walk_files(self, relative: bool = True) -> List[str]:
        """
        Walks through the current directory and collects all files with allowed extensions.

        Returns:
            List[str]: A list of file paths.
        """
        all_files = []
        print(f"Indexing {self.current_dir}...")
        for root, dirs, files in os.walk(self.current_dir):
            for filename in files:
                if filename.endswith(tuple(self.allowed_extensions)):
                    file_path = os.path.join(root, filename)
                    if relative:
                        file_path = os.path.relpath(file_path, self.current_dir)
                    all_files.append(file_path)
        return all_files

    def remove_database(self) -> None:
        """
        Removes the FTS database file.
        """
        if self.db_path.exists():
            os.remove(self.db_path)

    def index_current_dir(self) -> None:
        """
        Indexes all files in the current directory into the FTS database.
        """
        # TODO: check hash before indexing
        # TODO candidate for config file
        all_files = self.walk_files(relative=True)
        for i, filepath in tqdm(enumerate(all_files)):
            ext = filepath
            ext = os.path.splitext(ext)[-1]
            if ext in self.allowed_extensions:
                print(f"Indexing {filepath}")
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        body = f.read()
                        title = filepath
                        self.db.execute(
                            "INSERT INTO fts(title, body) VALUES (?, ?)", (title, body)
                        )
                except Exception as e:
                    # Log the error or handle it accordingly
                    print(f"Error indexing file {filepath}: {e}", file=sys.stderr)
        self.db.commit()

        # Test that the indexing was successful
        with self.db:
            cursor = self.db.execute("SELECT COUNT(*) FROM fts")
            count = cursor.fetchone()[0]
            print(f"Indexed {count} documents into {self.db_path}")

    def close(self) -> None:
        """
        Closes the database connection.
        """
        if self.db:
            self.db.close()

    def __enter__(self):
        """
        Allows use of the 'with' statement for the FTS class.
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Ensures the database connection is closed when exiting the 'with' block.
        """
        self.close()

    def search(self, query: str) -> List[tuple]:
        """
        Searches the FTS database for the given query.

        Args:
            query (str): The search query.

        Returns:
            List[tuple]: A list of tuples containing the title and body of matching documents.
        """

        def get_all_files() -> sqlite3.Cursor:
            return self.db.execute("SELECT title FROM fts")

        if query.strip() == "":
            # Return all documents if the query is empty
            cursor = get_all_files()
        else:
            try:
                cursor = self.db.execute(
                    "SELECT title FROM fts WHERE fts MATCH ?", (query,)
                )
            except sqlite3.OperationalError as e:
                # If the query is invalid, return all documents
                cursor = get_all_files()
                print(f"Invalid query: {e}", file=sys.stderr)
            except Exception as e:
                # Log the error or handle it accordingly
                print(f"Error searching for '{query}': {e}", file=sys.stderr)
                cursor = get_all_files()

        results = cursor.fetchall()
        # Get only the filenames
        return [filepath for filepath, in results]

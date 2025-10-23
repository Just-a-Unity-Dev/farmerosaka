import sqlite3
from datetime import datetime, timezone


class Database:
    database: sqlite3.Connection

    def __init__(self, path: str):
        self.database = sqlite3.connect(path)

    def setup(self):
        cursor = self.database.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS "command_action_logs" (
    "id"	INTEGER UNIQUE,
    "timestamp"	INTEGER NOT NULL,
    "author"	INTEGER NOT NULL,
    "action"	TEXT,
    "details"	TEXT,
    PRIMARY KEY("id" AUTOINCREMENT)
);""")
        cursor.execute("""CREATE TABLE IF NOT EXISTS "statuses" (
    "id"	INTEGER UNIQUE,
    "author"	INTEGER NOT NULL,
    "status"	TEXT,
    PRIMARY KEY("id" AUTOINCREMENT)
);""")
        self.database.commit()
        cursor.close()

    def add_log(self, author: int, action: str, details: str, cursor: sqlite3.Cursor = None):
        """
        Author should be a discord user ID, action should be a function name, and details can
        be whatever you want, preferably user-readable.
        """
        if cursor is None:
            cursor = self.database.cursor()

        query = "INSERT INTO command_action_logs VALUES (NULL, ?, ?, ?, ?)"
        cursor.execute(query, (datetime.now(timezone.utc).timestamp(), author, action, details,))
        self.database.commit()

        print("Log added!")

        cursor.close()

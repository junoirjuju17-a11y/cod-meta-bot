import sqlite3


class Database:

    def __init__(self):

        self.conn = sqlite3.connect("meta.db")

        self.cursor = self.conn.cursor()

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS weapons(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
        """)

        self.conn.commit()


    def exists(self, name):

        self.cursor.execute(
            "SELECT name FROM weapons WHERE name=?",
            (name,)
        )

        return self.cursor.fetchone() is not None


    def add(self, name):

        try:

            self.cursor.execute(
                "INSERT INTO weapons(name) VALUES(?)",
                (name,)
            )

            self.conn.commit()

        except:

            pass


    def all(self):

        self.cursor.execute(
            "SELECT name FROM weapons"
        )

        return self.cursor.fetchall()


    def clear(self):

        self.cursor.execute(
            "DELETE FROM weapons"
        )

        self.conn.commit()

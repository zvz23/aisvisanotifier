import sqlite3


class WebScraperDB:
    def __init__(self, db_name):
        self.db_name = db_name
        self.table = 'dates'
        self.conn = None
        self.cursor = None

    def __enter__(self):
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn:
            self.conn.commit()
            self.conn.close()
    
    def init_db(self):
        self.cursor.execute(f"""
            CREATE TABLE {self.table} (
            ID   INTEGER NOT NULL
                        PRIMARY KEY AUTOINCREMENT,
            DATE  TEXT    NOT NULL
                        UNIQUE,
            IS_SENT  INTEGER
        );
    """)
        self.conn.commit()
        print("Database initialized")

    def get_all(self):
        self.cursor.execute(f"SELECT * FROM {self.table}")
        return self.cursor.fetchall()

    def get_all_not_sent(self):
        self.cursor.execute(f"SELECT DATE FROM {self.table} WHERE IS_SENT IS NULL")
        return [r[0] for r in self.cursor.fetchall()]

    def save_date(self, date: str):
        self.cursor.execute(f"INSERT OR IGNORE INTO {self.table}(DATE) VALUES(?)", [date])

    def save_dates(self, dates: list):
        self.cursor.executemany(f"INSERT OR IGNORE INTO {self.table}(DATE) VALUES(?)", dates)

    def set_sent(self, date: str):
        self.cursor.execute(f"UPDATE {self.table} SET IS_SENT=1 WHERE DATE=?", [date])
    
    def set_sent_many(self, dates: list):
        self.cursor.executemany(f"UPDATE {self.table} SET IS_SENT=1 WHERE DATE=?", dates)
    
    def set_sent_all(self):
        self.cursor.execute(f"UPDATE {self.table} SET IS_SENT=1")


    def unsent_all(self):
        self.cursor.execute(f"UPDATE {self.table} SET IS_SENT=NULL")


if __name__ == '__main__':
    with WebScraperDB('visa.db') as conn:
        conn.init_db()
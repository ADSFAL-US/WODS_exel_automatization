#pylint:disable=//github.com/pylint-dev/pylint/pull/3578.
import sqlite3
import random

class DatabaseHandler:
    def __init__(self, db_name='my_database.db'):
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self.create_table()
        
    def create_new_user(self):
        """Создает нового пользователя с дефолтными значениями"""
        self.cursor.execute('''
            INSERT INTO Users 
            (username, urank, kills, deads, kills_deads, to_main)
            VALUES(?, ?, ?, ?, ?, ?)
        ''', (
            "Новый", 
            "-", 
            0, 
            0, 
            0.0, 
            False
        ))
        self.connection.commit()
        return self.cursor.lastrowid

    def create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                urank TEXT NOT NULL,
                kills INTEGER NOT NULL,
                deads INTEGER NOT NULL,
                kills_deads REAL NOT NULL,
                to_main BLOB NOT NULL
            )
        ''')
        self.connection.commit()

    def insert_example_data(self, count=1):
        example_ranks = ["новобранец","-","-","боец","офицер","-","глава"]
        for _ in range(count):
            example_k = random.randint(1, 1000)
            example_d = random.randint(1, 1000)
            kd = example_k / example_d
            to_main = kd > 0.5
            
            self.cursor.execute('''
                INSERT INTO Users 
                (username, urank, kills, deads, kills_deads, to_main)
                VALUES(?, ?, ?, ?, ?, ?)
            ''', (
                'example',
                random.choice(example_ranks),
                example_k,
                example_d,
                kd,
                to_main
            ))
        self.connection.commit()

    def fetch_all_users(self):
        return self.cursor.execute('''
            SELECT id, username, urank, kills, deads, kills_deads, to_main 
            FROM Users
        ''').fetchall()

    def update_user(self, user_data):
        self.cursor.execute('''
            UPDATE Users 
            SET username=?, urank=?, kills=?, deads=?, kills_deads=?, to_main=?
            WHERE id=?
        ''', user_data)
        self.connection.commit()

    def close(self):
        self.connection.close()
        

    def delete_user(self, user_id):
        """Удаляет пользователя по ID"""
        self.cursor.execute('DELETE FROM Users WHERE id=?', (user_id,))
        self.connection.commit()
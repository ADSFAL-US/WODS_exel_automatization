import sqlite3
import random
from typing import List, Tuple, Optional
import os

class DatabaseHandler:
    """Обработчик работы с базой данных SQLite"""

    CREATE_TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            urank TEXT NOT NULL,
            kills INTEGER NOT NULL,
            deads INTEGER NOT NULL,
            kills_deads REAL NOT NULL,
            to_main BLOB NOT NULL,
            ocr_nickname TEXT
        )
    """

    INSERT_USER_SQL = """
        INSERT INTO Users 
        (username, urank, kills, deads, kills_deads, to_main)
        VALUES(?, ?, ?, ?, ?, ?)
    """

    def __init__(self, db_name: str = 'my_database.db') -> None:
        
        os.makedirs(os.path.dirname(db_name), exist_ok=True)
        self.connection = sqlite3.connect(db_name)
        self.cursor = self.connection.cursor()
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Инициализация структуры базы данных"""
        try:
            self.cursor.execute(self.CREATE_TABLE_SQL)
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"Ошибка при создании таблицы: {e}")

    #region CRUD Operations
    def create_new_user(self) -> int:
        """Создает нового пользователя с дефолтными значениями"""
        default_data = ("Новый", "-", 0, 0, 0.0, False)
        try:
            self.cursor.execute(self.INSERT_USER_SQL, default_data)
            self.connection.commit()
            return self.cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Ошибка при создании пользователя: {e}")
            return -1

    def fetch_all_users(self) -> List[Tuple]:
        """Возвращает всех пользователей из базы"""
        try:
            return self.cursor.execute('''
                SELECT id, username, urank, kills, deads, kills_deads, to_main 
                FROM Users
            ''').fetchall()
        except sqlite3.Error as e:
            print(f"Ошибка при получении данных: {e}")
            return []

    def update_user(self, user_data: Tuple) -> None:
        """Обновляет данные пользователя"""
        try:
            self.cursor.execute('''
                UPDATE Users 
                SET username=?, urank=?, kills=?, deads=?, kills_deads=?, to_main=?
                WHERE id=?
            ''', user_data)
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"Ошибка при обновлении пользователя: {e}")

    def delete_user(self, user_id: int) -> None:
        """Удаляет пользователя по ID"""
        try:
            self.cursor.execute('DELETE FROM Users WHERE id=?', (user_id,))
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"Ошибка при удалении пользователя: {e}")
    #endregion

    #region Additional Methods
    def insert_example_data(self, count: int = 1) -> None:
        """Генерация тестовых данных"""
        example_ranks = ["новобранец", "-", "-", "боец", "офицер", "-", "глава"]
        
        for _ in range(count):
            example_k = random.randint(1, 1000)
            example_d = random.randint(1, 1000)
            kd = float(example_k) / float(example_d)
            to_main = bool(kd > 0.75)
            
            try:
                self.cursor.execute(self.INSERT_USER_SQL, (
                    'example',
                    random.choice(example_ranks),
                    example_k,
                    example_d,
                    kd,
                    to_main
                ))
            except sqlite3.Error as e:
                print(f"Ошибка при вставке тестовых данных: {e}")
        
        self.connection.commit()

    def find_user_by_name_or_ocr(self, name: str) -> Optional[Tuple]:
        """Поиск пользователя по имени или OCR-никнейму"""
        try:
            return self.cursor.execute('''
                SELECT * FROM Users 
                WHERE username = ? OR ocr_nickname = ?
            ''', (name, name)).fetchone()
        except sqlite3.Error as e:
            print(f"Ошибка при поиске пользователя: {e}")
            return None

    def update_user_stats(self, user_id: int, kills: int, deaths: int) -> None:
        """Обновление статистики пользователя с пересчетом K/D"""
        try:
            # Получаем текущие значения
            current = self.cursor.execute(
                "SELECT kills, deads FROM Users WHERE id=?", (user_id,)
            ).fetchone()
            
            new_kills = current[0] + kills
            new_deaths = current[1] + deaths
            new_kd = new_kills / new_deaths if new_deaths != 0 else 0.0
            
            self.cursor.execute('''
                UPDATE Users 
                SET kills = ?, 
                    deads = ?,
                    kills_deads = ?
                WHERE id = ?
            ''', (new_kills, new_deaths, new_kd, user_id))
            
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"Ошибка при обновлении статистики: {e}")

    def close(self):
        """Закрытие соединения с базой"""
        try:
            self.cursor.close()
            self.connection.close()
        except Exception as e:
            print(f"Ошибка закрытия соединения: {str(e)}")

    def __del__(self) -> None:
        """Деструктор для автоматического закрытия соединения"""
        self.close()
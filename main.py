# main.py
import tkinter as tk
from database import DatabaseHandler
from gui import ApplicationGUI


def initialize_database() -> DatabaseHandler:
    """Инициализация подключения к базе данных и структуры"""
    db = DatabaseHandler()
    # db.insert_example_data(1)  # Раскомментировать для тестовых данных
    return db


def main() -> None:
    """Точка входа в приложение"""
    try:
        db = initialize_database()
        root = tk.Tk()
        app = ApplicationGUI(root, db)
        root.mainloop()
    except Exception as e:
        print(f"Critical error: {str(e)}")
    finally:
        if 'db' in locals():
            db.close()


if __name__ == "__main__":
    main()
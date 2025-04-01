#pylint:disable=//github.com/pylint-dev/pylint/pull/3578.
from database import DatabaseHandler
from gui import ApplicationGUI
import tkinter as tk

def main():
    # Инициализация базы данных
    db = DatabaseHandler()
    #db.insert_example_data(1)  # Добавляем один пример
    
    # Создание GUI
    root = tk.Tk()
    app = ApplicationGUI(root, db)
    root.mainloop()
    
    # Закрытие соединения с БД при выходе
    db.close()

if __name__ == "__main__":
    main()
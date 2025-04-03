#pylint:disable=//github.com/pylint-dev/pylint/pull/3578.
from database import DatabaseHandler
from gui import ApplicationGUI
import tkinter as tk

def main():
    print("for use OCR install tesseract programm. https://github.com/tesseract-ocr/tesseract/releases/download/5.5.0/tesseract-ocr-w64-setup-5.5.0.20241111.exe")
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
# start_window.py
import os
import tkinter as tk
from tkinter import ttk, messagebox
from database import DatabaseHandler
from gui import ApplicationGUI

class CreateDatabaseDialog(tk.Toplevel):
    """Диалог создания новой базы данных"""
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Создать базу данных")
        self.geometry("300x120")
        self.resizable(False, False)
        
        self.db_name = tk.StringVar()
        
        self._setup_ui()
        self.grab_set()
    
    def _setup_ui(self):
        tk.Label(self, text="""Название базы данных без ".db":""", bg = "#383838", fg = "#ffffff").pack(pady=5)
        entry = tk.Entry(self, textvariable=self.db_name, bg = "#383838", fg = "#ffffff")
        entry.pack(pady=5)
        entry.bind("<Return>", lambda e: self._create_db())
        
        btn_frame = tk.Frame(self, background="#383838")
        btn_frame.pack(pady=5)
        
        self.configure(bg="#383838")
        self.parent.configure(bg="#383838")
        tk.Button(btn_frame, text="Создать", command=self._create_db, fg="#ffffff", bg="#11f018").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Отмена", command=self.destroy, fg="#ffffff", bg="#f01111").pack(side=tk.RIGHT, padx=5)
    
    def _create_db(self):
        name = self.db_name.get().strip()
        if not name:
            messagebox.showerror("Ошибка", "Введите название базы данных")
            return
        
        if not name.endswith('.db'):
            name += '.db'
        
        db_path = os.path.join("data", name)
        try:
            if not os.path.exists("data"):
                os.makedirs("data")
            
            if os.path.exists(db_path):
                messagebox.showerror("Ошибка", "База с таким именем уже существует")
                return
            
            # Создаем пустую базу
            DatabaseHandler(db_path).close()
            self.parent.refresh_table_list()
            self.parent.open_database(db_path)
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

class StartWindow(tk.Tk):
    """Стартовое окно приложения"""
    def __init__(self):
        super().__init__()
        self.title("Менеджер таблиц")
        self.geometry("600x400")
        self._setup_ui()
        self.refresh_table_list()
        self.current_app_window = None
        self.app_window = None
        self._init_style()
    
    def _init_style(self):
        style = ttk.Style()
        style.theme_use('default')
        
        style.configure(
            "Custom.Treeview",
            background="#383838",  # Цвет фона
            fieldbackground="#383838",  # Цфон области данных
            foreground="white"  # Цвет текста
        )

        # Настраиваем цвета для выделенных элементов
        style.map(
            "Custom.Treeview",
            background=[('selected', '#606060')],
            foreground=[('selected', 'white')]
        )
    
    def _setup_ui(self):
        # Фрейм для списка таблиц
        list_frame = tk.Frame(self, width=200, background="#383838")
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)
        
        self.table_list = ttk.Treeview(list_frame, show="tree", selectmode="browse", style="Custom.Treeview")
        self.table_list.pack(fill=tk.BOTH, expand=True)
        self.table_list.bind("<Double-1>", self._on_table_selected)
        
        # Центральная кнопка
        self.configure(bg = "#383838")
        center_frame = tk.Frame(self, bg = "#383838")
        center_frame.pack(expand=True, fill=tk.BOTH)
        
        self.create_btn = tk.Button(
            center_frame,
            text="+ Создать таблицу",
            command=self.show_create_dialog,
            font=("Arial", 14, "bold"),
            bg="#11f018",
            fg = "#ffffff"
        )
        self.create_btn.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
    
    def refresh_table_list(self):
        """Обновление списка доступных таблиц"""
        self.table_list.delete(*self.table_list.get_children())
        if not os.path.exists("data"):
            return
        
        for fname in sorted(os.listdir("data")):
            if fname.endswith(".db"):
                self.table_list.insert("", "end", text=fname, values=os.path.join("data/", fname))
    
    def _on_table_selected(self, event):
        """Обработчик выбора таблицы"""
        selected = self.table_list.selection()
        if not selected:
            return
        
        db_path = self.table_list.item(selected[0], "values")[0]
        self.open_database(db_path)
    
    def show_create_dialog(self):
        """Показать диалог создания базы"""
        CreateDatabaseDialog(self)
    
    def open_database(self, db_path: str):
        try:
            if self.current_app_window:
                self.current_app_window.close_database()
                
            self.withdraw()  # Скрываем стартовое окно
            
            # Создаем новое окно приложения
            self.current_app_window = ApplicationWindow(self, db_path)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть базу:\n{str(e)}")
            self.deiconify()
            
    def show_self(self):
        """Показать стартовое окно после закрытия приложения"""
        self.deiconify()
        self.refresh_table_list()
            
    def on_main_close(self):
        """Обработчик закрытия главного окна"""
        if self.current_app_window:
            self.current_app_window.close_database()
        self.destroy()
        
        
class ApplicationWindow(tk.Toplevel):
    """Окно работы с базой данных"""
    def __init__(self, parent, db_path):
        super().__init__(parent)
        self.parent = parent
        self.db_path = db_path
        self.db = DatabaseHandler(db_path)
        self.app_gui = ApplicationGUI(self, self.db)
        self.protocol("WM_DELETE_WINDOW", self.close_database)

    def close_database(self):
        """Корректное закрытие базы данных"""
        try:
            self.db.close()
            self.destroy()
            self.parent.show_self()  # Показываем стартовое окно
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
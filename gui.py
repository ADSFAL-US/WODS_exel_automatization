# gui.py
import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Dict, List, Tuple, Any
from myOCR_test import OCRApp, CropWindow
from database import DatabaseHandler

class ThemeManager:
    """Управление стилями интерфейса"""
    DARK_THEME = {
        "bg": "#2e2e2e",
        "fg": "#ffffff",
        "entry_bg": "#404040",
        "button_bg": "#3e3e3e",
        "button_active_bg": "#5e5e5e",
        "header_bg": "#1e1e1e",
        "scrollbar_bg": "#3e3e3e",
        "error_red": "#5e2e2e",
        "success_green": "#2e5e2e",
        "error_fg": "#ff6666",
        "header_fg": "#000000",  # Белый текст заголовков
        "readonly_fg": "#a0a0a0"
    }
    
    @classmethod
    def apply_theme(cls, widget: tk.Widget, element_type: str) -> None:
        colors = cls.DARK_THEME
        if isinstance(widget, tk.Button):
            widget.config(
                bg=colors["button_bg"],
                fg=colors["fg"],
                activebackground=colors["button_active_bg"]
            )
        elif isinstance(widget, tk.Entry):
            widget.config(
                bg=colors["entry_bg"],
                fg=colors["fg"],
                insertbackground=colors["fg"]
            )
            if widget['state'] == 'readonly':
                widget.config(
                fg=cls.DARK_THEME["readonly_fg"],
                disabledbackground=cls.DARK_THEME["entry_bg"]
            )
        if element_type == "header":
            widget.config(
                bg=cls.DARK_THEME["header_bg"],
                fg=cls.DARK_THEME["header_fg"],  # Цвет текста
                state="readonly"
            )
        elif isinstance(widget, tk.Entry) and widget["state"] == "readonly":
            widget.config(
                fg=cls.DARK_THEME["readonly_fg"],  # Серый текст
                disabledbackground=cls.DARK_THEME["entry_bg"]
            )

class TableWidget(tk.Frame):
    """Кастомизированный виджет таблицы"""
    
    def __init__(self, master, db_handler: DatabaseHandler):
        super().__init__(master)
        self.db = db_handler
        self.columns = ('ID', 'Username', 'Rank', 'Kills', 'Deads', 'K/D', 'To Main', 'Actions')  # Добавлено явное определение
        self.column_widths = [50, 150, 100, 80, 80, 80, 80, 80]
        self._setup_table()

    def _setup_table(self) -> None:
        """Инициализация компонентов таблицы"""
        self.canvas = tk.Canvas(self, bg=ThemeManager.DARK_THEME["bg"])
        scroll_x = tk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
        scroll_y = tk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        
        self.table_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.table_frame, anchor="nw")
        
        # Конфигурация прокрутки
        self.canvas.configure(
            xscrollcommand=scroll_x.set,
            yscrollcommand=scroll_y.set
        )
        
        # Упаковка элементов
        scroll_x.pack(side="bottom", fill="x")
        scroll_y.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        self.table_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self._create_headers()
        self.refresh()

    def _create_headers(self) -> None:
        """Создание заголовков с правильными стилями"""
        for col, (name, width) in enumerate(zip(self.columns, self.column_widths)):
            header = tk.Entry(
                self.table_frame,
                width=width//10,
                relief="groove",
                font=('Arial', 10, 'bold')
            )
            header.config(
                bg=ThemeManager.DARK_THEME["header_bg"],
                fg=ThemeManager.DARK_THEME["header_fg"],
                state="readonly"
            )
            header.grid(row=0, column=col, sticky="nsew", pady=1)
            header.insert("end", name)


    def refresh(self) -> None:
        """Пересоздание таблицы с очисткой виджетов"""
        for widget in self.table_frame.winfo_children():
            widget.destroy()  # Полная очистка перед обновлением
        self._create_headers()
        self._load_data()

    def _create_row(self, row_idx: int, user_data: Tuple, user_idx: int) -> None:
        entries = []
        user_id = user_data[0]  # Реальный ID из базы данных
        self._add_delete_button(row_idx, user_id)
        # Сохраняем оригинальный ID вместо индекса строки
        user_data = list(user_data)
        
        for col in range(7):
            entry = tk.Entry(self.table_frame, width=self.column_widths[col]//10)
            ThemeManager.apply_theme(entry, "entry")
            entry.grid(row=row_idx, column=col, sticky="nsew", padx=1, pady=1)
            
            value = self._format_value(col, user_data[col])
            entry.insert("end", value)
            
            # Привязка к обновлению данных
            if col in (3, 4):  # Поля, которые можно редактировать
                entry.bind("<KeyRelease>", lambda e, r=row_idx: self._update_kd(r))
                
            if col in (5, 6):  # Поля K/D и To Main (только для чтения)
                entry.config(state="readonly", fg="#103ae3")
                
            
                
                
        # Добавляем скрытый ID в последнюю колонку
        #tk.Label(self.table_frame, text=str(user_id)).grid(row=row_idx, column=8)
        
    
    def _save_row_changes(self, row_idx: int) -> None:
        """Сохраняет изменения строки в БД"""
        try:
            # Получаем ID из скрытой колонки
            user_id = int(self.table_frame.grid_slaves(row=row_idx, column=8)[0].cget("text"))
            
            # Собираем данные из полей ввода
            data = [
                self.table_frame.grid_slaves(row=row_idx, column=col)[0].get()
                for col in range(7)
            ]
            
            # Конвертация и валидация
            db_data = (
                data[1],  # username
                data[2],  # urank
                int(data[3]),  # kills
                int(data[4]),  # deads
                float(data[5]),  # kills_deads
                data[6] == "+",  # to_main
                user_id  # id
            )
            
            self.db.update_user(db_data)
            
        except Exception as e:
            print(f"Ошибка сохранения строки {row_idx}: {str(e)}")
        
    
    def _update_kd(self, row_idx: int) -> None:
        """Исправленный расчет K/D"""
        try:
            # Получаем элементы через grid_slaves
            kills_entry = self.table_frame.grid_slaves(row=row_idx, column=3)[0]
            deads_entry = self.table_frame.grid_slaves(row=row_idx, column=4)[0]
            
            kills = int(kills_entry.get())
            deads = int(deads_entry.get())
            
            kd = kills / deads if deads != 0 else 0.0
            kd_entry = self.table_frame.grid_slaves(row=row_idx, column=5)[0]
            
            kd_entry.config(state="normal")
            kd_entry.delete(0, "end")
            kd_entry.insert(0, f"{kd:.2f}")
            kd_entry.config(
                state="readonly",
                fg=ThemeManager.DARK_THEME["readonly_fg"]  # Явное указание цвета
            )
        except (IndexError, ValueError, ZeroDivisionError):
            pass

    def _format_value(self, col: int, value: Any) -> str:
        """Форматирование значений для отображения"""
        if col == 5:  # K/D
            return f"{float(value):.2f}"
        if col == 6:  # To Main
            return "+" if value else "-"
        return str(value)

    def _add_delete_button(self, row: int, user_id: int) -> None:
        """Исправленная кнопка удаления с фиксацией ID"""
        btn = tk.Button(
            self.table_frame,
            text="-",
            font=('Arial', 12, 'bold'),
            command=lambda uid=user_id: self._delete_user(uid)  # Фиксация ID в лямбде
        )
        ThemeManager.apply_theme(btn, "button")
        btn.grid(row=row, column=7, sticky="nsew", padx=2, pady=1)

    def _delete_user(self, user_id: int) -> None:
        """Удаление с подтверждением и принудительным обновлением"""
        if messagebox.askyesno("Подтверждение", "Удалить игрока?", parent=self):
            try:
                self.db.delete_user(user_id)
                self.refresh()  # Явное обновление таблицы
                print(f"Удален пользователь с ID: {user_id}")  # Отладочный вывод
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить: {str(e)}")
                
    def _load_data(self) -> None:
        """Загрузка данных из БД"""
        data = self.db.fetch_all_users()
        for row_idx, user in enumerate(data, start=1):
            user_list = list(user)
            user_idx = row_idx
            self._create_row(row_idx, tuple(user_list), user_idx)

class OCRDialogHandler:
    """Обработчик диалогов OCR"""
    
    @staticmethod
    @staticmethod
    def process_ocr_image(parent: tk.Tk, db_handler: DatabaseHandler) -> None:
        file_path = filedialog.askopenfilename(filetypes=[("Изображения", "*.png *.jpg *.jpeg")])
        if not file_path:
            return
            
        try:
            crop_win = CropWindow(parent, file_path)
            parent.wait_window(crop_win)
            
            if crop_win.ocr_data:
                OCRDialogHandler._update_database(db_handler, crop_win.ocr_data)
                db_handler._gui_table.refresh()

        except Exception as e:
            messagebox.showerror("Ошибка OCR", str(e))
            
    @staticmethod
    def _process_and_show_results(parent: tk.Tk, db: DatabaseHandler, path: str) -> None:
        """Обработка и отображение результатов"""
        processing_win = tk.Toplevel(parent)
        processing_win.grab_set()
        tk.Label(processing_win, text="Обработка...").pack(pady=20)
        processing_win.after(100, lambda: OCRDialogHandler._finalize_processing(processing_win, db, path))
        
        
    
    @staticmethod
    def _finalize_processing(win: tk.Toplevel, db: DatabaseHandler, path: str) -> None:
        """Финализация обработки OCR"""
        try:
            ocr_app = OCRApp(win, path)
            if ocr_app.processed_data:
                OCRDialogHandler._update_database(db, ocr_app.processed_data)
        finally:
            win.destroy()

    @staticmethod
    def _update_database(db: DatabaseHandler, data: List[Dict]) -> None:
        """Обновление базы данных с проверкой структуры"""
        if not data:
            messagebox.showwarning("Пустые данные", "Нет данных для сохранения")
            return

        for player in data:
            # Проверка обязательных полей
            if 'name' not in player or 'kills' not in player or 'deaths' not in player:
                print(f"Invalid player data: {player}")
                continue
                
            # Остальная логика обновления
            existing = db.find_user_by_name_or_ocr(player['name'])
            if existing:
                db.update_user_stats(existing[0], player['kills'], player['deaths'])
            else:
                kills = player.get('kills', 0)
                deaths = player.get('deaths', 0)
                kills_deads = kills / deaths if deaths != 0 else 0.0
                if kills_deads >= 0.75:
                    to_main = 1
                else:
                    to_main = 0

                db.cursor.execute(
                    'INSERT INTO Users (username, urank, kills, deads, kills_deads, to_main) VALUES (?, ?, ?, ?, ?, ?)',
                    (player['name'], '-', kills, deaths, kills_deads, to_main)
                )
        db.connection.commit()

class ApplicationGUI:
    """Главное окно приложения"""
    
    def __init__(self, root: tk.Tk, db_handler: DatabaseHandler):
        self.root = root
        self.db = db_handler
        self.db._gui_table = None
        
        self._setup_window()
        self._create_widgets()
        
        self.db._gui_table = self.table
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def on_close(self):
        """Обработчик закрытия окна"""
        self.db.close()
        self.root.destroy()

    def _setup_window(self) -> None:
        self.root.title("Player Statistics Manager")
        self.root.geometry("1280x800")
        ThemeManager.apply_theme(self.root, "root")

    def _create_widgets(self) -> None:
        """Создание интерфейса"""
        self._create_control_panel()
        self.table = TableWidget(self.root, self.db)
        self.table.pack(fill="both", expand=True)

    def _create_control_panel(self) -> None:
        """Панель управления"""
        control_frame = tk.Frame(self.root)
        ThemeManager.apply_theme(control_frame, "frame")
        control_frame.pack(fill="x", pady=5)
        
        buttons = [
            ("+ Добавить", "#2e5e2e", self._add_user),
            ("OCR Загрузка", "#5e2e2e", lambda: OCRDialogHandler.process_ocr_image(self.root, self.db)),
            ("Сохранить", "#5e2e2e", self._commit_changes)
        ]
        
        for text, color, command in buttons:
            btn = tk.Button(control_frame, text=text, bg=color, command=command)
            ThemeManager.apply_theme(btn, "button")
            btn.pack(side="left", padx=10)

    def _add_user(self) -> None:
        """Добавление нового пользователя"""
        self.db.create_new_user()
        self.table.refresh()

    def _commit_changes(self) -> None:
        """Корректное сохранение данных с игнорированием кнопок"""
        try:
            rows = self.table.table_frame.grid_size()[1]
            
            for row_idx in range(1, rows):
                row_data = []
                for col in range(len(self.table.columns) - 1):  # Исключаем столбец Actions
                    widgets = self.table.table_frame.grid_slaves(row=row_idx, column=col)
                    if widgets and isinstance(widgets[0], tk.Entry):
                        value = widgets[0].get()
                        row_data.append(value)
                    else:
                        row_data.append("0")  # Значение по умолчанию
                
                # Проверка наличия всех необходимых данных
                if len(row_data) < 7:
                    print(f"Ошибка: Недостаточно данных в строке {row_idx}")
                    continue
                
                try:
                    # Формирование данных в порядке, ожидаемом методом update_user
                    db_data = (
                        row_data[1],  # username
                        row_data[2],  # urank
                        int(row_data[3]),  # kills
                        int(row_data[4]),  # deads
                        float(row_data[5]),  # kills_deads
                        row_data[6] == "+",  # to_main (преобразование в bool)
                        int(row_data[0])      # id (должен быть последним для WHERE)
                    )
                    self.db.update_user(db_data)
                except (ValueError, IndexError) as e:
                    print(f"Ошибка конвертации данных в строке {row_idx}: {str(e)}")
                    continue
            
            messagebox.showinfo("Успех", "Данные сохранены")
            self.table.refresh()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка сохранения: {str(e)}")
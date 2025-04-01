#pylint:disable=//github.com/pylint-dev/pylint/pull/3578.
import tkinter as tk
from tkinter import messagebox

class ApplicationGUI:
    DARK_THEME = {
        "bg": "#2e2e2e",
        "fg": "#ffffff",
        "entry_bg": "#404040",
        "button_bg": "#3e3e3e",
        "button_active_bg": "#5e5e5e",
        "header_bg": "#1e1e1e",
        "scrollbar_bg": "#3e3e3e",
        "error_bg": "#5e1e1e",
        "success_green": "#2e5e2e",
        "error_red": "#5e2e2e"
    }

    def __init__(self, root, db_handler):
        self.column_widths = [50, 150, 100, 80, 80, 80, 80, 80]  # Добавить эту строку
        self.root = root
        self.db = db_handler
        self.entries = []
        self.setup_ui()
        
        

    # Модифицируем следующие методы:

    def create_scrollable_area(self):
        self.main_frame = tk.Frame(self.root, bg=self.DARK_THEME["bg"])
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Создаем прокрутки первыми
        self.x_scrollbar = tk.Scrollbar(
            self.main_frame,
            orient="horizontal",
            bg=self.DARK_THEME["scrollbar_bg"],
            troughcolor=self.DARK_THEME["bg"]
        )
        self.y_scrollbar = tk.Scrollbar(
            self.main_frame,
            orient="vertical",
            bg=self.DARK_THEME["scrollbar_bg"],
            troughcolor=self.DARK_THEME["bg"]
        )

        # Холст с привязкой к прокруткам
        self.canvas = tk.Canvas(
            self.main_frame,
            bg=self.DARK_THEME["bg"],
            highlightthickness=0,
            yscrollcommand=self.y_scrollbar.set,
            xscrollcommand=self.x_scrollbar.set
        )

        # Настройка прокруток
        self.x_scrollbar.config(command=self.canvas.xview)
        self.y_scrollbar.config(command=self.canvas.yview)

        # Упаковка элементов
        self.y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Фрейм для таблицы ВНУТРИ холста
        self.table_frame = tk.Frame(self.canvas, bg=self.DARK_THEME["bg"])
        self.canvas.create_window((0, 0), window=self.table_frame, anchor="nw")

        # Критически важный бинд!
        self.table_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
    
    def create_table(self):
        columns = ['ID', 'Username', 'Rank', 'Kills', 'Deads', 'K/D', 'To Main', 'Actions']
        column_widths = [50, 150, 100, 80, 80, 80, 80, 80]
    
        # 1. Очистка предыдущих данных (если есть)
        for widget in self.table_frame.winfo_children():
            widget.destroy()
    
        # 2. Настройка колонок
        for col in range(8):
            self.table_frame.grid_columnconfigure(
                col, 
                minsize=column_widths[col], 
                weight=1 if col not in [0,7] else 0
            )
    
        # 3. Заголовки
        for col, name in enumerate(columns):
            header = tk.Entry(
                self.table_frame,
                width=column_widths[col]//10,
                relief=tk.GROOVE,
                font=('Arial', 10, 'bold'),
                bg=self.DARK_THEME["header_bg"],
                fg=self.DARK_THEME["fg"],
                readonlybackground=self.DARK_THEME["header_bg"]
            )
            header.grid(row=0, column=col, sticky="nsew", pady=1)  # Добавлен pady
            header.insert(tk.END, name)
            header.config(state='readonly')
    
        # 4. Данные таблицы
        data = self.db.fetch_all_users()
        print(f"Загружено записей: {len(data)}")  # Отладочный вывод
    
        for row_idx, user in enumerate(data, start=1):
            self.create_table_row(row_idx, user)
            self.table_frame.grid_rowconfigure(row_idx, weight=1)  # Важная строка!
    
        # 5. Принудительное обновление
        self.table_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def create_table_row(self, row_idx, user_data):
        row_entries = []
        print(f"Данные строки {row_idx}: {user_data}")  # Отладочный вывод
        
        for col in range(7):
            e = tk.Entry(
                self.table_frame,
                width=self.column_widths[col]//10,
                relief=tk.GROOVE,
                bg=self.DARK_THEME["entry_bg"],
                fg=self.DARK_THEME["fg"],
                insertbackground=self.DARK_THEME["fg"]
            )
            e.grid(row=row_idx, column=col, sticky="nsew", padx=1, pady=1)
            
            value = user_data[col]  # Индексы 0-6: id, username, ..., to_main
            
            if col == 5:  # K/D
                e.insert(tk.END, f"{float(value):.2f}")
                e.config(state='readonly')
            elif col == 6:  # To Main (булево значение)
                display_value = "+" if bool(value) else "-"
                e.insert(tk.END, display_value)
                e.config(state='readonly')
            else:
                e.insert(tk.END, str(value))
                if col in [3, 4]:  # Kills/Deads
                    e.bind("<KeyRelease>", lambda event, r=row_idx: self.update_row_data(r))

            row_entries.append(e)

        # Кнопка удаления (исправленная команда)
        delete_btn = tk.Button(
            self.table_frame,
            text="-",
            font=('Arial', 12, 'bold'),
            bg=self.DARK_THEME["error_red"],
            fg=self.DARK_THEME["fg"],
            activebackground="#7e3e3e",
            command=lambda uid=user_data[0]: self.delete_user_warning(uid)  # user_data[0] = id
        )
        delete_btn.grid(row=row_idx, column=7, sticky="nsew", padx=2, pady=1)
        row_entries.append(delete_btn)
        
        self.entries.append(row_entries)

    def refresh_table(self):
        """Обновление данных из БД"""
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        self.entries = []
        self.create_table()
        self.canvas.yview_moveto(0)
       

    # В метод setup_ui добавляем:
    def setup_ui(self):
        self.root.configure(bg=self.DARK_THEME["bg"])
        self.root.geometry("1280x800")
    
        # Сначала создаем scrollable area
        self.create_scrollable_area()
    
        # Затем создаем остальные элементы
        self.create_buttons_frame()
        self.create_table()
        self.create_commit_button()

    def create_buttons_frame(self):
        self.buttons_frame = tk.Frame(self.root, bg=self.DARK_THEME["bg"])
        self.buttons_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        self.add_btn = tk.Button(
            self.buttons_frame,
            text="+ Добавить нового пользователя",
            font=('Arial', 12, 'bold'),
            bg=self.DARK_THEME["success_green"],
            fg=self.DARK_THEME["fg"],
            activebackground="#1e3e1e",
            relief=tk.FLAT,
            command=self.add_new_user
        )
        self.add_btn.pack(side=tk.LEFT, padx=10)

    def create_commit_button(self):
        commit_btn = tk.Button(
            self.buttons_frame,
            text="💾|COMMIT|💾", 
            bg=self.DARK_THEME["error_red"],
            activebackground="#3e2e2e",
            fg=self.DARK_THEME["fg"],
            command=self.commit_changes
        )
        commit_btn.pack(side=tk.LEFT, padx=10)

    # Остальные методы остаются без изменений (как в оригинале), кроме handle_update_error:
    def handle_update_error(self, row):
        for col in [5, 6]:
            self.entries[row][col].config(
                bg=self.DARK_THEME["error_bg"],
                fg="#ff6666",
                state='normal'
            )
            self.entries[row][col].delete(0, tk.END)
            self.entries[row][col].insert(0, "Error")
            self.entries[row][col].config(state='readonly')

    # Остальные методы (delete_user_warning, add_new_user, refresh_table, update_row_data, commit_changes) 
    # остаются без изменений, как в исходном файле
    

    def delete_user_warning(self, user_id):
        if messagebox.askyesno(
            "Подтверждение удаления",
            "Вы точно хотите удалить этого игрока?",
            icon='warning'
        ):
            self.db.delete_user(user_id)
            self.refresh_table()

    def create_add_button(self):
        add_btn = tk.Button(
            self.table_frame,
            width=100,
            text="+ Добавить нового пользователя",
            font=('Arial', 12, 'bold'),
            bg='#4CAF50',
            fg='white',
            relief=tk.FLAT,
            command=self.add_new_user
        )
        add_btn.grid(ipadx=5, ipady=5, column = 0, columnspan = 5)
        #-column, -columnspan, -in, -ipadx, -ipady, -padx, -pady, -row, -rowspan, or -sticky

    def add_new_user(self):
        self.db.create_new_user()
        self.refresh_table()

    def refresh_table(self):
        """Полная перерисовка таблицы"""
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        self.entries = []
        self.create_table()
        self.canvas.yview_moveto(0)

    def update_row_data(self, row):
        try:
            kills = int(self.entries[row-1][3].get())
            deads = int(self.entries[row-1][4].get())
            kd = kills / deads if deads != 0 else 0.0
            to_main = "+" if kd > 0.75 else "-"

            # Update K/D
            self.entries[row-1][5].config(state='normal')
            self.entries[row-1][5].delete(0, tk.END)
            self.entries[row-1][5].insert(0, f"{kd:.2f}")
            self.entries[row-1][5].config(state='readonly')

            # Update to_main
            self.entries[row-1][6].config(state='normal')
            self.entries[row-1][6].delete(0, tk.END)
            self.entries[row-1][6].insert(0, to_main)
            self.entries[row-1][6].config(state='readonly')

        except (ValueError, ZeroDivisionError):
            self.handle_update_error(row-1)
            


        
    def commit_changes(self):
        for row in self.entries:
            user_data = (
                row[1].get(),  # username
                row[2].get(),  # urank
                int(row[3].get()),  # kills
                int(row[4].get()),  # deads
                float(row[5].get()),  # kills_deads
                row[6].get() == "+",  # to_main
                int(row[0].get())  # id
            )
            self.db.update_user(user_data)
        print("Данные успешно сохранены!")
        
    def clear_table(self):
        """Удаляет все виджеты таблицы"""
        for widget in self.frame.winfo_children():
            widget.destroy()
        self.entries = []
import tkinter as tk
from tkinter import messagebox

class ApplicationGUI:
    def __init__(self, root, db_handler):
        self.root = root
        self.db = db_handler
        self.entries = []
        self.setup_ui()

    def setup_ui(self):
        self.root.geometry("1280x800")
        self.create_scrollable_area()
        self.create_buttons_frame()  # Новый метод для кнопок
        self.create_table()
        self.create_commit_button()

    def create_scrollable_area(self):
        # Основной контейнер
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Холст и скроллбар
        self.canvas = tk.Canvas(self.main_frame, width=1600)
        self.scrollbar = tk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Фрейм для таблицы
        self.table_frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.table_frame, anchor=tk.NW)

        # Привязка событий
        self.table_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind_all("<MouseWheel>", lambda e: self.canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

    def create_table(self):
        columns = ['ID', 'Username', 'Rank', 'Kills', 'Deads', 'K/D', 'To Main', 'Actions']
        
        # Заголовки
        for col, name in enumerate(columns):
            header = tk.Entry(self.table_frame, relief=tk.GROOVE, font=('Arial', 10, 'bold'))
            header.grid(row=0, column=col, sticky=tk.NSEW)
            header.insert(tk.END, name)
            header.config(state='readonly')
            if col == len(columns)-1:  # Последний столбец
                header.config(width=10)

        # Данные
        data = self.db.fetch_all_users()
        for row_idx, user in enumerate(data, start=1):
            self.create_table_row(row_idx, user)

    def create_table_row(self, row_idx, user_data):
        row_entries = []
        for col in range(7):  # Основные колонки
            e = tk.Entry(self.table_frame, relief=tk.GROOVE)
            e.grid(row=row_idx, column=col, sticky=tk.NSEW)
            
            value = user_data[col]
            if col == 5:  # K/D
                e.insert(tk.END, f"{value:.2f}")
                e.config(state='readonly')
            elif col == 6:  # To Main
                display_value = "+" if value else "-"
                e.insert(tk.END, display_value)
                e.config(state='readonly')
            else:
                e.insert(tk.END, value)
                if col in [3, 4]:  # Kills/Deads
                    e.bind("<KeyRelease>", lambda event, r=row_idx: self.update_row_data(r))

            row_entries.append(e)

        # Кнопка удаления
        delete_btn = tk.Button(
            self.table_frame,
            text="-",
            font=('Arial', 12, 'bold'),
            width=3,
            command=lambda uid=user_data[0]: self.delete_user_warning(uid)
        )
        delete_btn.grid(row=row_idx, column=7, padx=0, pady=1, sticky="nesw")
        row_entries.append(delete_btn)
        
        self.entries.append(row_entries)

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
            to_main = "+" if kd > 0.6 else "-"

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
            
    def create_buttons_frame(self):
        self.buttons_frame = tk.Frame(self.root)
        self.buttons_frame.pack(side=tk.TOP, fill=tk.X, pady=5)
        
        # Кнопка добавления
        self.add_btn = tk.Button(
            self.buttons_frame,
            text="+ Добавить нового пользователя",
            font=('Arial', 12, 'bold'),
            bg='#4CAF50',
            fg='white',
            relief=tk.FLAT,
            command=self.add_new_user
        )
        self.add_btn.pack(side=tk.LEFT, padx=10)

    def handle_update_error(self, row):
        for col in [5, 6]:
            self.entries[row][col].config(state='normal')
            self.entries[row][col].delete(0, tk.END)
            self.entries[row][col].insert(0, "Error")
            self.entries[row][col].config(state='readonly')

    def create_commit_button(self):
        commit_btn = tk.Button(
            self.buttons_frame,  # Перенесено в buttons_frame
            text="💾|COMMIT|💾", 
            bg="#de4d2c", 
            activebackground="#30d146", 
            command=self.commit_changes
        )
        commit_btn.pack(side=tk.LEFT, padx=10)
        
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
import sqlite3
import tkinter
from tkinter import Entry, Button
from tkinter import ttk
import random

root = tkinter.Tk()

connection = sqlite3.connect('my_database.db')
cursor = connection.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS Users (
username TEXT NOT NULL,
urank TEXT NOT NULL,
kills INTEGER NOT NULL,
deads INTEGER NOT NULL,
kills_deads REAL NOT NULL,
to_main BLOB NOT NULL
)
''')



for i in range(0,5):
    example_ranks = ["новобранец","-" ,"-" ,"боец","офицер","-","глава"]
    example_k, example_d = random.randint(0,1000)+1, random.randint(0,1000)+1
    if example_k/example_d>0.5:
        example_to_main = True
    else:
        example_to_main = False
    
    cursor.execute('INSERT INTO Users (username, urank, kills, deads, kills_deads, to_main) VALUES(?, ?, ?, ?, ?, ?)', 
                  ('example', example_ranks[random.randint(0,len(example_ranks)-1)], example_k, example_d, example_k/example_d, example_to_main))

connection.commit()

res = cursor.execute("SELECT username, urank, kills, deads, kills_deads, to_main FROM Users")

root.geometry("500x500")

# Создаем Canvas и Scrollbar
canvas = tkinter.Canvas(root, width=1600)
scrollbar = tkinter.Scrollbar(root, orient="vertical", command=canvas.yview)
scrollbar.pack(side=tkinter.RIGHT, fill=tkinter.Y)
canvas.pack(side=tkinter.LEFT, fill=tkinter.BOTH, expand=False, padx=50)
canvas.configure(yscrollcommand=scrollbar.set)

# Создаем фрейм для таблицы
frame = tkinter.Frame(canvas)
canvas.create_window((0, 0), window=frame, anchor=tkinter.NW)

columns = ['username', 'urank', 'kills', 'deads', 'kills_deads', 'to_main']

data = res.fetchall()

connection.close()

# Создаем таблицу
for i in range(len(data)+1):
    cols = []
    for j in range(6+1):
        e = Entry(frame, relief=tkinter.GROOVE)
        e.grid(row=i, column=j, sticky=tkinter.NSEW)
        
        if j != 0 and i != 0:
            e.insert(tkinter.END, data[i-1][j-1])
        else:
            if i == 0 and j != 0:
                e.insert(tkinter.END, columns[j-1])
            elif i != 0 and j == 0:
                e.insert(tkinter.END, "[WODS]")
        
        cols.append(e)
    
    # Настраиваем вес строки для правильного растяжения
    frame.rowconfigure(i, weight=1)

# Настраиваем вес колонок
for j in range(7):
    frame.columnconfigure(j, weight=1)



def commit_cursor():
    connection = sqlite3.connect('my_database.db')
    cursor = connection.cursor()
    cursor.execute("")
    connection.commit()
    connection.close()
    
commit_but = Button(root, text="""💾|COMMIT|💾""", bg="#de4d2c", activebackground="#30d146", command=commit_cursor)
commit_but.pack(side="left", anchor="nw")
    
# Обновляем scrollregion при изменении размера фрейма
def configure_scrollregion(event):
    canvas.configure(scrollregion=canvas.bbox("all"))

frame.bind("<Configure>", configure_scrollregion)

# Привязка прокрутки колесом мыши
def on_mousewheel(event):
    canvas.yview_scroll(int(-1*(event.delta/120)), "units")

canvas.bind_all("<MouseWheel>", on_mousewheel)

root.mainloop()
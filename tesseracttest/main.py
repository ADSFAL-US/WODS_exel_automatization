import cv2
import pytesseract
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from difflib import SequenceMatcher
import os
import numpy as np
from PIL import Image, ImageTk
import re
from datetime import datetime

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class CropWindow:
    def __init__(self, parent, image_path):
        self.parent = parent
        self.image_path = image_path
        self.points = []
        
        self.window = tk.Toplevel(parent)
        self.window.title("Обрезка изображения")
        
        self.img = cv2.imread(image_path)
        self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)
        self.original_height, self.original_width = self.img.shape[:2]
        
        self.scale_factor = self.calculate_scale_factor()
        self.resized_img = cv2.resize(self.img, None, 
                                    fx=self.scale_factor, 
                                    fy=self.scale_factor)
        
        self.tk_image = ImageTk.PhotoImage(Image.fromarray(self.resized_img))
        
        self.canvas = tk.Canvas(self.window, 
                              width=self.resized_img.shape[1], 
                              height=self.resized_img.shape[0])
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.pack()
        
        self.canvas.bind("<Button-1>", self.on_click)
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
    def calculate_scale_factor(self):
        max_size = 800
        return min(max_size/self.original_width, max_size/self.original_height)
    
    def on_click(self, event):
        if len(self.points) < 2:
            x = int(event.x / self.scale_factor)
            y = int(event.y / self.scale_factor)
            self.points.append((x, y))
            
            # Рисуем маркер
            radius = 5
            self.canvas.create_oval(
                event.x - radius, event.y - radius,
                event.x + radius, event.y + radius,
                fill='red', tags="marker"
            )
            
        if len(self.points) == 2:
            self.crop_image()
            
    def crop_image(self):
        x1, y1 = self.points[0]
        x2, y2 = self.points[1]
        self.cropped_img = self.img[
            min(y1, y2):max(y1, y2),
            min(x1, x2):max(x1, x2)
        ]
        self.window.destroy()
        
    def on_close(self):
        self.cropped_img = None
        self.window.destroy()

class OCRApp:
    def __init__(self, root):
        self.root = root
        self.root.title("OCR Comparer")
        self.root.geometry("800x600")
        
        self.create_widgets()
        self.match_text = self.read_match_file()
    
    def preprocess_text(self, text):
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^a-zа-яё0-9\s]', '', text)  # Добавлена поддержка кириллицы
        return text
        
    def read_match_file(self):
        try:
            with open('match.txt', 'r', encoding='utf-8') as f:
                return self.preprocess_text(f.read())
        except UnicodeDecodeError:
            with open('match.txt', 'r', encoding='cp1252') as f:
                return self.preprocess_text(f.read())
        except FileNotFoundError:
            self.show_error("Файл match.txt не найден!")
            return ""
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Панель управления
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)
        
        self.btn_open = ttk.Button(control_frame, text="Выбрать изображение", command=self.open_image)
        self.btn_open.pack(side=tk.LEFT, padx=5)
        
        self.lbl_file = ttk.Label(control_frame, text="Файл не выбран")
        self.lbl_file.pack(side=tk.LEFT, padx=5)
        
        self.btn_process = ttk.Button(control_frame, text="Обработать", command=self.process_image, state=tk.DISABLED)
        self.btn_process.pack(side=tk.LEFT, padx=5)
        
        # Результаты
        results_frame = ttk.Frame(main_frame)
        results_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.lbl_similarity = ttk.Label(results_frame, text="Сходство: -")
        self.lbl_similarity.pack(anchor=tk.W)
        
        # Текстовое поле с прокруткой
        text_frame = ttk.Frame(results_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        self.txt_output = tk.Text(text_frame, wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(text_frame, command=self.txt_output.yview)
        self.txt_output.configure(yscrollcommand=scrollbar.set)
        
        self.txt_output.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.lbl_error = ttk.Label(results_frame, text="", foreground="red")
        self.lbl_error.pack(anchor=tk.W)
        
    # Остальные методы остаются без изменений, кроме process_image
    
    def process_image(self):
        try:
            if not hasattr(self, 'cropped_img'):
                raise ValueError("Изображение не было обрезано")
                
            # Конвертируем PIL Image в numpy array
            image = cv2.cvtColor(np.array(self.cropped_img), cv2.COLOR_RGB2BGR)
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            gray = cv2.bitwise_not(gray)
            gray = cv2.resize(gray, None, fx=2, fy=2)
            gray = cv2.GaussianBlur(gray, (3, 3), 0)
            
            binary = cv2.adaptiveThreshold(
                gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
            
            config = '--oem 3 --psm 6 -l rus+eng'
            ocr_text = pytesseract.image_to_string(binary, config=config)
            
            # Обновляем текстовое поле
            self.txt_output.delete(1.0, tk.END)
            self.txt_output.insert(tk.END, ocr_text)
            
            processed_ocr = self.preprocess_text(ocr_text)
            
            similarity = SequenceMatcher(
                None, self.match_text, processed_ocr
            ).ratio() * 100
            
            self.lbl_similarity.config(
                text=f"Сходство: {similarity:.2f}%"
            )
            
            data = self.process_ocr_data(ocr_text)
            self.save_to_table(data, 'table.txt')
            
            # Показываем уведомление
            messagebox.showinfo("Успех", "Данные сохранены в table.txt!")
            
        except Exception as e:
            self.show_error(str(e))
    
    def open_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if file_path:
            crop_win = CropWindow(self.root, file_path)
            self.root.wait_window(crop_win.window)
            
            if hasattr(crop_win, 'cropped_img') and crop_win.cropped_img is not None:
                self.cropped_img = Image.fromarray(crop_win.cropped_img)
                self.lbl_file.config(text=os.path.basename(file_path))
                self.btn_process.config(state=tk.NORMAL)
                self.lbl_error.config(text="")
            else:
                self.show_error("Обрезка отменена")
                
                
    def process_ocr_data(self, ocr_text):
        # Регулярка для парсинга строк
        pattern = r"""
            ^\s*                 # Начало строки
            (?:[^\w\s]?\d+)      # Номер места (с возможным спецсимволом в начале)
            \s+                  # Разделитель
            ([^\d]+?)            # Имя игрока (все символы до цифр)
            \s+                  # Разделитель
            (\d+)                # Убийства
            \s+ 
            (\d+)                # Смерти
            \s+ 
            (\d+)                # Помощь
            \s+ 
            ([\dоO]+)            # Потрачено казны (учет возможной буквы 'о' вместо цифр)
            \s+ 
            \d+                  # Счет (пропускаем)
            \s+ 
            \w+                  # Ранг (пропускаем)
            \s*$                 # Конец строки
        """
        
        data = []
        for line in ocr_text.split('\n'):
            line = re.sub(r'[°_—]', ' ', line)  # Чистим специальные символы
            match = re.search(pattern, line, re.VERBOSE | re.IGNORECASE)
            
            if match:
                try:
                    # Обработка потраченной казны
                    treasury = match.group(5).lower().replace('o', '0').replace('ё', '0')
                    treasury = int(treasury) if treasury.isdigit() else 0
                    
                    player_data = {
                        'name': match.group(1).strip(),
                        'kills': int(match.group(2)),
                        'deaths': int(match.group(3)),
                        'treasury': treasury
                    }
                    data.append(player_data)
                except (ValueError, IndexError):
                    continue
        return data
                
                
                
    def save_to_table(self, data, filename):
        headers = ["Имя игрока", "Убийства", "Смерти", "Потрачено казны"]
        max_len = [len(h) for h in headers]
        
        # Определяем максимальные длины полей
        for row in data:
            max_len[0] = max(max_len[0], len(row['name']))
            max_len[1] = max(max_len[1], len(str(row['kills'])))
            max_len[2] = max(max_len[2], len(str(row['deaths'])))
            max_len[3] = max(max_len[3], len(str(row['treasury'])))

        # Форматируем таблицу
        table = []
        table.append(" | ".join([h.ljust(l) for h, l in zip(headers, max_len)]))
        table.append("-" * (sum(max_len) + 3 * len(headers)))
        
        for row in data:
            table.append(
                f"{row['name'].ljust(max_len[0])} | "
                f"{str(row['kills']).ljust(max_len[1])} | "
                f"{str(row['deaths']).ljust(max_len[2])} | "
                f"{str(row['treasury']).ljust(max_len[3])}"
            )
        
        # Добавляем дату создания
        table.insert(0, f"Дата отчета: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(table))
            
            
            
    def show_error(self, message):
        self.lbl_error.config(text=message)
        self.btn_process.config(state=tk.DISABLED)
        self.lbl_similarity.config(text="Сходство: -")

if __name__ == "__main__":
    root = tk.Tk()
    app = OCRApp(root)
    root.mainloop()
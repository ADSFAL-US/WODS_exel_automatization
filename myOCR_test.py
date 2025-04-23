# myOCR_test.py
import cv2
import pytesseract
import tkinter as tk
from tkinter import messagebox
import numpy as np
from PIL import Image, ImageTk
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
import tkinter.ttk as ttk

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class ImageProcessor:
    """Обработка и преобразование изображений"""
    
    @staticmethod
    def load_image(image_path: str) -> np.ndarray:
        """Загрузка и конвертация изображения"""
        img = cv2.imread(image_path, cv2.IMREAD_ANYCOLOR)
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    @staticmethod
    def preprocess_image(image: np.ndarray) -> np.ndarray:
        """Предобработка изображения для OCR"""
        resized = cv2.resize(image, None, fx=4, fy=4)
        gray = cv2.cvtColor(resized, cv2.COLOR_RGB2GRAY)
        inverted = cv2.bitwise_not(gray)
        _, thresh = cv2.threshold(inverted, 100, 255, 0)
        blured = cv2.GaussianBlur(thresh, (9, 9), 0)
        cv2.imwrite("./prerprocessed_image.png", blured)
        return blured
    

class OCRProcessor:
    """Обработка текста с использованием Tesseract OCR"""
    
    TESSERACT_CONFIG = '--oem 3 --psm 6 -l rus+eng'
    
    @classmethod
    def extract_text(cls, image: np.ndarray) -> str:
        """Извлечение текста из изображения"""
        return pytesseract.image_to_string(image, config=cls.TESSERACT_CONFIG)

    @staticmethod
    def preprocess_text(text: str) -> str:
        """Очистка и нормализация текста"""
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)
        return re.sub(r'[^a-zа-яё0-9\s]', '', text)

class CropWindow(tk.Toplevel):
    """Окно для обрезки изображения"""
    
    def __init__(self, parent: tk.Tk, image_path: str):
        super().__init__(parent)
        self.parent = parent
        self.image_path = image_path
        self.points: List[tuple] = []
        self.cropped_img: Optional[np.ndarray] = None
        self.ocr_data: List[Dict[str, Any]] = []  # Добавлено хранилище данных
        
        self._setup_window()
        self._load_image()
        self._bind_events()
        self.ocr_data: List[Dict[str, Any]] = []

    def _setup_window(self) -> None:
        """Настройка параметров окна"""
        self.title("Обрезка изображения")
        self.geometry(f"{self.winfo_screenwidth()//2}x{self.winfo_screenheight()//2}")

    def _load_image(self) -> None:
        """Загрузка и отображение изображения"""
        self.img = ImageProcessor.load_image(self.image_path)
        self.original_height, self.original_width = self.img.shape[:2]
        self.scale_factor = self._calculate_scale_factor()
        
        resized_img = cv2.resize(self.img, None, 
                               fx=self.scale_factor, 
                               fy=self.scale_factor)
        self.tk_image = ImageTk.PhotoImage(Image.fromarray(resized_img))
        
        self.canvas = tk.Canvas(self, width=resized_img.shape[1], height=resized_img.shape[0])
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.pack()

    def _calculate_scale_factor(self) -> float:
        """Вычисление коэффициента масштабирования"""
        max_size = 800
        return min(max_size/self.original_width, max_size/self.original_height)

    def _bind_events(self) -> None:
        """Привязка обработчиков событий"""
        self.canvas.bind("<Button-1>", self._on_click)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_click(self, event: tk.Event) -> None:
        """Обработка клика мыши"""
        if len(self.points) < 2:
            x = int(event.x / self.scale_factor)
            y = int(event.y / self.scale_factor)
            self.points.append((x, y))
            self._draw_marker(event.x, event.y)
            
        if len(self.points) == 2:
            self._crop_image()

    def _draw_marker(self, x: int, y: int) -> None:
        """Отрисовка маркера выбора"""
        radius = 5
        self.canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill='red', tags="marker"
        )

    def _crop_image(self) -> None:
        """Обрезка изображения по выбранным точкам"""
        x1, y1 = self.points[0]
        x2, y2 = self.points[1]
        self.cropped_img = self.img[
            min(y1, y2):max(y1, y2),
            min(x1, x2):max(x1, x2)
        ]
        
        # Непосредственная обработка OCR
        processed_img = ImageProcessor.preprocess_image(self.cropped_img)
        ocr_text = OCRProcessor.extract_text(processed_img)
        self.ocr_data = OCRDataHandler.parse_ocr_data(ocr_text)  # Сохраняем данные
        self._show_ocr_preview()
        

    def _on_close(self) -> None:
        """Обработка закрытия окна"""
        self.cropped_img = None
        self.destroy()
        
    def _show_ocr_preview(self) -> None:
        """Окно проверки распознанных данных"""
        preview_win = tk.Toplevel(self)
        preview_win.title("Проверка данных")
        preview_win.grab_set()

        # Обработка OCR с проверкой ошибок
        try:
            processed_img = ImageProcessor.preprocess_image(self.cropped_img)
            ocr_text = OCRProcessor.extract_text(processed_img)
            self.ocr_data = OCRDataHandler.parse_ocr_data(ocr_text)
            
            # Проверка наличия данных
            if not self.ocr_data:
                raise ValueError("Не удалось распознать данные")
                
        except Exception as e:
            messagebox.showerror("Ошибка", str(e), parent=preview_win)
            preview_win.destroy()
            return

        # Создаем таблицу с данными
        self._create_preview_table(preview_win)

        # Кнопки действий
        btn_frame = tk.Frame(preview_win)
        btn_frame.pack(pady=10)

        def save_and_close():
            preview_win.destroy()
            self.destroy()

        tk.Button(btn_frame, 
                text="Сохранить", 
                command=save_and_close
        ).pack(side="left", padx=5)
        
        tk.Button(btn_frame, 
                text="Отмена", 
                command=lambda: [preview_win.destroy(), self.destroy()]
        ).pack(side="right", padx=5)
        
        
    def _create_preview_table(self, parent: tk.Toplevel) -> None:
        """Таблица для предпросмотра данных с прокруткой"""
        frame = tk.Frame(parent)
        frame.pack(fill="both", expand=True)

        # Создаем Treeview с прокруткой
        tree = ttk.Treeview(frame, 
                          columns=("name", "kills", "deaths", "treasury"),
                          show="headings",
                          height=6)
        
        # Настройка колонок
        tree.heading("name", text="Имя игрока")
        tree.heading("kills", text="Убийства")
        tree.heading("deaths", text="Смерти")
        tree.heading("treasury", text="Казна")
        
        # Добавляем данные
        for player in self.ocr_data:
            tree.insert("", "end", values=(
                player.get('name', 'N/A'),
                player.get('kills', 0),
                player.get('deaths', 0),
                player.get('treasury', 0)
            ))

        # Прокрутка
        scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        
    def _save_and_close(self, preview_win: tk.Toplevel) -> None:
        """Финализация сохранения"""
        preview_win.destroy()
        self.destroy()

class OCRDataHandler:
    
    """Обработка и сохранение данных OCR"""
    
    DATA_PATTERN = re.compile(
        r"""
        ^\s*\d+\.?\s+          # Пропускаем номер места
        ([\w\s_\-—]+?)\s+      # Имя игрока (с пробелами, дефисами, подчеркиваниями и тире)
        (\d+)\s+               # Убийства (У)
        (\d+)\s+               # Смерти (С)
        .*                     # Игнорируем остальные колонки
        """,
        re.VERBOSE | re.UNICODE
    )

    @classmethod
    def parse_ocr_data(cls, ocr_text: str) -> List[Dict[str, Any]]:
        data = []
        for line in ocr_text.split('\n'):
            line = line.strip()
            if not line:
                continue

            # Замена тире и других проблемных символов
            #line = line.replace('—', '-').replace('№', '')
            match = cls.DATA_PATTERN.search(line)
            
            if match:
                try:
                    parsed_data = cls._process_match(match)
                    data.append(parsed_data)
                except Exception as e:
                    print(f"Ошибка обработки строки: {line}\n{str(e)}")
            else:
                print(f"Не распознано: {line}")
        print(data)
        return data


    @classmethod
    def _process_match(cls, match: re.Match) -> Dict[str, Any]:
        """Извлекаем данные из совпадения."""
        return {
            'name': match.group(1).strip(),
            'kills': int(match.group(2)),
            'deaths': int(match.group(3))
        }

    @staticmethod
    def save_to_table(data: List[Dict[str, Any]], filename: str = 'table.txt') -> None:
        """Сохранение данных в табличном формате"""
        headers = ["Имя игрока", "Убийства", "Смерти", "Потрачено казны"]
        max_lens = [len(h) for h in headers]
        
        for row in data:
            max_lens[0] = max(max_lens[0], len(row['name']))
            max_lens[1] = max(max_lens[1], len(str(row['kills'])))
            max_lens[2] = max(max_lens[2], len(str(row['deaths'])))
            max_lens[3] = max(max_lens[3], len(str(row['treasury'])))

        table = [
            " | ".join([h.ljust(l) for h, l in zip(headers, max_lens)]),
            "-" * (sum(max_lens) + 3 * len(headers))
        ]
        
        for row in data:
            table.append(
                f"{row['name'].ljust(max_lens[0])} | "
                f"{str(row['kills']).ljust(max_lens[1])} | "
                f"{str(row['deaths']).ljust(max_lens[2])} | "
                f"{str(row['treasury']).ljust(max_lens[3])}"
            )
            
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join([f"Дата отчета: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"] + table))

class OCRApp:
    """Основное приложение для обработки OCR"""
    
    def __init__(self, root: tk.Tk, file_path: str):
        self.root = root
        self.file_path = file_path
        self.processed_data: List[Dict[str, Any]] = []
        self._setup_ui()
        self._process_image()

    def _setup_ui(self) -> None:
        """Настройка интерфейса загрузки"""
        self.root.title("Обработка...")
        tk.Label(
            self.root, 
            text="Идет обработка изображения...",
            font=('Arial', 12)
        ).pack(pady=20, padx=20)

    def _process_image(self) -> None:
        try:
            crop_win = CropWindow(self.root, self.file_path)
            self.root.wait_window(crop_win)
            
            # Проверка на None и тип данных
            if crop_win.cropped_img is None or not isinstance(crop_win.cropped_img, np.ndarray):
                return
            
            # Обработка изображения
            processed_img = ImageProcessor.preprocess_image(crop_win.cropped_img)
            ocr_text = OCRProcessor.extract_text(processed_img)
            self.processed_data = OCRDataHandler.parse_ocr_data(ocr_text)
        except Exception as e:
            messagebox.showerror("Ошибка OCR", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    OCRApp(root, "test_image.png")
    root.mainloop()
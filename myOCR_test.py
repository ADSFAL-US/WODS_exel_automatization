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
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        inverted = cv2.bitwise_not(gray)
        resized = cv2.resize(inverted, None, fx=2, fy=2)
        return cv2.GaussianBlur(resized, (3, 3), 0)

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
        
        self._setup_window()
        self._load_image()
        self._bind_events()

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
        self.destroy()

    def _on_close(self) -> None:
        """Обработка закрытия окна"""
        self.cropped_img = None
        self.destroy()

class OCRDataHandler:
    """Обработка и сохранение данных OCR"""
    
    DATA_PATTERN = re.compile(r"""
        ^\s*(?:[^\w\s]?\d+)\s+      # Номер места
        ([^\d]+?)\s+                # Имя игрока
        (\d+)\s+(\d+)\s+(\d+)\s+   # K/D/A
        ([\dоO]+)\s+               # Потрачено казны
        \d+\s+\w+\s*$              # Пропуск остальных полей
    """, re.VERBOSE | re.IGNORECASE)

    @classmethod
    def parse_ocr_data(cls, ocr_text: str) -> List[Dict[str, Any]]:
        data = []
        for line in ocr_text.split('\n'):
            line = line.strip()
            if not line:  # Пропуск пустых строк
                continue
            match = cls.DATA_PATTERN.search(line)
            if match is not None:  # Явная проверка
                try:
                    data.append(cls._process_match(match))
                except (ValueError, IndexError):
                    continue
        return data


    @classmethod
    def _process_match(cls, match: re.Match) -> Dict[str, Any]:
        """Обработка совпадения регулярного выражения"""
        treasury = match.group(5).lower().replace('o', '0').replace('ё', '0')
        return {
            'name': match.group(1).strip(),
            'kills': int(match.group(2)),
            'deaths': int(match.group(3)),
            'treasury': int(treasury) if treasury.isdigit() else 0
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
import easyocr
from PIL import Image

class OCRProcessor:
    """
    Класс для распознавания текста с изображений с использованием EasyOCR.
    
    Attributes:
        default_lang (list): Список языков для распознавания (по умолчанию ['en', 'ru'])
        ocr_reader: Экземпляр EasyOCR Reader
    """
    
    def __init__(self, default_lang=['en', 'ru']):
        """
        Инициализация процессора OCR.
        
        Args:
            default_lang (list): Список языков для распознавания
        """
        self.ocr_reader = easyocr.Reader(
            lang_list=default_lang,
            gpu=False,
            verbose=False
        )

    def recognize(self, image_path, prompt_question=None):
        """
        Распознает текст на изображении.
        
        Args:
            image_path (str): Путь к изображению
            prompt_question: Аргумент для совместимости (не используется)
            
        Returns:
            str: Распознанный текст, объединенный в одну строку
        """
        # Выполняем распознавание
        result = (self.ocr_reader.readtext(image_path))
        
        
        texts = [text for _, text, _ in result]
        
        
        out = ('\n->'.join(texts)).lower()
        out = out.replace("сержант", "")
        out = out.replace("офицер", "")
        out = out.replace("лидер", "")
        return out
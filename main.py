# main.py
from start_window import StartWindow

def main() -> None:
    """Точка входа в приложение"""
    try:
        root = StartWindow()
        root.mainloop()
    except Exception as e:
        print(f"Critical error: {str(e)}")

if __name__ == "__main__":
    main()
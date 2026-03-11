"""
main.py — Точка запуска ИС Фотоцентра.
"""

from app import PhotoCenterApp


def main() -> None:
    """Запустить приложение."""
    app = PhotoCenterApp()
    app.mainloop()


if __name__ == "__main__":
    main()

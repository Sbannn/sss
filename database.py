"""
database.py — Слой хранения данных (JSON-файл).
Обеспечивает персистентность для клиентов, заказов, оплат и прайс-листа.
"""

import json
import os
from typing import Any, Dict


_DEFAULT_PRICES: Dict[str, float] = {
    "10x15": 15.0,
    "15x20": 25.0,
    "20x30": 45.0,
    "A4": 60.0,
    "A3": 90.0,
}


class Database:
    """Простая JSON-база данных для ИС Фотоцентра."""

    def __init__(self, filepath: str = "data.json") -> None:
        self.filepath = filepath
        self._data: Dict[str, Any] = {
            "clients": {},
            "orders": {},
            "payments": {},
            "price_list": dict(_DEFAULT_PRICES),
        }
        self._load()

    # ------------------------------------------------------------------
    # Internal I/O
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Загрузить данные из файла (если существует)."""
        if not os.path.exists(self.filepath):
            return
        try:
            with open(self.filepath, "r", encoding="utf-8") as fh:
                saved = json.load(fh)
            for key in self._data:
                if key in saved:
                    self._data[key] = saved[key]
        except (json.JSONDecodeError, IOError):
            pass  # повреждённый файл — работаем с дефолтами

    def save(self) -> None:
        """Сохранить текущее состояние в файл."""
        with open(self.filepath, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # Clients
    # ------------------------------------------------------------------

    def get_clients(self) -> dict:
        return dict(self._data["clients"])

    def add_client(self, client_id: str, client_data: dict) -> None:
        self._data["clients"][client_id] = client_data
        self.save()

    def delete_client(self, client_id: str) -> None:
        self._data["clients"].pop(client_id, None)
        self.save()

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    def get_orders(self) -> dict:
        return dict(self._data["orders"])

    def add_order(self, order_id: str, order_data: dict) -> None:
        self._data["orders"][order_id] = order_data
        self.save()

    def update_order(self, order_id: str, order_data: dict) -> None:
        self._data["orders"][order_id] = order_data
        self.save()

    # ------------------------------------------------------------------
    # Payments
    # ------------------------------------------------------------------

    def get_payments(self) -> dict:
        return dict(self._data["payments"])

    def add_payment(self, payment_id: str, payment_data: dict) -> None:
        self._data["payments"][payment_id] = payment_data
        self.save()

    def update_payment(self, payment_id: str, payment_data: dict) -> None:
        self._data["payments"][payment_id] = payment_data
        self.save()

    # ------------------------------------------------------------------
    # Price list
    # ------------------------------------------------------------------

    def get_price_list(self) -> dict:
        return dict(self._data["price_list"])

    def set_price(self, format_name: str, price: float) -> None:
        self._data["price_list"][format_name] = price
        self.save()

    def delete_price(self, format_name: str) -> None:
        self._data["price_list"].pop(format_name, None)
        self.save()

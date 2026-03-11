"""
models.py — Бизнес-логика ИС Фотоцентра.
Содержит классы: PriceList, Photo, Client, Order, Payment, Employee, Administrator, Cashier.
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class PriceList:
    """Прайс-лист формата печати."""

    format: str
    price: float

    def update_price(self, new_price: float) -> None:
        """Обновить цену формата печати."""
        if new_price <= 0:
            raise ValueError("Цена должна быть положительной")
        self.price = new_price

    def get_price(self) -> float:
        """Вернуть текущую цену."""
        return self.price


@dataclass
class Photo:
    """Фотография, добавленная в заказ."""

    id: str
    format: str
    copy_count: int
    additional_options: List[str] = field(default_factory=list)

    def upload(self) -> str:
        """Зафиксировать загрузку фотографии."""
        if self.copy_count <= 0:
            raise ValueError("Количество копий должно быть положительным")
        return f"Фото {self.id} загружено"

    def delete(self) -> str:
        """Зафиксировать удаление фотографии."""
        return f"Фото {self.id} удалено"


@dataclass
class Client:
    """Клиент фотоцентра."""

    id: str
    name: str
    phone: str
    email: str

    def validate(self) -> bool:
        """Проверить заполненность обязательных полей."""
        return bool(self.name.strip() and self.phone.strip())

    def receive_product(self, order_id: str) -> str:
        """Подтвердить получение заказа клиентом."""
        return f"Клиент {self.name} получил заказ {order_id}"


@dataclass
class Order:
    """Заказ на печать фотографий."""

    order_number: str
    order_date: str
    client_id: str
    photos: List[Photo] = field(default_factory=list)
    status: str = "Новый"
    total: float = 0.0

    VALID_STATUSES: List[str] = field(
        default_factory=lambda: ["Новый", "В обработке", "Готов", "Оплачен", "Выдан"],
        repr=False,
    )

    def calculate_cost(self, price_list: dict) -> float:
        """Рассчитать итоговую стоимость заказа."""
        total = 0.0
        for photo in self.photos:
            price = price_list.get(photo.format, 0.0)
            total += price * photo.copy_count
        self.total = total
        return total

    def change_status(self, new_status: str) -> None:
        """Изменить статус заказа."""
        valid = ["Новый", "В обработке", "Готов", "Оплачен", "Выдан"]
        if new_status not in valid:
            raise ValueError(f"Недопустимый статус: {new_status}")
        self.status = new_status


@dataclass
class Payment:
    """Платёж по заказу."""

    id: str
    order_number: str
    payment_method: str
    amount: float
    status: str = "Ожидает оплаты"

    def process(self) -> str:
        """Провести оплату."""
        self.status = "Оплачен"
        return self.status

    def get_receipt(self) -> str:
        """Сформировать строку чека."""
        return (
            f"Чек №{self.id}: заказ {self.order_number}, "
            f"{self.payment_method}, {self.amount:.2f} руб."
        )


class Employee:
    """Базовый класс сотрудника фотоцентра."""

    def __init__(self, role: str, name: str) -> None:
        self.role = role
        self.name = name
        self._logged_in: bool = False

    def login(self) -> str:
        """Войти в систему."""
        self._logged_in = True
        return f"{self.name} вошёл в систему"

    def logout(self) -> str:
        """Выйти из системы."""
        self._logged_in = False
        return f"{self.name} вышел из системы"

    @property
    def is_logged_in(self) -> bool:
        """Флаг активной сессии."""
        return self._logged_in


class Administrator(Employee):
    """Администратор — управляет прайс-листом."""

    def __init__(self, admin_id: str, name: str) -> None:
        super().__init__("Администратор", name)
        self.id = admin_id

    def set_price(self, price_list: PriceList, price: float) -> None:
        """Установить новую цену в прайс-листе."""
        price_list.update_price(price)

    def edit_price(self, price_list: PriceList, new_price: float) -> None:
        """Редактировать существующую цену."""
        price_list.update_price(new_price)


class Cashier(Employee):
    """Кассир — проверяет оплату и выдаёт заказы."""

    def __init__(self, cashier_id: str, name: str) -> None:
        super().__init__("Кассир", name)
        self.id = cashier_id

    def verify_payment(self, payment: Payment) -> bool:
        """Проверить, что заказ оплачен."""
        return payment.status == "Оплачен"

    def hand_out_product(self, order: Order) -> str:
        """Выдать оплаченный заказ клиенту."""
        if order.status == "Оплачен":
            order.change_status("Выдан")
            return f"Заказ {order.order_number} выдан клиенту"
        return "Заказ ещё не оплачен"

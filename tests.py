"""
tests.py — Unit-тесты для ИС Фотоцентра.
Покрывают: PriceList, Photo, Client, Order, Payment,
           Employee, Administrator, Cashier, Database.
Запуск: python -m pytest tests.py -v
"""

import os
import json
import tempfile
import unittest

from models import (
    PriceList, Photo, Client, Order, Payment,
    Employee, Administrator, Cashier,
)
from database import Database


# ══════════════════════════════════════════════════════════════════════
class TestPriceList(unittest.TestCase):
# ══════════════════════════════════════════════════════════════════════

    def setUp(self):
        self.pl = PriceList("10x15", 15.0)

    def test_get_price_returns_initial(self):
        self.assertEqual(self.pl.get_price(), 15.0)

    def test_update_price_valid(self):
        self.pl.update_price(20.0)
        self.assertEqual(self.pl.get_price(), 20.0)

    def test_update_price_zero_raises(self):
        with self.assertRaises(ValueError):
            self.pl.update_price(0)

    def test_update_price_negative_raises(self):
        with self.assertRaises(ValueError):
            self.pl.update_price(-5)

    def test_format_stored(self):
        self.assertEqual(self.pl.format, "10x15")


# ══════════════════════════════════════════════════════════════════════
class TestPhoto(unittest.TestCase):
# ══════════════════════════════════════════════════════════════════════

    def setUp(self):
        self.photo = Photo("P1", "10x15", 3)

    def test_upload_returns_string(self):
        result = self.photo.upload()
        self.assertIn("P1", result)

    def test_upload_zero_copies_raises(self):
        bad = Photo("P2", "10x15", 0)
        with self.assertRaises(ValueError):
            bad.upload()

    def test_delete_returns_string(self):
        result = self.photo.delete()
        self.assertIn("P1", result)

    def test_additional_options_default_empty(self):
        self.assertEqual(self.photo.additional_options, [])

    def test_additional_options_custom(self):
        p = Photo("P3", "A4", 1, ["рамка", "ламинирование"])
        self.assertEqual(len(p.additional_options), 2)


# ══════════════════════════════════════════════════════════════════════
class TestClient(unittest.TestCase):
# ══════════════════════════════════════════════════════════════════════

    def setUp(self):
        self.client = Client("C1", "Иван Иванов", "+79001112233", "ivan@mail.ru")

    def test_validate_success(self):
        self.assertTrue(self.client.validate())

    def test_validate_empty_name_fails(self):
        bad = Client("C2", "  ", "+7900", "")
        self.assertFalse(bad.validate())

    def test_validate_empty_phone_fails(self):
        bad = Client("C3", "Имя", "", "")
        self.assertFalse(bad.validate())

    def test_receive_product_message(self):
        msg = self.client.receive_product("О-001")
        self.assertIn("Иван Иванов", msg)
        self.assertIn("О-001", msg)

    def test_fields_stored(self):
        self.assertEqual(self.client.id, "C1")
        self.assertEqual(self.client.email, "ivan@mail.ru")


# ══════════════════════════════════════════════════════════════════════
class TestOrder(unittest.TestCase):
# ══════════════════════════════════════════════════════════════════════

    def _make_order(self):
        photos = [Photo("P1", "10x15", 2), Photo("P2", "A4", 1)]
        return Order("О-001", "01.01.2026", "C1", photos)

    def test_default_status_new(self):
        o = self._make_order()
        self.assertEqual(o.status, "Новый")

    def test_calculate_cost(self):
        o = self._make_order()
        price_list = {"10x15": 15.0, "A4": 60.0}
        cost = o.calculate_cost(price_list)
        # 2*15 + 1*60 = 90
        self.assertAlmostEqual(cost, 90.0)
        self.assertAlmostEqual(o.total, 90.0)

    def test_calculate_cost_unknown_format_zero(self):
        o = Order("О-002", "01.01.2026", "C1",
                  [Photo("P3", "НЕИЗВЕСТНЫЙ", 5)])
        cost = o.calculate_cost({"10x15": 15.0})
        self.assertAlmostEqual(cost, 0.0)

    def test_change_status_valid(self):
        o = self._make_order()
        o.change_status("В обработке")
        self.assertEqual(o.status, "В обработке")

    def test_change_status_all_valid_values(self):
        o = self._make_order()
        for status in ("Новый", "В обработке", "Готов", "Оплачен", "Выдан"):
            o.change_status(status)
            self.assertEqual(o.status, status)

    def test_change_status_invalid_raises(self):
        o = self._make_order()
        with self.assertRaises(ValueError):
            o.change_status("НеСуществует")

    def test_order_fields(self):
        o = self._make_order()
        self.assertEqual(o.order_number, "О-001")
        self.assertEqual(o.client_id, "C1")
        self.assertEqual(len(o.photos), 2)


# ══════════════════════════════════════════════════════════════════════
class TestPayment(unittest.TestCase):
# ══════════════════════════════════════════════════════════════════════

    def setUp(self):
        self.pay = Payment("П-001", "О-001", "Наличные", 150.0)

    def test_default_status(self):
        self.assertEqual(self.pay.status, "Ожидает оплаты")

    def test_process_changes_status(self):
        self.pay.process()
        self.assertEqual(self.pay.status, "Оплачен")

    def test_process_returns_string(self):
        result = self.pay.process()
        self.assertEqual(result, "Оплачен")

    def test_get_receipt_contains_fields(self):
        receipt = self.pay.get_receipt()
        self.assertIn("П-001", receipt)
        self.assertIn("О-001", receipt)
        self.assertIn("150", receipt)
        self.assertIn("Наличные", receipt)

    def test_payment_fields(self):
        self.assertEqual(self.pay.order_number, "О-001")
        self.assertAlmostEqual(self.pay.amount, 150.0)


# ══════════════════════════════════════════════════════════════════════
class TestEmployee(unittest.TestCase):
# ══════════════════════════════════════════════════════════════════════

    def setUp(self):
        self.emp = Employee("Оператор", "Мария")

    def test_default_not_logged_in(self):
        self.assertFalse(self.emp.is_logged_in)

    def test_login(self):
        msg = self.emp.login()
        self.assertTrue(self.emp.is_logged_in)
        self.assertIn("Мария", msg)

    def test_logout(self):
        self.emp.login()
        msg = self.emp.logout()
        self.assertFalse(self.emp.is_logged_in)
        self.assertIn("Мария", msg)

    def test_role_stored(self):
        self.assertEqual(self.emp.role, "Оператор")


# ══════════════════════════════════════════════════════════════════════
class TestAdministrator(unittest.TestCase):
# ══════════════════════════════════════════════════════════════════════

    def setUp(self):
        self.admin = Administrator("A1", "Анна")
        self.pl = PriceList("15x20", 25.0)

    def test_role_is_administrator(self):
        self.assertEqual(self.admin.role, "Администратор")

    def test_set_price(self):
        self.admin.set_price(self.pl, 30.0)
        self.assertAlmostEqual(self.pl.get_price(), 30.0)

    def test_edit_price(self):
        self.admin.edit_price(self.pl, 35.0)
        self.assertAlmostEqual(self.pl.get_price(), 35.0)

    def test_set_price_invalid_raises(self):
        with self.assertRaises(ValueError):
            self.admin.set_price(self.pl, -1.0)

    def test_admin_login(self):
        self.admin.login()
        self.assertTrue(self.admin.is_logged_in)

    def test_id_stored(self):
        self.assertEqual(self.admin.id, "A1")


# ══════════════════════════════════════════════════════════════════════
class TestCashier(unittest.TestCase):
# ══════════════════════════════════════════════════════════════════════

    def setUp(self):
        self.cashier = Cashier("K1", "Борис")

    def _paid_order(self):
        o = Order("О-003", "01.01.2026", "C1", status="Оплачен")
        return o

    def _unpaid_order(self):
        o = Order("О-004", "01.01.2026", "C1", status="Готов")
        return o

    def test_role_is_cashier(self):
        self.assertEqual(self.cashier.role, "Кассир")

    def test_verify_payment_paid(self):
        pay = Payment("П-002", "О-003", "Карта", 100.0, status="Оплачен")
        self.assertTrue(self.cashier.verify_payment(pay))

    def test_verify_payment_unpaid(self):
        pay = Payment("П-003", "О-004", "Карта", 100.0)
        self.assertFalse(self.cashier.verify_payment(pay))

    def test_hand_out_paid_order(self):
        order = self._paid_order()
        result = self.cashier.hand_out_product(order)
        self.assertEqual(order.status, "Выдан")
        self.assertIn("О-003", result)

    def test_hand_out_unpaid_order_no_change(self):
        order = self._unpaid_order()
        result = self.cashier.hand_out_product(order)
        self.assertNotEqual(order.status, "Выдан")
        self.assertIn("не оплачен", result)

    def test_cashier_login(self):
        self.cashier.login()
        self.assertTrue(self.cashier.is_logged_in)


# ══════════════════════════════════════════════════════════════════════
class TestDatabase(unittest.TestCase):
# ══════════════════════════════════════════════════════════════════════

    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.unlink(self.path)   # удаляем — Database создаст нужную
        self.db = Database(self.path)

    def tearDown(self):
        if os.path.exists(self.path):
            os.unlink(self.path)

    # --- price list ---

    def test_default_prices_loaded(self):
        prices = self.db.get_price_list()
        self.assertIn("10x15", prices)

    def test_set_and_get_price(self):
        self.db.set_price("13x18", 20.0)
        self.assertAlmostEqual(self.db.get_price_list()["13x18"], 20.0)

    def test_delete_price(self):
        self.db.delete_price("10x15")
        self.assertNotIn("10x15", self.db.get_price_list())

    def test_delete_nonexistent_price_no_error(self):
        self.db.delete_price("НеСуществует")  # не должно бросать

    # --- clients ---

    def test_add_and_get_client(self):
        self.db.add_client("C1", {"name": "Иван", "phone": "999", "email": ""})
        clients = self.db.get_clients()
        self.assertIn("C1", clients)
        self.assertEqual(clients["C1"]["name"], "Иван")

    def test_delete_client(self):
        self.db.add_client("C2", {"name": "Пётр", "phone": "888", "email": ""})
        self.db.delete_client("C2")
        self.assertNotIn("C2", self.db.get_clients())

    def test_delete_nonexistent_client_no_error(self):
        self.db.delete_client("NOID")

    # --- orders ---

    def test_add_and_get_order(self):
        self.db.add_order("О-001", {"status": "Новый", "total": 90.0,
                                     "client_id": "C1", "date": "01.01.2026",
                                     "photos": []})
        orders = self.db.get_orders()
        self.assertIn("О-001", orders)

    def test_update_order(self):
        self.db.add_order("О-002", {"status": "Новый", "total": 0})
        self.db.update_order("О-002", {"status": "Оплачен", "total": 50.0})
        self.assertEqual(self.db.get_orders()["О-002"]["status"], "Оплачен")

    # --- payments ---

    def test_add_and_get_payment(self):
        self.db.add_payment("П-001", {"order_number": "О-001",
                                       "payment_method": "Карта",
                                       "amount": 90.0, "status": "Оплачен"})
        payments = self.db.get_payments()
        self.assertIn("П-001", payments)

    def test_update_payment(self):
        self.db.add_payment("П-002", {"status": "Ожидает"})
        self.db.update_payment("П-002", {"status": "Оплачен"})
        self.assertEqual(self.db.get_payments()["П-002"]["status"], "Оплачен")

    # --- persistence ---

    def test_persistence_across_instances(self):
        self.db.add_client("C99", {"name": "Тест", "phone": "000", "email": ""})
        db2 = Database(self.path)
        self.assertIn("C99", db2.get_clients())

    def test_corrupted_file_loads_defaults(self):
        with open(self.path, "w") as f:
            f.write("{INVALID JSON}")
        db2 = Database(self.path)
        # должен загрузить значения по умолчанию
        self.assertIn("10x15", db2.get_price_list())


# ══════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    unittest.main(verbosity=2)

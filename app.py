"""
app.py — Графический интерфейс ИС Фотоцентра.
Архитектура: боковая панель навигации + сменная рабочая область.
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import uuid
from datetime import datetime

from database import Database
from models import (
    Client, Order, Photo, Payment, PriceList,
    Administrator, Cashier,
)

# ──────────────────────────────────────────────
# Цветовая палитра
# ──────────────────────────────────────────────
C_SIDEBAR   = "#1e3a5f"
C_NAV_ACT   = "#2980b9"
C_NAV_HOV   = "#2c5f8f"
C_HEADER    = "#1e3a5f"
C_BG        = "#f0f4f8"
C_CARD      = "#ffffff"
C_TEXT      = "#2d3436"
C_MUTED     = "#636e72"
C_PRIMARY   = "#2980b9"
C_SUCCESS   = "#27ae60"
C_WARNING   = "#f39c12"
C_DANGER    = "#e74c3c"
C_WHITE     = "#ffffff"

FONT_TITLE  = ("Segoe UI", 14, "bold")
FONT_HEAD   = ("Segoe UI", 10, "bold")
FONT_BODY   = ("Segoe UI", 10)
FONT_SMALL  = ("Segoe UI", 9)
FONT_LOGO   = ("Segoe UI", 13, "bold")

SECTIONS = [
    ("clients",   "  Клиенты"),
    ("orders",    "  Заказы"),
    ("pricelist", "  Прайс-лист"),
    ("payments",  "  Оплата"),
    ("handout",   "  Выдача заказов"),
]


# ══════════════════════════════════════════════════════════════════════
class PhotoCenterApp(tk.Tk):
# ══════════════════════════════════════════════════════════════════════

    def __init__(self) -> None:
        super().__init__()
        self.title("ИС Фотоцентра")
        self.geometry("1160x700")
        self.minsize(900, 600)
        self.configure(bg=C_BG)

        self.db = Database("data.json")
        self._nav_buttons: dict = {}
        self._sections: dict = {}
        self._active_section: str = ""

        # Временный список фото при создании заказа
        self._draft_photos: list = []

        self._build_ui()
        self._show_section("clients")

    # ──────────────────────────────────────────
    # UI  SKELETON
    # ──────────────────────────────────────────

    def _build_ui(self) -> None:
        # Sidebar
        self.sidebar = tk.Frame(self, bg=C_SIDEBAR, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        # Logo
        tk.Label(
            self.sidebar,
            text="\U0001F4F7  ФотоЦентр",
            bg=C_SIDEBAR, fg=C_WHITE,
            font=FONT_LOGO, anchor="w",
            padx=18, pady=22,
        ).pack(fill="x")

        ttk.Separator(self.sidebar, orient="horizontal").pack(fill="x", padx=12)

        # Nav buttons
        for key, label in SECTIONS:
            btn = tk.Button(
                self.sidebar,
                text=label,
                bg=C_SIDEBAR, fg=C_WHITE,
                activebackground=C_NAV_ACT, activeforeground=C_WHITE,
                relief="flat", anchor="w",
                font=FONT_BODY, padx=18, pady=11,
                cursor="hand2",
                command=lambda k=key: self._show_section(k),
            )
            btn.pack(fill="x", pady=1)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=C_NAV_HOV)
                     if b != self._nav_buttons.get(self._active_section) else None)
            btn.bind("<Leave>", lambda e, b=btn, k=key: b.config(
                bg=C_NAV_ACT if k == self._active_section else C_SIDEBAR))
            self._nav_buttons[key] = btn

        # Right content area
        right = tk.Frame(self, bg=C_BG)
        right.pack(side="left", fill="both", expand=True)

        # Header bar
        self.header_bar = tk.Frame(right, bg=C_HEADER, height=52)
        self.header_bar.pack(fill="x")
        self.header_bar.pack_propagate(False)
        self.header_label = tk.Label(
            self.header_bar, text="", bg=C_HEADER, fg=C_WHITE,
            font=FONT_TITLE, anchor="w", padx=20,
        )
        self.header_label.pack(side="left", fill="y")

        # Content container
        self.content = tk.Frame(right, bg=C_BG)
        self.content.pack(fill="both", expand=True, padx=20, pady=16)

        # Status bar
        self.status_var = tk.StringVar(value="Готово")
        status_bar = tk.Frame(right, bg=C_HEADER, height=26)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)
        tk.Label(
            status_bar, textvariable=self.status_var,
            bg=C_HEADER, fg=C_WHITE, font=FONT_SMALL, anchor="w", padx=12,
        ).pack(fill="y", side="left")

        # Build sections
        self._sections["clients"]   = self._build_clients_section()
        self._sections["orders"]    = self._build_orders_section()
        self._sections["pricelist"] = self._build_pricelist_section()
        self._sections["payments"]  = self._build_payments_section()
        self._sections["handout"]   = self._build_handout_section()

    # ──────────────────────────────────────────
    # NAVIGATION
    # ──────────────────────────────────────────

    def _show_section(self, key: str) -> None:
        if self._active_section:
            self._nav_buttons[self._active_section].config(bg=C_SIDEBAR)
            self._sections[self._active_section].pack_forget()

        self._active_section = key
        self._nav_buttons[key].config(bg=C_NAV_ACT)
        label = dict(SECTIONS)[key].strip()
        self.header_label.config(text=label)
        self._sections[key].pack(fill="both", expand=True)

        # Refresh data when entering section
        refresh = getattr(self, f"_refresh_{key}", None)
        if callable(refresh):
            refresh()

    # ──────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────

    def _card(self, parent: tk.Frame, title: str = "") -> tk.Frame:
        """Создать карточку (белый блок) с заголовком."""
        outer = tk.Frame(parent, bg=C_BG)
        if title:
            tk.Label(outer, text=title, bg=C_BG, fg=C_MUTED,
                     font=FONT_HEAD, anchor="w").pack(anchor="w", pady=(0, 4))
        inner = tk.Frame(outer, bg=C_CARD, bd=0, relief="flat",
                         highlightthickness=1,
                         highlightbackground="#dfe6e9")
        inner.pack(fill="both", expand=True)
        return outer, inner

    def _toolbar(self, parent: tk.Frame, buttons: list) -> tk.Frame:
        """Строка кнопок над таблицей."""
        bar = tk.Frame(parent, bg=C_BG)
        bar.pack(fill="x", pady=(0, 8))
        for label, color, cmd in buttons:
            tk.Button(
                bar, text=label, bg=color, fg=C_WHITE,
                activebackground=color, font=FONT_BODY,
                relief="flat", padx=14, pady=6,
                cursor="hand2", command=cmd,
            ).pack(side="left", padx=(0, 8))
        return bar

    def _tree(self, parent: tk.Frame, columns: list) -> ttk.Treeview:
        """Создать Treeview с полосами прокрутки."""
        style = ttk.Style()
        style.configure("Custom.Treeview",
                         rowheight=28, font=FONT_BODY,
                         background=C_CARD, fieldbackground=C_CARD)
        style.configure("Custom.Treeview.Heading",
                         font=FONT_HEAD, background="#dfe6e9")
        style.map("Custom.Treeview", background=[("selected", C_PRIMARY)])

        frame = tk.Frame(parent, bg=C_CARD)
        frame.pack(fill="both", expand=True, padx=1, pady=1)

        vsb = ttk.Scrollbar(frame, orient="vertical")
        vsb.pack(side="right", fill="y")

        tv = ttk.Treeview(
            frame, columns=columns, show="headings",
            yscrollcommand=vsb.set, style="Custom.Treeview",
        )
        vsb.config(command=tv.yview)

        for col in columns:
            tv.heading(col, text=col)
            tv.column(col, width=120, anchor="w", stretch=True)
        tv.pack(fill="both", expand=True)
        return tv

    def _status(self, msg: str) -> None:
        self.status_var.set(msg)

    # ══════════════════════════════════════════
    # SECTION — КЛИЕНТЫ
    # ══════════════════════════════════════════

    def _build_clients_section(self) -> tk.Frame:
        frame = tk.Frame(self.content, bg=C_BG)

        self._toolbar(frame, [
            ("+ Добавить клиента", C_PRIMARY,  self._add_client),
            ("Удалить",            C_DANGER,   self._del_client),
        ])

        outer, inner = self._card(frame, "Список клиентов")
        outer.pack(fill="both", expand=True)

        cols = ("ID", "Имя", "Телефон", "E-mail")
        self.tv_clients = self._tree(inner, cols)
        self.tv_clients.column("ID",      width=90)
        self.tv_clients.column("Имя",     width=200)
        self.tv_clients.column("Телефон", width=150)
        self.tv_clients.column("E-mail",  width=200)
        return frame

    def _refresh_clients(self) -> None:
        self.tv_clients.delete(*self.tv_clients.get_children())
        for cid, c in self.db.get_clients().items():
            self.tv_clients.insert("", "end",
                values=(cid, c["name"], c["phone"], c["email"]))

    def _add_client(self) -> None:
        dlg = _FormDialog(self, "Новый клиент", [
            ("Имя*",     "text"),
            ("Телефон*", "text"),
            ("E-mail",   "text"),
        ])
        if not dlg.result:
            return
        name, phone, email = dlg.result
        if not name or not phone:
            messagebox.showwarning("Внимание", "Имя и телефон обязательны")
            return
        cid = str(uuid.uuid4())[:8].upper()
        client = Client(cid, name, phone, email)
        if not client.validate():
            messagebox.showwarning("Внимание", "Некорректные данные")
            return
        self.db.add_client(cid, {"name": name, "phone": phone, "email": email})
        self._refresh_clients()
        self._status(f"Клиент {name} добавлен")

    def _del_client(self) -> None:
        sel = self.tv_clients.selection()
        if not sel:
            messagebox.showinfo("Выберите строку", "Выберите клиента для удаления")
            return
        cid = self.tv_clients.item(sel[0])["values"][0]
        if messagebox.askyesno("Подтверждение", f"Удалить клиента {cid}?"):
            self.db.delete_client(cid)
            self._refresh_clients()
            self._status(f"Клиент {cid} удалён")

    # ══════════════════════════════════════════
    # SECTION — ЗАКАЗЫ
    # ══════════════════════════════════════════

    def _build_orders_section(self) -> tk.Frame:
        frame = tk.Frame(self.content, bg=C_BG)

        self._toolbar(frame, [
            ("+ Создать заказ",    C_PRIMARY,  self._create_order),
            ("Изменить статус",    C_WARNING,  self._change_order_status),
        ])

        outer, inner = self._card(frame, "Список заказов")
        outer.pack(fill="both", expand=True)

        cols = ("№ заказа", "Дата", "Клиент", "Фото", "Статус", "Сумма, руб.")
        self.tv_orders = self._tree(inner, cols)
        self.tv_orders.column("№ заказа",    width=100)
        self.tv_orders.column("Дата",        width=110)
        self.tv_orders.column("Клиент",      width=160)
        self.tv_orders.column("Фото",        width=60)
        self.tv_orders.column("Статус",      width=120)
        self.tv_orders.column("Сумма, руб.", width=100)
        return frame

    def _refresh_orders(self) -> None:
        self.tv_orders.delete(*self.tv_orders.get_children())
        clients = self.db.get_clients()
        for oid, o in self.db.get_orders().items():
            client_name = clients.get(o["client_id"], {}).get("name", o["client_id"])
            photos_count = len(o.get("photos", []))
            self.tv_orders.insert("", "end", values=(
                oid, o["date"], client_name,
                photos_count, o["status"],
                f"{o.get('total', 0):.2f}",
            ))

    def _create_order(self) -> None:
        clients = self.db.get_clients()
        if not clients:
            messagebox.showwarning("Нет клиентов", "Сначала добавьте клиента")
            return
        dlg = _OrderDialog(self, clients, self.db.get_price_list())
        if not dlg.result:
            return
        client_id, photos_data = dlg.result
        order_id = "О-" + str(uuid.uuid4())[:6].upper()
        today = datetime.now().strftime("%d.%m.%Y")
        photos = [Photo(str(i), pd["format"], pd["count"]) for i, pd in enumerate(photos_data)]
        order = Order(order_id, today, client_id, photos)
        order.calculate_cost(self.db.get_price_list())
        order_dict = {
            "date": today, "client_id": client_id,
            "photos": photos_data,
            "status": order.status,
            "total": order.total,
        }
        self.db.add_order(order_id, order_dict)
        self._refresh_orders()
        self._status(f"Заказ {order_id} создан, сумма: {order.total:.2f} руб.")

    def _change_order_status(self) -> None:
        sel = self.tv_orders.selection()
        if not sel:
            messagebox.showinfo("Выбор", "Выберите заказ")
            return
        oid = str(self.tv_orders.item(sel[0])["values"][0])
        STATUSES = ["Новый", "В обработке", "Готов", "Оплачен", "Выдан"]
        dlg = _ChoiceDialog(self, "Новый статус", "Выберите статус:", STATUSES)
        if not dlg.result:
            return
        orders = self.db.get_orders()
        if oid not in orders:
            return
        orders[oid]["status"] = dlg.result
        self.db.update_order(oid, orders[oid])
        self._refresh_orders()
        self._status(f"Статус заказа {oid} → {dlg.result}")

    # ══════════════════════════════════════════
    # SECTION — ПРАЙС-ЛИСТ
    # ══════════════════════════════════════════

    def _build_pricelist_section(self) -> tk.Frame:
        frame = tk.Frame(self.content, bg=C_BG)

        self._toolbar(frame, [
            ("+ Добавить формат",  C_PRIMARY, self._add_price),
            ("Редактировать цену", C_WARNING, self._edit_price),
            ("Удалить",            C_DANGER,  self._del_price),
        ])

        outer, inner = self._card(frame, "Прайс-лист")
        outer.pack(fill="both", expand=True)

        cols = ("Формат", "Цена, руб.")
        self.tv_prices = self._tree(inner, cols)
        self.tv_prices.column("Формат",     width=200)
        self.tv_prices.column("Цена, руб.", width=150)
        return frame

    def _refresh_pricelist(self) -> None:
        self.tv_prices.delete(*self.tv_prices.get_children())
        for fmt, price in self.db.get_price_list().items():
            self.tv_prices.insert("", "end", values=(fmt, f"{price:.2f}"))

    def _add_price(self) -> None:
        dlg = _FormDialog(self, "Новый формат", [
            ("Формат (напр. 13x18)*", "text"),
            ("Цена, руб.*",           "text"),
        ])
        if not dlg.result:
            return
        fmt, price_str = dlg.result
        if not fmt:
            return
        try:
            price = float(price_str.replace(",", "."))
            if price <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректную положительную цену")
            return
        self.db.set_price(fmt.strip(), price)
        self._refresh_pricelist()
        self._status(f"Добавлен формат {fmt}")

    def _edit_price(self) -> None:
        sel = self.tv_prices.selection()
        if not sel:
            messagebox.showinfo("Выбор", "Выберите строку")
            return
        fmt = self.tv_prices.item(sel[0])["values"][0]
        current = self.db.get_price_list().get(fmt, 0)
        new_str = simpledialog.askstring(
            "Редактировать цену",
            f"Новая цена для {fmt} (текущая: {current:.2f} руб.):",
            parent=self,
        )
        if not new_str:
            return
        try:
            new_price = float(new_str.replace(",", "."))
            if new_price <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректную цену")
            return
        admin = Administrator("A1", "Система")
        pl = PriceList(fmt, current)
        admin.edit_price(pl, new_price)
        self.db.set_price(fmt, pl.get_price())
        self._refresh_pricelist()
        self._status(f"Цена {fmt} обновлена → {new_price:.2f} руб.")

    def _del_price(self) -> None:
        sel = self.tv_prices.selection()
        if not sel:
            messagebox.showinfo("Выбор", "Выберите строку")
            return
        fmt = self.tv_prices.item(sel[0])["values"][0]
        if messagebox.askyesno("Подтверждение", f"Удалить формат «{fmt}»?"):
            self.db.delete_price(fmt)
            self._refresh_pricelist()
            self._status(f"Формат {fmt} удалён")

    # ══════════════════════════════════════════
    # SECTION — ОПЛАТА
    # ══════════════════════════════════════════

    def _build_payments_section(self) -> tk.Frame:
        frame = tk.Frame(self.content, bg=C_BG)

        self._toolbar(frame, [
            ("Принять оплату", C_SUCCESS, self._process_payment),
        ])

        outer, inner = self._card(frame, "История оплат")
        outer.pack(fill="both", expand=True)

        cols = ("№ платежа", "№ заказа", "Способ", "Сумма, руб.", "Статус")
        self.tv_payments = self._tree(inner, cols)
        self.tv_payments.column("№ платежа",   width=110)
        self.tv_payments.column("№ заказа",    width=110)
        self.tv_payments.column("Способ",      width=130)
        self.tv_payments.column("Сумма, руб.", width=110)
        self.tv_payments.column("Статус",      width=130)
        return frame

    def _refresh_payments(self) -> None:
        self.tv_payments.delete(*self.tv_payments.get_children())
        for pid, p in self.db.get_payments().items():
            self.tv_payments.insert("", "end", values=(
                pid, p["order_number"],
                p["payment_method"],
                f"{p['amount']:.2f}",
                p["status"],
            ))

    def _process_payment(self) -> None:
        orders = self.db.get_orders()
        unpaid = {
            oid: o for oid, o in orders.items()
            if o["status"] in ("Новый", "В обработке", "Готов")
        }
        if not unpaid:
            messagebox.showinfo("Нет заказов", "Нет заказов, ожидающих оплаты")
            return

        order_ids = list(unpaid.keys())
        dlg = _ChoiceDialog(self, "Оплата заказа", "Выберите заказ:", order_ids)
        if not dlg.result:
            return
        oid = dlg.result
        amount = unpaid[oid].get("total", 0)

        METHODS = ["Наличные", "Банковская карта", "Оплата онлайн"]
        dlg2 = _ChoiceDialog(self, "Способ оплаты", "Выберите способ:", METHODS)
        if not dlg2.result:
            return

        pid = "П-" + str(uuid.uuid4())[:6].upper()
        pay = Payment(pid, oid, dlg2.result, amount)
        pay.process()

        self.db.add_payment(pid, {
            "order_number":   oid,
            "payment_method": dlg2.result,
            "amount":         amount,
            "status":         pay.status,
        })
        orders[oid]["status"] = "Оплачен"
        self.db.update_order(oid, orders[oid])
        self._refresh_payments()
        self._status(f"Заказ {oid} оплачен. Чек: {pay.get_receipt()}")

    # ══════════════════════════════════════════
    # SECTION — ВЫДАЧА ЗАКАЗОВ
    # ══════════════════════════════════════════

    def _build_handout_section(self) -> tk.Frame:
        frame = tk.Frame(self.content, bg=C_BG)

        self._toolbar(frame, [
            ("Обновить список", C_PRIMARY, self._refresh_handout),
            ("Выдать заказ",    C_SUCCESS, self._hand_out),
        ])

        outer, inner = self._card(frame, "Оплаченные заказы — готовы к выдаче")
        outer.pack(fill="both", expand=True)

        cols = ("№ заказа", "Дата", "Клиент", "Сумма, руб.", "Статус")
        self.tv_handout = self._tree(inner, cols)
        self.tv_handout.column("№ заказа",    width=110)
        self.tv_handout.column("Дата",        width=110)
        self.tv_handout.column("Клиент",      width=180)
        self.tv_handout.column("Сумма, руб.", width=110)
        self.tv_handout.column("Статус",      width=110)
        return frame

    def _refresh_handout(self) -> None:
        self.tv_handout.delete(*self.tv_handout.get_children())
        clients = self.db.get_clients()
        for oid, o in self.db.get_orders().items():
            if o["status"] == "Оплачен":
                client_name = clients.get(o["client_id"], {}).get("name", o["client_id"])
                self.tv_handout.insert("", "end", values=(
                    oid, o["date"], client_name,
                    f"{o.get('total', 0):.2f}", o["status"],
                ))

    def _hand_out(self) -> None:
        sel = self.tv_handout.selection()
        if not sel:
            messagebox.showinfo("Выбор", "Выберите заказ для выдачи")
            return
        oid = str(self.tv_handout.item(sel[0])["values"][0])
        orders = self.db.get_orders()
        if oid not in orders:
            return
        cashier = Cashier("K1", "Кассир")
        o = orders[oid]
        order_obj = Order(oid, o["date"], o["client_id"],
                          status=o["status"], total=o.get("total", 0))
        msg = cashier.hand_out_product(order_obj)
        orders[oid]["status"] = order_obj.status
        self.db.update_order(oid, orders[oid])
        self._refresh_handout()
        self._status(msg)
        messagebox.showinfo("Выдача", msg)


# ══════════════════════════════════════════════════════════════════════
# DIALOG — универсальная форма ввода
# ══════════════════════════════════════════════════════════════════════

class _FormDialog(tk.Toplevel):
    def __init__(self, parent, title: str, fields: list) -> None:
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result = None
        self._entries = []

        tk.Label(self, text=title, font=FONT_TITLE,
                 bg=C_WHITE, fg=C_TEXT, padx=20, pady=14).pack(fill="x")

        form = tk.Frame(self, bg=C_WHITE, padx=20, pady=10)
        form.pack(fill="x")

        for label, _ in fields:
            tk.Label(form, text=label, bg=C_WHITE,
                     font=FONT_BODY, anchor="w").pack(anchor="w", pady=(6, 0))
            e = tk.Entry(form, font=FONT_BODY, relief="solid", bd=1)
            e.pack(fill="x", ipady=4)
            self._entries.append(e)

        btn_row = tk.Frame(self, bg=C_WHITE, pady=14)
        btn_row.pack(fill="x")
        tk.Button(btn_row, text="Сохранить", bg=C_PRIMARY, fg=C_WHITE,
                  font=FONT_BODY, relief="flat", padx=20, pady=6,
                  cursor="hand2", command=self._ok).pack(side="right", padx=20)
        tk.Button(btn_row, text="Отмена", bg="#b2bec3", fg=C_WHITE,
                  font=FONT_BODY, relief="flat", padx=16, pady=6,
                  cursor="hand2", command=self.destroy).pack(side="right", padx=(0, 8))

        self.grab_set()
        self.transient(parent)
        self._entries[0].focus()
        self.wait_window()

    def _ok(self) -> None:
        self.result = [e.get().strip() for e in self._entries]
        self.destroy()


# ══════════════════════════════════════════════════════════════════════
# DIALOG — выбор из списка
# ══════════════════════════════════════════════════════════════════════

class _ChoiceDialog(tk.Toplevel):
    def __init__(self, parent, title: str, prompt: str, choices: list) -> None:
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.result = None

        tk.Label(self, text=title, font=FONT_TITLE,
                 bg=C_WHITE, fg=C_TEXT, padx=20, pady=14).pack(fill="x")
        tk.Label(self, text=prompt, bg=C_WHITE,
                 font=FONT_BODY, padx=20, anchor="w").pack(fill="x")

        self._var = tk.StringVar(value=choices[0])
        lb_frame = tk.Frame(self, bg=C_WHITE, padx=20, pady=8)
        lb_frame.pack(fill="both", expand=True)

        vsb = ttk.Scrollbar(lb_frame)
        vsb.pack(side="right", fill="y")
        lb = tk.Listbox(lb_frame, yscrollcommand=vsb.set,
                        font=FONT_BODY, relief="solid", bd=1,
                        selectmode="single", height=min(8, len(choices)))
        vsb.config(command=lb.yview)
        for c in choices:
            lb.insert("end", c)
        lb.select_set(0)
        lb.pack(fill="both", expand=True)
        self._lb = lb

        btn_row = tk.Frame(self, bg=C_WHITE, pady=12)
        btn_row.pack(fill="x")
        tk.Button(btn_row, text="Выбрать", bg=C_PRIMARY, fg=C_WHITE,
                  font=FONT_BODY, relief="flat", padx=20, pady=6,
                  cursor="hand2", command=self._ok).pack(side="right", padx=20)
        tk.Button(btn_row, text="Отмена", bg="#b2bec3", fg=C_WHITE,
                  font=FONT_BODY, relief="flat", padx=16, pady=6,
                  cursor="hand2", command=self.destroy).pack(side="right", padx=(0, 8))

        self.grab_set()
        self.transient(parent)
        self.wait_window()

    def _ok(self) -> None:
        sel = self._lb.curselection()
        if sel:
            self.result = self._lb.get(sel[0])
        self.destroy()


# ══════════════════════════════════════════════════════════════════════
# DIALOG — создание заказа (выбор клиента + добавление фото)
# ══════════════════════════════════════════════════════════════════════

class _OrderDialog(tk.Toplevel):
    def __init__(self, parent, clients: dict, price_list: dict) -> None:
        super().__init__(parent)
        self.title("Создание заказа")
        self.geometry("520x540")
        self.resizable(False, False)
        self.result = None
        self._photos: list = []
        self._price_list = price_list

        bg = C_WHITE
        self.configure(bg=bg)

        # Header
        tk.Label(self, text="Создание заказа", font=FONT_TITLE,
                 bg=bg, fg=C_TEXT, padx=20, pady=14).pack(fill="x")

        body = tk.Frame(self, bg=bg, padx=20)
        body.pack(fill="both", expand=True)

        # Client choice
        tk.Label(body, text="Клиент:", bg=bg, font=FONT_HEAD, anchor="w").pack(anchor="w", pady=(0, 4))
        client_names = [f"{cid} — {c['name']}" for cid, c in clients.items()]
        self._client_ids = list(clients.keys())

        self._client_var = tk.StringVar(value=client_names[0])
        client_cb = ttk.Combobox(body, textvariable=self._client_var,
                                 values=client_names, state="readonly",
                                 font=FONT_BODY)
        client_cb.pack(fill="x", ipady=4)

        # Photo adding
        tk.Label(body, text="Добавить позицию:", bg=bg,
                 font=FONT_HEAD, anchor="w").pack(anchor="w", pady=(14, 4))

        photo_row = tk.Frame(body, bg=bg)
        photo_row.pack(fill="x")

        tk.Label(photo_row, text="Формат:", bg=bg, font=FONT_BODY).pack(side="left")
        self._fmt_var = tk.StringVar(
            value=list(price_list.keys())[0] if price_list else "")
        fmt_cb = ttk.Combobox(photo_row, textvariable=self._fmt_var,
                              values=list(price_list.keys()),
                              state="readonly", width=10, font=FONT_BODY)
        fmt_cb.pack(side="left", padx=(4, 16))

        tk.Label(photo_row, text="Кол-во:", bg=bg, font=FONT_BODY).pack(side="left")
        self._count_var = tk.StringVar(value="1")
        tk.Entry(photo_row, textvariable=self._count_var,
                 width=5, font=FONT_BODY, relief="solid", bd=1).pack(side="left", padx=4)

        tk.Button(photo_row, text="+ Добавить", bg=C_PRIMARY, fg=C_WHITE,
                  font=FONT_BODY, relief="flat", padx=10, pady=4,
                  cursor="hand2", command=self._add_photo).pack(side="left", padx=8)

        # Photo list
        tk.Label(body, text="Позиции заказа:", bg=bg,
                 font=FONT_HEAD, anchor="w").pack(anchor="w", pady=(10, 2))
        lf = tk.Frame(body, bg=bg)
        lf.pack(fill="both", expand=True)
        vsb = ttk.Scrollbar(lf)
        vsb.pack(side="right", fill="y")
        self._photo_lb = tk.Listbox(lf, yscrollcommand=vsb.set,
                                    font=FONT_BODY, relief="solid", bd=1, height=6)
        vsb.config(command=self._photo_lb.yview)
        self._photo_lb.pack(fill="both", expand=True)

        # Buttons
        btn_row = tk.Frame(self, bg=bg, pady=12)
        btn_row.pack(fill="x")
        tk.Button(btn_row, text="Создать заказ", bg=C_SUCCESS, fg=C_WHITE,
                  font=FONT_BODY, relief="flat", padx=18, pady=6,
                  cursor="hand2", command=self._ok).pack(side="right", padx=20)
        tk.Button(btn_row, text="Отмена", bg="#b2bec3", fg=C_WHITE,
                  font=FONT_BODY, relief="flat", padx=16, pady=6,
                  cursor="hand2", command=self.destroy).pack(side="right", padx=(0, 8))

        self.grab_set()
        self.transient(parent)
        self.wait_window()

    def _add_photo(self) -> None:
        fmt = self._fmt_var.get()
        try:
            count = int(self._count_var.get())
            if count <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректное количество копий", parent=self)
            return
        if not fmt:
            return
        price = self._price_list.get(fmt, 0)
        self._photos.append({"format": fmt, "count": count})
        self._photo_lb.insert(
            "end", f"{fmt}  ×{count}  = {price * count:.2f} руб."
        )

    def _ok(self) -> None:
        if not self._photos:
            messagebox.showwarning("Нет фото", "Добавьте хотя бы одну позицию", parent=self)
            return
        idx = [f.split(" — ")[0] for f in [self._client_var.get()]]
        client_id = idx[0] if idx else self._client_ids[0]
        self.result = (client_id, self._photos)
        self.destroy()

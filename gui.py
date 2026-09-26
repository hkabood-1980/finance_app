# gui.py
"""رابط گرافیکی برنامه مدیریت مالی — نسخه‌ی مدرن با CustomTkinter"""

import customtkinter as ctk
from tkinter import ttk, messagebox, scrolledtext
from datetime import datetime
import os

# تنظیم ظاهر اولیه
from theme import (
    setup_appearance, toggle_appearance,
    FONT_TITLE, FONT_SUBTITLE, FONT_HEADING, FONT_BODY,
    FONT_SMALL, FONT_BUTTON,
    COLOR_PRIMARY, COLOR_PRIMARY_HOVER,
    COLOR_SUCCESS, COLOR_SUCCESS_HOVER,
    COLOR_DANGER, COLOR_DANGER_HOVER,
    COLOR_WARNING, COLOR_WARNING_HOVER,
    COLOR_INFO, COLOR_INFO_HOVER,
    COLOR_PINK, COLOR_CYAN, COLOR_INDIGO,
    WINDOW_WIDTH, WINDOW_HEIGHT,
    BUTTON_WIDTH, BUTTON_HEIGHT, BUTTON_CORNER,
)

setup_appearance()

from database import (
    create_tables,
    add_account, load_accounts,
    get_transaction_by_id, update_transaction,
    get_account_by_id, update_account,
    delete_account as db_delete_account,
    get_connection,
)
from models import BankCard, FinanceManager
from services import (
    register_transaction,
    register_transfer,
    register_saving,
    show_financial_summary,
    show_transaction_report,
    show_category_report,
    search_date,
    search_by_date_range,
    search_by_type,
    search_by_description,
    set_savings_account,
    get_savings_account_id,
    get_transaction_sides,
    apply_transaction_edit,
    delete_transaction_with_revert,
)
from charts import (
    show_monthly_chart,
    show_yearly_chart,
    show_category_chart,
)
from backup import (
    create_backup,
    list_backups,
    restore_backup,
    delete_backup,
    get_backup_count,
    get_database_size,
    should_auto_backup,
)


# ✅ ساخت جدول‌ها قبل از هر چیز
create_tables()

# ✅ پشتیبان خودکار
if should_auto_backup():
    create_backup()

manager = FinanceManager()
manager.reload_from_db()


def refresh_manager():
    """بازخوانی کارت‌ها از دیتابیس"""
    manager.reload_from_db()


# =====================================================
# پنجره‌ی اصلی — ساخت
# =====================================================

window = ctk.CTk()
window.title("💰 برنامه مدیریت مالی")
window.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
window.resizable(False, False)


# =====================================================
# توابع کمکی
# =====================================================

def make_field(parent, label, placeholder=""):
    """ساخت یک فیلد ورودی با برچسب"""
    ctk.CTkLabel(parent, text=label, font=("Tahoma", 12, "bold"),
                 anchor="e").pack(fill="x", pady=(8, 3))
    entry = ctk.CTkEntry(parent, height=40, corner_radius=10,
                         font=("Tahoma", 12),
                         placeholder_text=placeholder)
    entry.pack(fill="x")
    return entry


def make_header(parent, title, color):
    """ساخت هدر رنگی برای پنجره"""
    header = ctk.CTkFrame(parent, height=60, corner_radius=0,
                            fg_color=color)
    header.pack(fill="x")
    header.pack_propagate(False)
    ctk.CTkLabel(header, text=title, font=("Tahoma", 18, "bold"),
                 text_color="white").pack(pady=15)
    return header


def make_buttons(parent, save_command, close_command,
                 save_text="✅  ثبت"):
    """ساخت دکمه‌های ذخیره و انصراف"""
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(pady=20)

    ctk.CTkButton(frame, text=save_text,
                  width=140, height=45, corner_radius=10,
                  font=("Tahoma", 13, "bold"),
                  fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER,
                  command=save_command).pack(side="right", padx=5)

    ctk.CTkButton(frame, text="❌  انصراف",
                  width=140, height=45, corner_radius=10,
                  font=("Tahoma", 13, "bold"),
                  fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER,
                  command=close_command).pack(side="left", padx=5)


def open_result_window(parent, title, geometry="850x550"):
    """باز کردن پنجره‌ی نتیجه که همیشه جلو بیاید"""
    rw = ctk.CTkToplevel(parent)
    rw.title(title)
    rw.geometry(geometry)
    rw.transient(parent)

    rw.lift()
    rw.focus_force()
    rw.attributes("-topmost", True)
    rw.after(1000, lambda: rw.attributes("-topmost", False))

    return rw


# =====================================================
# ثبت کارت بانکی
# =====================================================

def open_add_card():
    card_window = ctk.CTkToplevel(window)
    card_window.title("ثبت کارت بانکی")
    card_window.geometry("500x620")
    card_window.resizable(False, False)
    card_window.transient(window)
    card_window.grab_set()

    make_header(card_window, "💳  ثبت کارت بانکی", COLOR_PRIMARY)

    form = ctk.CTkFrame(card_window, fg_color="transparent")
    form.pack(pady=20, padx=30, fill="both", expand=True)

    name_entry = make_field(form, "نام حساب", "مثلاً: حساب اصلی")
    bank_entry = make_field(form, "نام بانک", "مثلاً: ملت")
    card_entry = make_field(form, "شماره کارت", "16 رقم")
    balance_entry = make_field(form, "موجودی اولیه", "0")
    account_type_entry = make_field(form, "نوع حساب", "جاری / پس‌انداز")

    def save_card():
        name = name_entry.get().strip()
        bank = bank_entry.get().strip()
        card_number = card_entry.get().strip()
        balance = balance_entry.get().strip()
        account_type = account_type_entry.get().strip()

        if not name:
            messagebox.showerror("خطا", "نام حساب را وارد کنید.")
            return
        if not bank:
            messagebox.showerror("خطا", "نام بانک را وارد کنید.")
            return
        if not card_number:
            messagebox.showerror("خطا", "شماره کارت را وارد کنید.")
            return

        try:
            balance = float(balance) if balance else 0
        except ValueError:
            messagebox.showerror("خطا", "موجودی باید عدد باشد.")
            return

        account_id = add_account(name, bank, card_number, balance, account_type)
        card = BankCard(
            name=name, balance=balance, bank=bank,
            card_number=card_number,
            account_type=account_type, account_id=account_id
        )
        manager.add_card(card)
        messagebox.showinfo("موفق", "✅ کارت با موفقیت ثبت شد.")
        card_window.destroy()
        open_home()

    make_buttons(card_window, save_card, card_window.destroy)


# =====================================================
# ثبت درآمد
# =====================================================

def open_income():
    if not manager.cards:
        messagebox.showwarning("توجه", "ابتدا یک کارت ثبت کنید.")
        return

    income_window = ctk.CTkToplevel(window)
    income_window.title("ثبت درآمد")
    income_window.geometry("500x620")
    income_window.resizable(False, False)
    income_window.transient(window)
    income_window.grab_set()

    make_header(income_window, "💵  ثبت درآمد", COLOR_SUCCESS)

    form = ctk.CTkFrame(income_window, fg_color="transparent")
    form.pack(pady=20, padx=30, fill="both", expand=True)

    ctk.CTkLabel(form, text="انتخاب کارت", font=("Tahoma", 12, "bold"),
                 anchor="e").pack(fill="x", pady=(8, 3))
    card_var = ctk.StringVar(value=manager.cards[0].name if manager.cards else "")
    ctk.CTkOptionMenu(form, values=[c.name for c in manager.cards],
                      variable=card_var, height=40, corner_radius=10,
                      font=("Tahoma", 12),
                      fg_color=COLOR_PRIMARY,
                      button_color=COLOR_PRIMARY_HOVER).pack(fill="x")

    amount_entry = make_field(form, "مبلغ درآمد", "0")
    category_entry = make_field(form, "دسته‌بندی", "حقوق / هدیه / ...")
    place_entry = make_field(form, "محل", "شرکت / خانه / ...")
    description_entry = make_field(form, "توضیحات", "اختیاری")

    def save_income():
        selected_name = card_var.get()
        if not selected_name:
            messagebox.showerror("خطا", "یک کارت انتخاب کنید.")
            return

        selected_card = next(
            (c for c in manager.cards if c.name == selected_name), None
        )
        if selected_card is None:
            messagebox.showerror("خطا", "کارت پیدا نشد.")
            return

        try:
            amount = float(amount_entry.get().strip())
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("خطا", "مبلغ باید عددی بزرگ‌تر از صفر باشد.")
            return

        category = category_entry.get().strip()
        place = place_entry.get().strip()
        description = description_entry.get().strip()
        date = datetime.now().strftime("%Y-%m-%d %H:%M")

        try:
            register_transaction(selected_card.id, date, "درآمد",
                                 category, amount, place, description)
        except ValueError as error:
            messagebox.showerror("خطا", str(error))
            return

        refresh_manager()
        messagebox.showinfo("موفق", "✅ درآمد با موفقیت ثبت شد.")
        income_window.destroy()
        open_home()

    make_buttons(income_window, save_income, income_window.destroy)


# =====================================================
# ثبت هزینه
# =====================================================

def open_expense():
    if not manager.cards:
        messagebox.showwarning("توجه", "ابتدا یک کارت ثبت کنید.")
        return

    expense_window = ctk.CTkToplevel(window)
    expense_window.title("ثبت هزینه")
    expense_window.geometry("500x620")
    expense_window.resizable(False, False)
    expense_window.transient(window)
    expense_window.grab_set()

    make_header(expense_window, "💸  ثبت هزینه", COLOR_DANGER)

    form = ctk.CTkFrame(expense_window, fg_color="transparent")
    form.pack(pady=20, padx=30, fill="both", expand=True)

    ctk.CTkLabel(form, text="انتخاب کارت", font=("Tahoma", 12, "bold"),
                 anchor="e").pack(fill="x", pady=(8, 3))
    card_var = ctk.StringVar(value=manager.cards[0].name if manager.cards else "")
    ctk.CTkOptionMenu(form, values=[c.name for c in manager.cards],
                      variable=card_var, height=40, corner_radius=10,
                      font=("Tahoma", 12),
                      fg_color=COLOR_DANGER,
                      button_color=COLOR_DANGER_HOVER).pack(fill="x")

    amount_entry = make_field(form, "مبلغ هزینه", "0")
    category_entry = make_field(form, "دسته‌بندی", "غذا / حمل‌ونقل / ...")
    place_entry = make_field(form, "محل", "رستوران / فروشگاه / ...")
    description_entry = make_field(form, "توضیحات", "اختیاری")

    def save_expense():
        selected_name = card_var.get()
        if not selected_name:
            messagebox.showerror("خطا", "یک کارت انتخاب کنید.")
            return

        selected_card = next(
            (c for c in manager.cards if c.name == selected_name), None
        )
        if selected_card is None:
            messagebox.showerror("خطا", "کارت پیدا نشد.")
            return

        try:
            amount = float(amount_entry.get().strip())
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("خطا", "مبلغ باید عددی بزرگ‌تر از صفر باشد.")
            return

        category = category_entry.get().strip()
        place = place_entry.get().strip()
        description = description_entry.get().strip()
        date = datetime.now().strftime("%Y-%m-%d %H:%M")

        try:
            register_transaction(selected_card.id, date, "هزینه",
                                 category, amount, place, description)
        except ValueError as error:
            messagebox.showerror("خطا", str(error))
            return

        refresh_manager()
        messagebox.showinfo("موفق", "✅ هزینه با موفقیت ثبت شد.")
        expense_window.destroy()
        open_home()

    make_buttons(expense_window, save_expense, expense_window.destroy)


# =====================================================
# انتقال
# =====================================================

def open_transfer():
    if len(manager.cards) < 2:
        messagebox.showwarning("توجه", "برای انتقال حداقل دو کارت لازم است.")
        return

    transfer_window = ctk.CTkToplevel(window)
    transfer_window.title("انتقال بین کارت‌ها")
    transfer_window.geometry("500x580")
    transfer_window.resizable(False, False)
    transfer_window.transient(window)
    transfer_window.grab_set()

    make_header(transfer_window, "🔁  انتقال بین کارت‌ها", COLOR_WARNING)

    form = ctk.CTkFrame(transfer_window, fg_color="transparent")
    form.pack(pady=20, padx=30, fill="both", expand=True)

    card_names = [c.name for c in manager.cards]

    ctk.CTkLabel(form, text="کارت مبدأ", font=("Tahoma", 12, "bold"),
                 anchor="e").pack(fill="x", pady=(8, 3))
    source_var = ctk.StringVar(value=card_names[0])
    ctk.CTkOptionMenu(form, values=card_names, variable=source_var,
                      height=40, corner_radius=10, font=("Tahoma", 12),
                      fg_color=COLOR_PRIMARY,
                      button_color=COLOR_PRIMARY_HOVER).pack(fill="x")

    ctk.CTkLabel(form, text="کارت مقصد", font=("Tahoma", 12, "bold"),
                 anchor="e").pack(fill="x", pady=(8, 3))
    dest_var = ctk.StringVar(value=card_names[1])
    ctk.CTkOptionMenu(form, values=card_names, variable=dest_var,
                      height=40, corner_radius=10, font=("Tahoma", 12),
                      fg_color=COLOR_INFO,
                      button_color=COLOR_INFO_HOVER).pack(fill="x")

    amount_entry = make_field(form, "مبلغ انتقال", "0")
    description_entry = make_field(form, "توضیحات", "اختیاری")

    def save_transfer():
        source_name = source_var.get()
        destination_name = dest_var.get()

        if source_name == destination_name:
            messagebox.showerror("خطا", "مبدأ و مقصد یکسان است.")
            return

        source_card = next((c for c in manager.cards if c.name == source_name), None)
        destination_card = next((c for c in manager.cards if c.name == destination_name), None)

        if source_card is None or destination_card is None:
            messagebox.showerror("خطا", "کارت پیدا نشد.")
            return

        try:
            amount = float(amount_entry.get().strip())
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("خطا", "مبلغ باید عددی بزرگ‌تر از صفر باشد.")
            return

        description = description_entry.get().strip()
        date = datetime.now().strftime("%Y-%m-%d %H:%M")

        try:
            register_transfer(source_card.id, destination_card.id,
                              date, amount, description)
        except ValueError as error:
            messagebox.showerror("خطا", str(error))
            return

        refresh_manager()
        messagebox.showinfo("موفق", "✅ انتقال با موفقیت انجام شد.")
        transfer_window.destroy()
        open_home()

    make_buttons(transfer_window, save_transfer, transfer_window.destroy,
                 save_text="✅  انتقال")


# =====================================================
# پس‌انداز
# =====================================================

def open_savings_menu():
    savings_window = ctk.CTkToplevel(window)
    savings_window.title("پس‌انداز")
    savings_window.geometry("450x380")
    savings_window.resizable(False, False)
    savings_window.transient(window)
    savings_window.grab_set()

    make_header(savings_window, "🐷  پس‌انداز", COLOR_PINK)

    frame = ctk.CTkFrame(savings_window, fg_color="transparent")
    frame.pack(pady=40, padx=30, fill="both", expand=True)

    ctk.CTkButton(frame, text="💰  ثبت پس‌انداز",
                  width=280, height=50, corner_radius=12,
                  font=("Tahoma", 13, "bold"),
                  fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER,
                  command=open_saving).pack(pady=10)

    ctk.CTkButton(frame, text="⚙️  تعیین/تغییر حساب پس‌انداز",
                  width=280, height=50, corner_radius=12,
                  font=("Tahoma", 13, "bold"),
                  fg_color=COLOR_WARNING, hover_color=COLOR_WARNING_HOVER,
                  command=open_set_savings_account).pack(pady=10)

    ctk.CTkButton(frame, text="❌  بستن",
                  width=280, height=45, corner_radius=12,
                  font=("Tahoma", 13, "bold"),
                  fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER,
                  command=savings_window.destroy).pack(pady=20)


def open_set_savings_account():
    if not manager.cards:
        messagebox.showinfo("حساب پس‌انداز", "ابتدا یک کارت ثبت کنید.")
        return

    set_window = ctk.CTkToplevel(window)
    set_window.title("تعیین حساب پس‌انداز")
    set_window.geometry("480x420")
    set_window.resizable(False, False)
    set_window.transient(window)
    set_window.grab_set()

    make_header(set_window, "⚙️  تعیین حساب پس‌انداز", COLOR_WARNING)

    form = ctk.CTkFrame(set_window, fg_color="transparent")
    form.pack(pady=20, padx=30, fill="both", expand=True)

    current_id = get_savings_account_id()
    current_name = "تعیین نشده"
    for c in manager.cards:
        if c.id == current_id:
            current_name = c.name
            break

    ctk.CTkLabel(form, text=f"حساب پس‌انداز فعلی: {current_name}",
                 font=("Tahoma", 12, "bold"),
                 text_color=COLOR_INFO).pack(pady=15)

    ctk.CTkLabel(form, text="انتخاب حساب جدید:", font=("Tahoma", 12, "bold"),
                 anchor="e").pack(fill="x", pady=(8, 3))
    card_var = ctk.StringVar()
    ctk.CTkOptionMenu(form, values=[c.name for c in manager.cards],
                      variable=card_var, height=40, corner_radius=10,
                      font=("Tahoma", 12),
                      fg_color=COLOR_PRIMARY,
                      button_color=COLOR_PRIMARY_HOVER).pack(fill="x")

    def save_choice():
        selected_name = card_var.get()
        if not selected_name:
            messagebox.showerror("خطا", "یک حساب انتخاب کنید.")
            return

        selected_card = next((c for c in manager.cards if c.name == selected_name), None)
        if selected_card is None:
            messagebox.showerror("خطا", "حساب پیدا نشد.")
            return

        try:
            set_savings_account(selected_card.id)
        except ValueError as error:
            messagebox.showerror("خطا", str(error))
            return

        messagebox.showinfo("موفق", "✅ حساب پس‌انداز تعیین شد.")
        set_window.destroy()

    make_buttons(set_window, save_choice, set_window.destroy,
                 save_text="✅  ذخیره")


def open_saving():
    savings_account_id = get_savings_account_id()

    if savings_account_id is None:
        messagebox.showwarning("حساب پس‌انداز تعیین نشده",
                               "ابتدا باید یک حساب پس‌انداز تعیین کنید.")
        open_set_savings_account()
        return

    savings_card = next((c for c in manager.cards if c.id == savings_account_id), None)
    if savings_card is None:
        messagebox.showerror("خطا", "حساب پس‌انداز پیدا نشد.")
        return

    source_names = [c.name for c in manager.cards if c.id != savings_account_id]
    if not source_names:
        messagebox.showerror("خطا", "به حداقل یک حساب مبدأ دیگر نیاز است.")
        return

    saving_window = ctk.CTkToplevel(window)
    saving_window.title("ثبت پس‌انداز")
    saving_window.geometry("500x640")
    saving_window.resizable(False, False)
    saving_window.transient(window)
    saving_window.grab_set()

    make_header(saving_window, "💰  ثبت پس‌انداز", COLOR_PINK)

    form = ctk.CTkFrame(saving_window, fg_color="transparent")
    form.pack(pady=20, padx=30, fill="both", expand=True)

    ctk.CTkLabel(form, text=f"🎯 حساب پس‌انداز: {savings_card.name}",
                 font=("Tahoma", 12, "bold"),
                 text_color=COLOR_INFO).pack(pady=10)

    ctk.CTkLabel(form, text="کارت مبدأ", font=("Tahoma", 12, "bold"),
                 anchor="e").pack(fill="x", pady=(8, 3))
    source_var = ctk.StringVar(value=source_names[0])
    ctk.CTkOptionMenu(form, values=source_names, variable=source_var,
                      height=40, corner_radius=10, font=("Tahoma", 12),
                      fg_color=COLOR_PRIMARY,
                      button_color=COLOR_PRIMARY_HOVER).pack(fill="x")

    amount_entry = make_field(form, "مبلغ پس‌انداز", "0")
    category_entry = make_field(form, "دسته‌بندی", "پس‌انداز ماهانه / ...")
    place_entry = make_field(form, "محل", "اختیاری")
    description_entry = make_field(form, "توضیحات", "اختیاری")

    def save_saving():
        source_name = source_var.get()
        if not source_name:
            messagebox.showerror("خطا", "کارت مبدأ را انتخاب کنید.")
            return

        source_card = next((c for c in manager.cards if c.name == source_name), None)
        if source_card is None:
            messagebox.showerror("خطا", "کارت پیدا نشد.")
            return

        try:
            amount = float(amount_entry.get().strip())
            if amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("خطا", "مبلغ باید عددی بزرگ‌تر از صفر باشد.")
            return

        category = category_entry.get().strip()
        place = place_entry.get().strip()
        description = description_entry.get().strip()
        date = datetime.now().strftime("%Y-%m-%d %H:%M")

        try:
            register_saving(account_id=source_card.id, amount=amount,
                            category=category, place=place,
                            description=description, date=date)
        except ValueError as error:
            messagebox.showerror("خطا", str(error))
            return

        refresh_manager()
        messagebox.showinfo("موفق", "✅ پس‌انداز با موفقیت ثبت شد.")
        saving_window.destroy()
        open_home()

    make_buttons(saving_window, save_saving, saving_window.destroy)


# =====================================================
# نمایش حساب‌ها
# =====================================================

def open_accounts():
    accounts_window = ctk.CTkToplevel(window)
    accounts_window.title("حساب‌های بانکی")
    accounts_window.geometry("900x550")
    accounts_window.resizable(False, False)
    accounts_window.transient(window)

    make_header(accounts_window, "📋  حساب‌های بانکی", COLOR_INFO)

    if not manager.cards:
        ctk.CTkLabel(accounts_window, text="هنوز هیچ حسابی ثبت نشده است.",
                     font=("Tahoma", 14)).pack(pady=80)
        ctk.CTkButton(accounts_window, text="❌  بستن",
                      width=150, height=45, corner_radius=10,
                      font=("Tahoma", 13, "bold"),
                      fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER,
                      command=accounts_window.destroy).pack(pady=20)
        return

    scroll_frame = ctk.CTkScrollableFrame(accounts_window, corner_radius=10)
    scroll_frame.pack(pady=15, padx=20, fill="both", expand=True)

    for card in manager.cards:
        card_frame = ctk.CTkFrame(scroll_frame, corner_radius=12,
                                   fg_color=("#E0F2FE", "#1E3A5F"))
        card_frame.pack(fill="x", pady=8, padx=5)

        info = ctk.CTkFrame(card_frame, fg_color="transparent")
        info.pack(side="right", fill="x", expand=True, padx=15, pady=10)

        ctk.CTkLabel(info, text=f"💳  {card.name}",
                     font=("Tahoma", 14, "bold"),
                     anchor="e").pack(fill="x")
        ctk.CTkLabel(info,
                     text=f"🏦 {card.bank}  |  💳 {card.card_number}  |  📁 {card.account_type}",
                     font=("Tahoma", 11),
                     anchor="e").pack(fill="x", pady=2)
        ctk.CTkLabel(info,
                     text=f"💰 موجودی: {card.balance:,.0f} تومان",
                     font=("Tahoma", 13, "bold"),
                     text_color=COLOR_SUCCESS,
                     anchor="e").pack(fill="x", pady=2)

        btn_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
        btn_frame.pack(side="left", padx=10)

        ctk.CTkButton(btn_frame, text="✏️ ویرایش",
                      width=90, height=40, corner_radius=8,
                      font=("Tahoma", 11, "bold"),
                      fg_color=COLOR_WARNING, hover_color=COLOR_WARNING_HOVER,
                      command=lambda c=card: edit_account(c)).pack(pady=3)

        ctk.CTkButton(btn_frame, text="🗑️ حذف",
                      width=90, height=40, corner_radius=8,
                      font=("Tahoma", 11, "bold"),
                      fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER,
                      command=lambda c=card: delete_account_gui(c)).pack(pady=3)


def edit_account(card):
    edit_window = ctk.CTkToplevel(window)
    edit_window.title("ویرایش حساب")
    edit_window.geometry("500x550")
    edit_window.resizable(False, False)
    edit_window.transient(window)
    edit_window.grab_set()

    make_header(edit_window, "✏️  ویرایش حساب", COLOR_WARNING)

    form = ctk.CTkFrame(edit_window, fg_color="transparent")
    form.pack(pady=20, padx=30, fill="both", expand=True)

    name_entry = make_field(form, "نام حساب")
    name_entry.insert(0, card.name)

    bank_entry = make_field(form, "نام بانک")
    bank_entry.insert(0, card.bank)

    card_entry = make_field(form, "شماره کارت")
    card_entry.insert(0, card.card_number)

    account_type_entry = make_field(form, "نوع حساب")
    account_type_entry.insert(0, card.account_type)

    def save_changes():
        name = name_entry.get().strip()
        bank = bank_entry.get().strip()
        card_number = card_entry.get().strip()
        account_type = account_type_entry.get().strip()

        if not name or not bank or not card_number:
            messagebox.showerror("خطا", "همه فیلدها را پر کنید.")
            return

        update_account(card.id, name, bank, card_number,
                       card.balance, account_type)

        card.name = name
        card.bank = bank
        card.card_number = card_number
        card.account_type = account_type

        messagebox.showinfo("موفق", "✅ اطلاعات حساب ویرایش شد.")
        edit_window.destroy()
        open_home()

    make_buttons(edit_window, save_changes, edit_window.destroy,
                 save_text="✅  ذخیره")


def delete_account_gui(card):
    answer = messagebox.askyesno(
        "حذف حساب",
        f"آیا مطمئن هستید که می‌خواهید حساب «{card.name}» حذف شود؟"
    )
    if not answer:
        return

    result = db_delete_account(card.id)
    if result is False:
        messagebox.showwarning("امکان حذف وجود ندارد",
                               "این حساب دارای تراکنش است.")
        return

    manager.cards = [c for c in manager.cards if c.id != card.id]
    messagebox.showinfo("موفق", "✅ حساب با موفقیت حذف شد.")
    open_home()


# =====================================================
# خلاصه مالی
# =====================================================

def show_financial_summary_gui():
    total_income, total_expense = show_financial_summary()
    balance = total_income - total_expense

    summary_window = ctk.CTkToplevel(window)
    summary_window.title("خلاصه مالی")
    summary_window.geometry("550x480")
    summary_window.resizable(False, False)
    summary_window.transient(window)
    summary_window.grab_set()

    make_header(summary_window, "📊  خلاصه مالی", COLOR_INFO)

    frame = ctk.CTkFrame(summary_window, fg_color="transparent")
    frame.pack(pady=30, padx=30, fill="both", expand=True)

    rows = [
        ("💵 مجموع درآمدها", f"{total_income:,.0f} تومان", COLOR_SUCCESS),
        ("💸 مجموع هزینه‌ها", f"{total_expense:,.0f} تومان", COLOR_DANGER),
        ("💰 مانده", f"{balance:,.0f} تومان", COLOR_INFO),
    ]

    for label, value, color in rows:
        row_frame = ctk.CTkFrame(frame, corner_radius=12, fg_color=color)
        row_frame.pack(fill="x", pady=8)

        ctk.CTkLabel(row_frame, text=label, font=("Tahoma", 13, "bold"),
                     text_color="white", anchor="e").pack(side="right",
                                                          padx=15, pady=12)
        ctk.CTkLabel(row_frame, text=value, font=("Tahoma", 14, "bold"),
                     text_color="white").pack(side="left", padx=15, pady=12)

    ctk.CTkButton(summary_window, text="❌  بستن",
                  width=150, height=45, corner_radius=10,
                  font=("Tahoma", 13, "bold"),
                  fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER,
                  command=summary_window.destroy).pack(pady=20)


# =====================================================
# گزارش همه تراکنش‌ها
# =====================================================

def show_all_transactions():
    transactions = show_transaction_report()
    if not transactions:
        messagebox.showinfo("گزارش تراکنش‌ها", "هیچ تراکنشی ثبت نشده است.")
        return

    report_window = ctk.CTkToplevel(window)
    report_window.title("گزارش همه تراکنش‌ها")
    report_window.geometry("1200x650")
    report_window.transient(window)

    make_header(report_window, "📋  گزارش همه تراکنش‌ها", COLOR_INFO)

    table_frame = ctk.CTkFrame(report_window, corner_radius=10)
    table_frame.pack(fill="both", expand=True, padx=15, pady=15)

    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Treeview",
                    font=("Tahoma", 11),
                    rowheight=30,
                    background="#F8FAFC",
                    fieldbackground="#F8FAFC")
    style.configure("Treeview.Heading",
                    font=("Tahoma", 11, "bold"),
                    background=COLOR_PRIMARY,
                    foreground="white")

    y_scroll = ttk.Scrollbar(table_frame, orient="vertical")
    y_scroll.pack(side="right", fill="y")
    x_scroll = ttk.Scrollbar(table_frame, orient="horizontal")
    x_scroll.pack(side="bottom", fill="x")

    columns = ("id", "account", "bank", "type", "category",
               "amount", "place", "description", "date")

    tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                        yscrollcommand=y_scroll.set,
                        xscrollcommand=x_scroll.set)
    y_scroll.config(command=tree.yview)
    x_scroll.config(command=tree.xview)
    tree.pack(fill="both", expand=True)

    headings = {"id": "شناسه", "account": "حساب", "bank": "بانک",
                "type": "نوع", "category": "دسته‌بندی", "amount": "مبلغ",
                "place": "محل", "description": "توضیحات", "date": "تاریخ"}
    for col, text in headings.items():
        tree.heading(col, text=text)

    widths = {"id": 60, "account": 120, "bank": 110, "type": 90,
              "category": 120, "amount": 130, "place": 120,
              "description": 200, "date": 140}
    for col, w in widths.items():
        tree.column(col, width=w, anchor="center")

    for t in transactions:
        tree.insert("", "end", values=(
            t[0], t[1], t[2], t[3], t[4],
            f"{t[5]:,.0f}", t[6], t[7], t[8]
        ))

    def edit_selected():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("توجه", "یک تراکنش انتخاب کنید.")
            return
        try:
            values = tree.item(selected[0])["values"]
            transaction_id = int(values[0])
            edit_transaction_gui(transaction_id)
        except (IndexError, ValueError) as e:
            messagebox.showerror("خطا", f"مشکل: {e}")

    def delete_selected():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("توجه", "یک تراکنش انتخاب کنید.")
            return

        try:
            values = tree.item(selected[0])["values"]
            if not values:
                return
            transaction_id = int(values[0])
        except (IndexError, ValueError) as e:
            messagebox.showerror("خطا", f"مشکل: {e}")
            return

        if not messagebox.askyesno(
            "تأیید حذف",
            f"آیا مطمئن هستید که می‌خواهید تراکنش شماره {transaction_id} حذف شود؟\n\n"
            "⚠️ موجودی حساب هم برگردانده می‌شود."
        ):
            return

        try:
            delete_transaction_with_revert(transaction_id)
        except ValueError as error:
            messagebox.showerror("خطا", str(error))
            return
        except Exception as error:
            messagebox.showerror("خطا", f"حذف انجام نشد: {error}")
            return

        refresh_manager()
        messagebox.showinfo("موفق", "✅ تراکنش حذف شد.")
        report_window.destroy()
        show_all_transactions()

    btn_frame = ctk.CTkFrame(report_window, fg_color="transparent")
    btn_frame.pack(pady=10)

    ctk.CTkButton(btn_frame, text="✏️  ویرایش",
                  width=150, height=45, corner_radius=10,
                  font=("Tahoma", 13, "bold"),
                  fg_color=COLOR_WARNING, hover_color=COLOR_WARNING_HOVER,
                  command=edit_selected).pack(side="right", padx=5)

    ctk.CTkButton(btn_frame, text="🗑️  حذف",
                  width=150, height=45, corner_radius=10,
                  font=("Tahoma", 13, "bold"),
                  fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER,
                  command=delete_selected).pack(side="right", padx=5)

    ctk.CTkButton(btn_frame, text="❌  بستن",
                  width=140, height=45, corner_radius=10,
                  font=("Tahoma", 13, "bold"),
                  fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER,
                  command=report_window.destroy).pack(side="left", padx=5)


# =====================================================
# ویرایش تراکنش
# =====================================================

def edit_transaction_gui(transaction_id):
    transaction = get_transaction_by_id(transaction_id)
    if transaction is None:
        messagebox.showerror("خطا", "تراکنش پیدا نشد.")
        return

    t_id, t_account_id, t_date, t_type, t_category, t_amount, t_place, t_desc = transaction

    origin_account_id, dest_account_id = get_transaction_sides(t_id)
    if origin_account_id is None:
        origin_account_id = t_account_id

    edit_window = ctk.CTkToplevel(window)
    edit_window.title("ویرایش تراکنش")
    edit_window.geometry("550x720")
    edit_window.resizable(False, False)
    edit_window.transient(window)
    edit_window.grab_set()

    make_header(edit_window, "✏️  ویرایش تراکنش", COLOR_WARNING)

    form = ctk.CTkFrame(edit_window, fg_color="transparent")
    form.pack(pady=15, padx=30, fill="both", expand=True)

    origin_account = get_account_by_id(origin_account_id)
    origin_name = origin_account[1] if origin_account else "نامشخص"

    ctk.CTkLabel(form, text=f"شناسه: {t_id}  |  حساب: {origin_name}  |  تاریخ: {t_date}",
                 font=("Tahoma", 10),
                 text_color=COLOR_INFO).pack(pady=5)

    ctk.CTkLabel(form, text="نوع تراکنش:", font=("Tahoma", 12, "bold"),
                 anchor="e").pack(fill="x", pady=(8, 3))
    type_var = ctk.StringVar(value=t_type)
    ctk.CTkOptionMenu(form, values=["درآمد", "هزینه", "انتقال", "پس‌انداز"],
                      variable=type_var, height=40, corner_radius=10,
                      font=("Tahoma", 12),
                      fg_color=COLOR_PRIMARY,
                      button_color=COLOR_PRIMARY_HOVER).pack(fill="x")

    category_entry = make_field(form, "دسته‌بندی")
    category_entry.insert(0, t_category or "")

    amount_entry = make_field(form, "مبلغ")
    amount_entry.insert(0, str(t_amount))

    place_entry = make_field(form, "محل")
    place_entry.insert(0, t_place or "")

    description_entry = make_field(form, "توضیحات")
    description_entry.insert(0, t_desc or "")

    ctk.CTkLabel(form, text="حساب مقصد (فقط برای انتقال):",
                 font=("Tahoma", 11, "bold"),
                 text_color=COLOR_INFO, anchor="e").pack(fill="x", pady=(8, 3))

    dest_options = [c.name for c in manager.cards if c.id != origin_account_id]
    dest_var = ctk.StringVar(value="انتخاب کنید...")

    if dest_options:
        ctk.CTkOptionMenu(form, values=dest_options, variable=dest_var,
                          height=40, corner_radius=10, font=("Tahoma", 12),
                          fg_color=COLOR_INFO,
                          button_color=COLOR_INFO_HOVER).pack(fill="x")

    if dest_account_id is not None:
        for card in manager.cards:
            if card.id == dest_account_id:
                dest_var.set(card.name)
                break

    def save_changes():
        try:
            new_amount = float(amount_entry.get().strip())
            if new_amount <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("خطا", "مبلغ باید عددی بزرگ‌تر از صفر باشد.")
            return

        new_type = type_var.get()
        new_category = category_entry.get().strip()
        new_place = place_entry.get().strip()
        new_description = description_entry.get().strip()

        new_dest_account_id = None
        if new_type == "انتقال":
            dest_name = dest_var.get()
            if dest_name == "انتخاب کنید..." or not dest_name:
                messagebox.showerror("خطا", "حساب مقصد را انتخاب کنید.")
                return
            for card in manager.cards:
                if card.name == dest_name:
                    new_dest_account_id = card.id
                    break
            if new_dest_account_id is None:
                messagebox.showerror("خطا", "حساب مقصد پیدا نشد.")
                return

        try:
            apply_transaction_edit(t_id, new_type, new_category, new_amount,
                                   new_place, new_description, new_dest_account_id)
        except ValueError as error:
            messagebox.showerror("خطا", str(error))
            return
        except Exception as error:
            messagebox.showerror("خطا", f"ویرایش انجام نشد: {error}")
            return

        refresh_manager()
        messagebox.showinfo("موفق", "✅ تراکنش با موفقیت ویرایش شد.")
        edit_window.destroy()

    make_buttons(edit_window, save_changes, edit_window.destroy,
                 save_text="✅  ذخیره تغییرات")


# =====================================================
# گزارش تراکنش‌های یک حساب
# =====================================================

def show_account_transactions():
    if not manager.cards:
        messagebox.showinfo("گزارش حساب", "هنوز هیچ حسابی ثبت نشده است.")
        return

    account_window = ctk.CTkToplevel(window)
    account_window.title("گزارش یک حساب")
    account_window.geometry("500x300")
    account_window.resizable(False, False)
    account_window.transient(window)
    account_window.grab_set()

    make_header(account_window, "📊  گزارش یک حساب", COLOR_INDIGO)

    form = ctk.CTkFrame(account_window, fg_color="transparent")
    form.pack(pady=25, padx=30, fill="both", expand=True)

    ctk.CTkLabel(form, text="انتخاب حساب:", font=("Tahoma", 12, "bold"),
                 anchor="e").pack(fill="x", pady=(8, 3))
    card_var = ctk.StringVar()
    ctk.CTkOptionMenu(form, values=[c.name for c in manager.cards],
                      variable=card_var, height=40, corner_radius=10,
                      font=("Tahoma", 12),
                      fg_color=COLOR_PRIMARY,
                      button_color=COLOR_PRIMARY_HOVER).pack(fill="x")

    def show_report():
        selected_name = card_var.get()
        if not selected_name:
            messagebox.showerror("خطا", "یک حساب را انتخاب کنید.")
            return

        selected_card = next((c for c in manager.cards if c.name == selected_name), None)
        if selected_card is None:
            messagebox.showerror("خطا", "حساب پیدا نشد.")
            return

        transactions = get_transactions_by_account_local(selected_card.id)
        if not transactions:
            messagebox.showinfo("گزارش حساب", "تراکنشی ثبت نشده است.")
            return

        report_window = ctk.CTkToplevel(account_window)
        report_window.title(f"گزارش حساب {selected_card.name}")
        report_window.geometry("1100x600")
        report_window.transient(account_window)

        make_header(report_window, f"📊  گزارش حساب: {selected_card.name}", COLOR_INDIGO)

        table_frame = ctk.CTkFrame(report_window, corner_radius=10)
        table_frame.pack(fill="both", expand=True, padx=15, pady=15)

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical")
        y_scroll.pack(side="right", fill="y")
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal")
        x_scroll.pack(side="bottom", fill="x")

        columns = ("id", "date", "type", "category",
                   "amount", "place", "description")
        tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                            yscrollcommand=y_scroll.set,
                            xscrollcommand=x_scroll.set)
        y_scroll.config(command=tree.yview)
        x_scroll.config(command=tree.xview)
        tree.pack(fill="both", expand=True)

        for col, text in [
            ("id", "شناسه"), ("date", "تاریخ"), ("type", "نوع"),
            ("category", "دسته‌بندی"), ("amount", "مبلغ"),
            ("place", "محل"), ("description", "توضیحات")
        ]:
            tree.heading(col, text=text)

        for col, w in [
            ("id", 60), ("date", 140), ("type", 90),
            ("category", 120), ("amount", 130),
            ("place", 120), ("description", 250)
        ]:
            tree.column(col, width=w, anchor="center")

        for t in transactions:
            tree.insert("", "end", values=(
                t[0], t[2], t[3], t[4], f"{t[5]:,.0f}", t[6], t[7]
            ))

        def edit_selected():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("توجه", "یک تراکنش انتخاب کنید.")
                return
            try:
                values = tree.item(selected[0])["values"]
                if not values:
                    return
                transaction_id = int(values[0])
                edit_transaction_gui(transaction_id)
            except (IndexError, ValueError) as e:
                messagebox.showerror("خطا", f"مشکل: {e}")

        def delete_selected():
            selected = tree.selection()
            if not selected:
                messagebox.showwarning("توجه", "یک تراکنش انتخاب کنید.")
                return

            try:
                values = tree.item(selected[0])["values"]
                if not values:
                    return
                transaction_id = int(values[0])
            except (IndexError, ValueError) as e:
                messagebox.showerror("خطا", f"مشکل: {e}")
                return

            if not messagebox.askyesno(
                "تأیید حذف",
                f"تراکنش شماره {transaction_id} حذف شود؟"
            ):
                return

            try:
                delete_transaction_with_revert(transaction_id)
            except ValueError as error:
                messagebox.showerror("خطا", str(error))
                return
            except Exception as error:
                messagebox.showerror("خطا", f"حذف انجام نشد: {error}")
                return

            refresh_manager()
            messagebox.showinfo("موفق", "✅ حذف شد.")
            report_window.destroy()
            show_account_transactions()

        btn_frame = ctk.CTkFrame(report_window, fg_color="transparent")
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="✏️  ویرایش",
                      width=140, height=45, corner_radius=10,
                      font=("Tahoma", 13, "bold"),
                      fg_color=COLOR_WARNING, hover_color=COLOR_WARNING_HOVER,
                      command=edit_selected).pack(side="right", padx=5)

        ctk.CTkButton(btn_frame, text="🗑️  حذف",
                      width=140, height=45, corner_radius=10,
                      font=("Tahoma", 13, "bold"),
                      fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER,
                      command=delete_selected).pack(side="right", padx=5)

        ctk.CTkButton(btn_frame, text="❌  بستن",
                      width=140, height=45, corner_radius=10,
                      font=("Tahoma", 13, "bold"),
                      fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER,
                      command=report_window.destroy).pack(side="left", padx=5)

    make_buttons(account_window, show_report, account_window.destroy,
                 save_text="📊  نمایش گزارش")


def get_transactions_by_account_local(account_id):
    from database import get_transactions_by_account
    return get_transactions_by_account(account_id)


# =====================================================
# گزارش دسته‌بندی هزینه‌ها
# =====================================================

def show_category_report_gui():
    if not manager.cards:
        messagebox.showinfo("گزارش", "هنوز هیچ حسابی ثبت نشده است.")
        return

    category_window = ctk.CTkToplevel(window)
    category_window.title("گزارش دسته‌بندی هزینه‌ها")
    category_window.geometry("520x520")
    category_window.resizable(False, False)
    category_window.transient(window)
    category_window.grab_set()

    make_header(category_window, "📊  گزارش دسته‌بندی", COLOR_INDIGO)

    form = ctk.CTkFrame(category_window, fg_color="transparent")
    form.pack(pady=20, padx=30, fill="both", expand=True)

    ctk.CTkLabel(form, text="انتخاب حساب:", font=("Tahoma", 12, "bold"),
                 anchor="e").pack(fill="x", pady=(8, 3))
    card_var = ctk.StringVar()
    ctk.CTkOptionMenu(form, values=[c.name for c in manager.cards],
                      variable=card_var, height=40, corner_radius=10,
                      font=("Tahoma", 12),
                      fg_color=COLOR_PRIMARY,
                      button_color=COLOR_PRIMARY_HOVER).pack(fill="x")

    start_entry = make_field(form, "تاریخ شروع", "YYYY-MM-DD")
    start_entry.insert(0, "2020-01-01")

    end_entry = make_field(form, "تاریخ پایان", "YYYY-MM-DD")
    end_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

    def show_report():
        selected_name = card_var.get()
        if not selected_name:
            messagebox.showerror("خطا", "یک حساب انتخاب کنید.")
            return

        selected_card = next((c for c in manager.cards if c.name == selected_name), None)
        if selected_card is None:
            messagebox.showerror("خطا", "حساب پیدا نشد.")
            return

        start_date = start_entry.get().strip()
        end_date = end_entry.get().strip()

        if not start_date or not end_date:
            messagebox.showerror("خطا", "تاریخ‌ها را وارد کنید.")
            return
        if start_date > end_date:
            messagebox.showerror("خطا", "تاریخ شروع بعد از پایان است.")
            return

        result = show_category_report(selected_card.id, start_date, end_date)
        if not result:
            messagebox.showinfo("گزارش", "هزینه‌ای ثبت نشده است.")
            return

        report_window = ctk.CTkToplevel(category_window)
        report_window.title(f"دسته‌بندی - {selected_card.name}")
        report_window.geometry("550x600")
        report_window.transient(category_window)

        make_header(report_window, f"📊  {selected_card.name}", COLOR_INDIGO)

        scroll = ctk.CTkScrollableFrame(report_window, corner_radius=10)
        scroll.pack(fill="both", expand=True, padx=20, pady=20)

        for cat, total in result:
            row = ctk.CTkFrame(scroll, corner_radius=10,
                               fg_color=("#E0F2FE", "#1E3A5F"))
            row.pack(fill="x", pady=5)

            ctk.CTkLabel(row, text=cat, font=("Tahoma", 13, "bold"),
                         anchor="e").pack(side="right", padx=15, pady=10)
            ctk.CTkLabel(row, text=f"{total:,.0f} تومان",
                         font=("Tahoma", 13, "bold"),
                         text_color=COLOR_SUCCESS).pack(side="left",
                                                        padx=15, pady=10)

    make_buttons(category_window, show_report, category_window.destroy,
                 save_text="📊  نمایش گزارش")


# =====================================================
# نمودارها
# =====================================================

def show_monthly_chart_gui():
    if not manager.cards:
        messagebox.showinfo("نمودار", "هنوز هیچ حسابی ثبت نشده است.")
        return

    chart_window = ctk.CTkToplevel(window)
    chart_window.title("نمودار ماهانه")
    chart_window.geometry("500x420")
    chart_window.resizable(False, False)
    chart_window.transient(window)
    chart_window.grab_set()

    make_header(chart_window, "📈  نمودار ماهانه", COLOR_CYAN)

    form = ctk.CTkFrame(chart_window, fg_color="transparent")
    form.pack(pady=20, padx=30, fill="both", expand=True)

    ctk.CTkLabel(form, text="انتخاب حساب:", font=("Tahoma", 12, "bold"),
                 anchor="e").pack(fill="x", pady=(8, 3))
    card_var = ctk.StringVar()
    ctk.CTkOptionMenu(form, values=[c.name for c in manager.cards],
                      variable=card_var, height=40, corner_radius=10,
                      font=("Tahoma", 12),
                      fg_color=COLOR_PRIMARY,
                      button_color=COLOR_PRIMARY_HOVER).pack(fill="x")

    year_entry = make_field(form, "سال")
    year_entry.insert(0, str(datetime.now().year))

    month_entry = make_field(form, "ماه (1-12)")
    month_entry.insert(0, str(datetime.now().month))

    def show_chart():
        card_name = card_var.get()
        if not card_name:
            messagebox.showerror("خطا", "حساب را انتخاب کنید.")
            return
        try:
            year = int(year_entry.get())
            month = int(month_entry.get())
            if month < 1 or month > 12:
                raise ValueError
        except ValueError:
            messagebox.showerror("خطا", "سال و ماه را درست وارد کنید.")
            return

        card = next((c for c in manager.cards if c.name == card_name), None)
        if card:
            show_monthly_chart(card.id, card_name, year, month)

    make_buttons(chart_window, show_chart, chart_window.destroy,
                 save_text="📈  نمایش نمودار")


def show_yearly_chart_gui():
    if not manager.cards:
        messagebox.showinfo("نمودار", "هنوز هیچ حسابی ثبت نشده است.")
        return

    chart_window = ctk.CTkToplevel(window)
    chart_window.title("نمودار سالانه")
    chart_window.geometry("500x350")
    chart_window.resizable(False, False)
    chart_window.transient(window)
    chart_window.grab_set()

    make_header(chart_window, "📈  نمودار سالانه", COLOR_CYAN)

    form = ctk.CTkFrame(chart_window, fg_color="transparent")
    form.pack(pady=20, padx=30, fill="both", expand=True)

    ctk.CTkLabel(form, text="انتخاب حساب:", font=("Tahoma", 12, "bold"),
                 anchor="e").pack(fill="x", pady=(8, 3))
    card_var = ctk.StringVar()
    ctk.CTkOptionMenu(form, values=[c.name for c in manager.cards],
                      variable=card_var, height=40, corner_radius=10,
                      font=("Tahoma", 12),
                      fg_color=COLOR_PRIMARY,
                      button_color=COLOR_PRIMARY_HOVER).pack(fill="x")

    year_entry = make_field(form, "سال")
    year_entry.insert(0, str(datetime.now().year))

    def show_chart():
        card_name = card_var.get()
        if not card_name:
            messagebox.showerror("خطا", "حساب را انتخاب کنید.")
            return
        try:
            year = int(year_entry.get())
        except ValueError:
            messagebox.showerror("خطا", "سال را درست وارد کنید.")
            return

        card = next((c for c in manager.cards if c.name == card_name), None)
        if card:
            show_yearly_chart(card.id, card_name, year)

    make_buttons(chart_window, show_chart, chart_window.destroy,
                 save_text="📈  نمایش نمودار")


def show_category_chart_gui():
    if not manager.cards:
        messagebox.showinfo("نمودار", "هنوز هیچ حسابی ثبت نشده است.")
        return

    chart_window = ctk.CTkToplevel(window)
    chart_window.title("نمودار دسته‌بندی")
    chart_window.geometry("500x420")
    chart_window.resizable(False, False)
    chart_window.transient(window)
    chart_window.grab_set()

    make_header(chart_window, "📈  نمودار دسته‌بندی", COLOR_CYAN)

    form = ctk.CTkFrame(chart_window, fg_color="transparent")
    form.pack(pady=20, padx=30, fill="both", expand=True)

    ctk.CTkLabel(form, text="انتخاب حساب:", font=("Tahoma", 12, "bold"),
                 anchor="e").pack(fill="x", pady=(8, 3))
    card_var = ctk.StringVar()
    ctk.CTkOptionMenu(form, values=[c.name for c in manager.cards],
                      variable=card_var, height=40, corner_radius=10,
                      font=("Tahoma", 12),
                      fg_color=COLOR_PRIMARY,
                      button_color=COLOR_PRIMARY_HOVER).pack(fill="x")

    start_entry = make_field(form, "تاریخ شروع", "YYYY-MM-DD")
    start_entry.insert(0, datetime.now().strftime("%Y-01-01"))

    end_entry = make_field(form, "تاریخ پایان", "YYYY-MM-DD")
    end_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

    def show_chart():
        card_name = card_var.get()
        if not card_name:
            messagebox.showerror("خطا", "حساب را انتخاب کنید.")
            return

        start_date = start_entry.get().strip()
        end_date = end_entry.get().strip()
        if not start_date or not end_date:
            messagebox.showerror("خطا", "تاریخ را وارد کنید.")
            return

        card = next((c for c in manager.cards if c.name == card_name), None)
        if card:
            show_category_chart(card.id, card_name, start_date, end_date)

    make_buttons(chart_window, show_chart, chart_window.destroy,
                 save_text="📈  نمایش نمودار")


# =====================================================
# پنجره گزارش‌ها
# =====================================================

def open_reports():
    reports_window = ctk.CTkToplevel(window)
    reports_window.title("گزارش‌ها و نمودارها")
    reports_window.geometry("800x580")
    reports_window.resizable(False, False)
    reports_window.transient(window)

    make_header(reports_window, "📊  گزارش‌ها و نمودارها", COLOR_INDIGO)

    main = ctk.CTkFrame(reports_window, fg_color="transparent")
    main.pack(pady=20, padx=20, fill="both", expand=True)

    right = ctk.CTkFrame(main, corner_radius=15,
                          fg_color=("#F1F5F9", "#1E293B"))
    right.grid(row=0, column=0, padx=10, sticky="nsew")

    ctk.CTkLabel(right, text="📊  گزارش‌ها",
                 font=("Tahoma", 15, "bold"),
                 text_color=COLOR_PRIMARY).pack(pady=15)

    for text, cmd in [
        ("💰 خلاصه مالی", show_financial_summary_gui),
        ("📋 همه تراکنش‌ها", show_all_transactions),
        ("📊 گزارش یک حساب", show_account_transactions),
        ("📈 دسته‌بندی هزینه‌ها", show_category_report_gui),
    ]:
        ctk.CTkButton(right, text=text, width=260, height=45,
                      corner_radius=10, font=("Tahoma", 12, "bold"),
                      fg_color=COLOR_PRIMARY,
                      hover_color=COLOR_PRIMARY_HOVER,
                      command=cmd).pack(pady=6, padx=15)

    left = ctk.CTkFrame(main, corner_radius=15,
                         fg_color=("#F1F5F9", "#1E293B"))
    left.grid(row=0, column=1, padx=10, sticky="nsew")

    ctk.CTkLabel(left, text="📈  نمودارها",
                 font=("Tahoma", 15, "bold"),
                 text_color=COLOR_SUCCESS).pack(pady=15)

    for text, cmd in [
        ("📊 نمودار ماهانه", show_monthly_chart_gui),
        ("📈 نمودار سالانه", show_yearly_chart_gui),
        ("🥧 نمودار دسته‌بندی", show_category_chart_gui),
    ]:
        ctk.CTkButton(left, text=text, width=260, height=45,
                      corner_radius=10, font=("Tahoma", 12, "bold"),
                      fg_color=COLOR_SUCCESS,
                      hover_color=COLOR_SUCCESS_HOVER,
                      command=cmd).pack(pady=6, padx=15)

    main.grid_columnconfigure(0, weight=1)
    main.grid_columnconfigure(1, weight=1)

    ctk.CTkButton(reports_window, text="❌  بستن",
                  width=150, height=45, corner_radius=10,
                  font=("Tahoma", 13, "bold"),
                  fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER,
                  command=reports_window.destroy).pack(pady=15)


# =====================================================
# جستجو
# =====================================================

def search_by_date_gui():
    if not manager.cards:
        messagebox.showinfo("جستجو", "هنوز هیچ حسابی ثبت نشده است.")
        return

    sw = ctk.CTkToplevel(window)
    sw.title("جستجو بر اساس تاریخ")
    sw.geometry("500x400")
    sw.transient(window)
    sw.grab_set()

    make_header(sw, "🔍  جستجو بر اساس تاریخ", COLOR_CYAN)

    form = ctk.CTkFrame(sw, fg_color="transparent")
    form.pack(pady=20, padx=30, fill="both", expand=True)

    ctk.CTkLabel(form, text="انتخاب حساب:", font=("Tahoma", 12, "bold"),
                 anchor="e").pack(fill="x", pady=(8, 3))
    card_var = ctk.StringVar()
    ctk.CTkOptionMenu(form, values=[c.name for c in manager.cards],
                      variable=card_var, height=40, corner_radius=10,
                      font=("Tahoma", 12),
                      fg_color=COLOR_PRIMARY,
                      button_color=COLOR_PRIMARY_HOVER).pack(fill="x")

    date_entry = make_field(form, "تاریخ", "مثال: 2026-08-13")

    def do_search():
        selected_name = card_var.get()
        if not selected_name:
            messagebox.showerror("خطا", "یک حساب انتخاب کنید.")
            return

        card = next((c for c in manager.cards if c.name == selected_name), None)
        if card is None:
            return

        date = date_entry.get().strip()
        if not date:
            messagebox.showerror("خطا", "تاریخ را وارد کنید.")
            return

        result = search_date(card.id, date)
        if not result:
            messagebox.showinfo("نتیجه", "تراکنشی پیدا نشد.")
            return

        rw = open_result_window(sw, f"نتیجه - {date}")

        make_header(rw, f"🔍  تراکنش‌های {card.name} - {date}", COLOR_CYAN)

        txt = scrolledtext.ScrolledText(rw, font=("Tahoma", 11),
                                         wrap="word", bg="#F8FAFC")
        txt.pack(fill="both", expand=True, padx=15, pady=15)

        for t in result:
            txt.insert("end", "─" * 40 + "\n")
            txt.insert("end", f"📅 تاریخ: {t[2]}\n")
            txt.insert("end", f"🏷️ نوع: {t[3]}\n")
            txt.insert("end", f"📁 دسته: {t[4]}\n")
            txt.insert("end", f"💰 مبلغ: {t[5]:,.0f}\n")
            txt.insert("end", f"📍 محل: {t[6]}\n")
            txt.insert("end", f"📝 توضیحات: {t[7]}\n\n")

        txt.config(state="disabled")

    make_buttons(sw, do_search, sw.destroy, save_text="🔍  جستجو")


def search_by_date_range_gui():
    if not manager.cards:
        messagebox.showinfo("جستجو", "هنوز هیچ حسابی ثبت نشده است.")
        return

    sw = ctk.CTkToplevel(window)
    sw.title("جستجو در بازه تاریخ")
    sw.geometry("520x420")
    sw.transient(window)
    sw.grab_set()

    make_header(sw, "🔍  جستجو در بازه تاریخ", COLOR_CYAN)

    form = ctk.CTkFrame(sw, fg_color="transparent")
    form.pack(pady=20, padx=30, fill="both", expand=True)

    ctk.CTkLabel(form, text="انتخاب حساب:", font=("Tahoma", 12, "bold"),
                 anchor="e").pack(fill="x", pady=(8, 3))
    card_var = ctk.StringVar()
    ctk.CTkOptionMenu(form, values=[c.name for c in manager.cards],
                      variable=card_var, height=40, corner_radius=10,
                      font=("Tahoma", 12),
                      fg_color=COLOR_PRIMARY,
                      button_color=COLOR_PRIMARY_HOVER).pack(fill="x")

    start_entry = make_field(form, "تاریخ شروع")
    end_entry = make_field(form, "تاریخ پایان")

    def do_search():
        selected_name = card_var.get()
        if not selected_name:
            return
        card = next((c for c in manager.cards if c.name == selected_name), None)
        if card is None:
            return

        start = start_entry.get().strip()
        end = end_entry.get().strip()
        if not start or not end:
            messagebox.showerror("خطا", "تاریخ‌ها را وارد کنید.")
            return

        result = search_by_date_range(card.id, start, end)
        if not result:
            messagebox.showinfo("نتیجه", "تراکنشی پیدا نشد.")
            return

        rw = open_result_window(sw, "نتیجه جستجو")

        make_header(rw, f"🔍  تراکنش‌های {card.name}", COLOR_CYAN)

        txt = scrolledtext.ScrolledText(rw, font=("Tahoma", 11),
                                         wrap="word", bg="#F8FAFC")
        txt.pack(fill="both", expand=True, padx=15, pady=15)

        for t in result:
            txt.insert("end", "─" * 40 + "\n")
            txt.insert("end", f"شناسه: {t[0]}\n")
            txt.insert("end", f"تاریخ: {t[2]}\n")
            txt.insert("end", f"نوع: {t[3]}\n")
            txt.insert("end", f"دسته: {t[4]}\n")
            txt.insert("end", f"مبلغ: {t[5]:,.0f} تومان\n")
            txt.insert("end", f"محل: {t[6]}\n")
            txt.insert("end", f"توضیحات: {t[7]}\n\n")

        txt.config(state="disabled")

    make_buttons(sw, do_search, sw.destroy, save_text="🔍  جستجو")


def search_by_type_gui():
    if not manager.cards:
        messagebox.showinfo("جستجو", "هنوز هیچ حسابی ثبت نشده است.")
        return

    sw = ctk.CTkToplevel(window)
    sw.title("جستجو بر اساس نوع")
    sw.geometry("520x420")
    sw.transient(window)
    sw.grab_set()

    make_header(sw, "🔍  جستجو بر اساس نوع", COLOR_CYAN)

    form = ctk.CTkFrame(sw, fg_color="transparent")
    form.pack(pady=20, padx=30, fill="both", expand=True)

    ctk.CTkLabel(form, text="انتخاب حساب:", font=("Tahoma", 12, "bold"),
                 anchor="e").pack(fill="x", pady=(8, 3))
    card_var = ctk.StringVar()
    ctk.CTkOptionMenu(form, values=[c.name for c in manager.cards],
                      variable=card_var, height=40, corner_radius=10,
                      font=("Tahoma", 12),
                      fg_color=COLOR_PRIMARY,
                      button_color=COLOR_PRIMARY_HOVER).pack(fill="x")

    ctk.CTkLabel(form, text="نوع تراکنش:", font=("Tahoma", 12, "bold"),
                 anchor="e").pack(fill="x", pady=(8, 3))
    type_var = ctk.StringVar(value="درآمد")
    ctk.CTkOptionMenu(form, values=["درآمد", "هزینه", "انتقال", "پس‌انداز"],
                      variable=type_var, height=40, corner_radius=10,
                      font=("Tahoma", 12),
                      fg_color=COLOR_INFO,
                      button_color=COLOR_INFO_HOVER).pack(fill="x")

    def do_search():
        selected_name = card_var.get()
        if not selected_name:
            return
        card = next((c for c in manager.cards if c.name == selected_name), None)
        if card is None:
            return

        result = search_by_type(card.id, type_var.get())
        if not result:
            messagebox.showinfo("نتیجه", "تراکنشی پیدا نشد.")
            return

        rw = open_result_window(sw, "نتیجه جستجو")

        make_header(rw, f"🔍  {type_var.get()}‌های {card.name}", COLOR_CYAN)

        txt = scrolledtext.ScrolledText(rw, font=("Tahoma", 11),
                                         wrap="word", bg="#F8FAFC")
        txt.pack(fill="both", expand=True, padx=15, pady=15)

        for t in result:
            txt.insert("end", "─" * 40 + "\n")
            txt.insert("end", f"تاریخ: {t[2]}\n")
            txt.insert("end", f"نوع: {t[3]}\n")
            txt.insert("end", f"دسته: {t[4]}\n")
            txt.insert("end", f"مبلغ: {t[5]:,.0f} تومان\n")
            txt.insert("end", f"محل: {t[6]}\n")
            txt.insert("end", f"توضیحات: {t[7]}\n\n")

        txt.config(state="disabled")

    make_buttons(sw, do_search, sw.destroy, save_text="🔍  جستجو")


def search_by_description_gui():
    if not manager.cards:
        messagebox.showinfo("جستجو", "هنوز هیچ حسابی ثبت نشده است.")
        return

    sw = ctk.CTkToplevel(window)
    sw.title("جستجو بر اساس توضیحات")
    sw.geometry("520x400")
    sw.transient(window)
    sw.grab_set()

    make_header(sw, "🔍  جستجو بر اساس توضیحات", COLOR_CYAN)

    form = ctk.CTkFrame(sw, fg_color="transparent")
    form.pack(pady=20, padx=30, fill="both", expand=True)

    ctk.CTkLabel(form, text="انتخاب حساب:", font=("Tahoma", 12, "bold"),
                 anchor="e").pack(fill="x", pady=(8, 3))
    card_var = ctk.StringVar()
    ctk.CTkOptionMenu(form, values=[c.name for c in manager.cards],
                      variable=card_var, height=40, corner_radius=10,
                      font=("Tahoma", 12),
                      fg_color=COLOR_PRIMARY,
                      button_color=COLOR_PRIMARY_HOVER).pack(fill="x")

    text_entry = make_field(form, "متن مورد جستجو")

    def do_search():
        selected_name = card_var.get()
        if not selected_name:
            return
        card = next((c for c in manager.cards if c.name == selected_name), None)
        if card is None:
            return

        text = text_entry.get().strip()
        if not text:
            messagebox.showerror("خطا", "متن جستجو را وارد کنید.")
            return

        result = search_by_description(card.id, text)
        if not result:
            messagebox.showinfo("نتیجه", "تراکنشی پیدا نشد.")
            return

        rw = open_result_window(sw, f"جستجو: {text}")

        make_header(rw, f"🔍  جستجو: {text}", COLOR_CYAN)

        txt = scrolledtext.ScrolledText(rw, font=("Tahoma", 11),
                                         wrap="word", bg="#F8FAFC")
        txt.pack(fill="both", expand=True, padx=15, pady=15)

        for t in result:
            txt.insert("end", "─" * 40 + "\n")
            txt.insert("end", f"تاریخ: {t[2]}\n")
            txt.insert("end", f"نوع: {t[3]}\n")
            txt.insert("end", f"دسته: {t[4]}\n")
            txt.insert("end", f"مبلغ: {t[5]:,.0f} تومان\n")
            txt.insert("end", f"محل: {t[6]}\n")
            txt.insert("end", f"توضیحات: {t[7]}\n\n")

        txt.config(state="disabled")

    make_buttons(sw, do_search, sw.destroy, save_text="🔍  جستجو")


def open_search():
    search_window = ctk.CTkToplevel(window)
    search_window.title("جستجوی تراکنش‌ها")
    search_window.geometry("500x500")
    search_window.resizable(False, False)
    search_window.transient(window)
    search_window.grab_set()

    make_header(search_window, "🔍  جستجوی تراکنش‌ها", COLOR_CYAN)

    frame = ctk.CTkFrame(search_window, fg_color="transparent")
    frame.pack(pady=30, padx=30, fill="both", expand=True)

    for text, cmd in [
        ("📅 جستجو بر اساس تاریخ", search_by_date_gui),
        ("📆 جستجو در بازه تاریخ", search_by_date_range_gui),
        ("🏷️ جستجو بر اساس نوع", search_by_type_gui),
        ("📝 جستجو بر اساس توضیحات", search_by_description_gui),
    ]:
        ctk.CTkButton(frame, text=text, width=280, height=50,
                      corner_radius=12, font=("Tahoma", 13, "bold"),
                      fg_color=COLOR_PRIMARY,
                      hover_color=COLOR_PRIMARY_HOVER,
                      command=cmd).pack(pady=10)

    ctk.CTkButton(search_window, text="❌  بستن",
                  width=150, height=45, corner_radius=10,
                  font=("Tahoma", 13, "bold"),
                  fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER,
                  command=search_window.destroy).pack(pady=15)


# =====================================================
# پشتیبان‌گیری
# =====================================================

def open_backup_manager():
    backup_window = ctk.CTkToplevel(window)
    backup_window.title("مدیریت پشتیبان‌گیری")
    backup_window.geometry("850x650")
    backup_window.resizable(False, False)
    backup_window.transient(window)

    make_header(backup_window, "💾  مدیریت پشتیبان‌گیری", COLOR_SUCCESS)

    info = ctk.CTkFrame(backup_window, corner_radius=12,
                         fg_color=("#F1F5F9", "#1E293B"))
    info.pack(pady=15, padx=20, fill="x")

    size_label = ctk.CTkLabel(info,
                               text=f"📊  حجم دیتابیس: {get_database_size()} KB",
                               font=("Tahoma", 12, "bold"))
    size_label.pack(pady=5)

    count_label = ctk.CTkLabel(info,
                                text=f"📦  تعداد پشتیبان‌ها: {get_backup_count()}",
                                font=("Tahoma", 12, "bold"))
    count_label.pack(pady=5)

    table_frame = ctk.CTkFrame(backup_window, corner_radius=10)
    table_frame.pack(pady=15, padx=20, fill="both", expand=True)

    scrollbar = ctk.CTkScrollbar(table_frame)
    scrollbar.pack(side="right", fill="y")

    columns = ("filename", "size", "date")
    tree = ttk.Treeview(table_frame, columns=columns, show="headings",
                        yscrollcommand=scrollbar.set, height=12)
    scrollbar.configure(command=tree.yview)
    tree.pack(fill="both", expand=True, padx=5, pady=5)

    tree.heading("filename", text="نام فایل")
    tree.heading("size", text="حجم (KB)")
    tree.heading("date", text="تاریخ ساخت")
    tree.column("filename", width=380, anchor="center")
    tree.column("size", width=130, anchor="center")
    tree.column("date", width=220, anchor="center")

    def refresh_list():
        for item in tree.get_children():
            tree.delete(item)
        for b in list_backups():
            tree.insert("", "end", values=(b["filename"], b["size_kb"], b["date"]))
        size_label.configure(text=f"📊  حجم دیتابیس: {get_database_size()} KB")
        count_label.configure(text=f"📦  تعداد پشتیبان‌ها: {get_backup_count()}")

    refresh_list()

    def do_backup():
        filename = create_backup()
        if filename:
            messagebox.showinfo("موفق", f"✅ پشتیبان ساخته شد:\n{filename}")
            refresh_list()
        else:
            messagebox.showerror("خطا", "ساخت پشتیبان ناموفق بود.")

    def restore_selected():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("توجه", "یک پشتیبان انتخاب کنید.")
            return

        filename = tree.item(selected[0])["values"][0]

        if not messagebox.askyesno("تأیید",
                                    f"آیا از «{filename}» بازگردانی شود؟"):
            return

        if restore_backup(filename):
            messagebox.showinfo("موفق", "✅ بازگردانی شد. برنامه بسته می‌شود.")
            window.destroy()
        else:
            messagebox.showerror("خطا", "بازگردانی ناموفق بود.")

    def delete_selected():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("توجه", "یک پشتیبان انتخاب کنید.")
            return

        filename = tree.item(selected[0])["values"][0]
        if not messagebox.askyesno("تأیید", f"حذف «{filename}»؟"):
            return

        if delete_backup(filename):
            messagebox.showinfo("موفق", "✅ حذف شد.")
            refresh_list()
        else:
            messagebox.showerror("خطا", "حذف ناموفق بود.")

    btn_frame = ctk.CTkFrame(backup_window, fg_color="transparent")
    btn_frame.pack(pady=15)

    ctk.CTkButton(btn_frame, text="📥  ساخت پشتیبان جدید",
                  width=200, height=45, corner_radius=10,
                  font=("Tahoma", 12, "bold"),
                  fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER,
                  command=do_backup).pack(side="right", padx=5)

    ctk.CTkButton(btn_frame, text="🔄  بازگردانی",
                  width=150, height=45, corner_radius=10,
                  font=("Tahoma", 12, "bold"),
                  fg_color=COLOR_INFO, hover_color=COLOR_INFO_HOVER,
                  command=restore_selected).pack(side="right", padx=5)

    ctk.CTkButton(btn_frame, text="🗑️  حذف",
                  width=130, height=45, corner_radius=10,
                  font=("Tahoma", 12, "bold"),
                  fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER,
                  command=delete_selected).pack(side="right", padx=5)

    ctk.CTkButton(backup_window, text="❌  بستن",
                  width=150, height=45, corner_radius=10,
                  font=("Tahoma", 13, "bold"),
                  fg_color=COLOR_DANGER, hover_color=COLOR_DANGER_HOVER,
                  command=backup_window.destroy).pack(pady=15)


# =====================================================
# پنجره‌ی اصلی — منو
# =====================================================

def open_home():
    for widget in window.winfo_children():
        widget.destroy()

    # =========================
    # نوار بالا
    # =========================
    top_bar = ctk.CTkFrame(window, height=70, corner_radius=0,
                            fg_color=COLOR_PRIMARY)
    top_bar.pack(fill="x", side="top")
    top_bar.pack_propagate(False)

    ctk.CTkLabel(top_bar, text="💰  برنامه مدیریت مالی",
                 font=("Tahoma", 22, "bold"),
                 text_color="white").pack(side="right", padx=20, pady=15)

    def on_toggle_theme():
        mode = toggle_appearance()
        theme_btn.configure(text="☀️" if mode == "light" else "🌙")

    theme_btn = ctk.CTkButton(
        top_bar,
        text="🌙" if ctk.get_appearance_mode() == "Dark" else "☀️",
        width=45, height=40, corner_radius=10,
        font=("Tahoma", 16),
        fg_color="transparent",
        hover_color=COLOR_PRIMARY_HOVER,
        command=on_toggle_theme
    )
    theme_btn.pack(side="left", padx=15, pady=15)

    # =========================
    # خوش‌آمد
    # =========================
    ctk.CTkLabel(window, text="به برنامه‌ی مدیریت مالی خوش آمدید",
                 font=("Tahoma", 14),
                 text_color=("#64748B", "#94A3B8")).pack(pady=(20, 10))

    # =========================
    # کارت‌های آمار
    # =========================
    stats_frame = ctk.CTkFrame(window, fg_color="transparent")
    stats_frame.pack(pady=10, padx=30, fill="x")

    try:
        # درآمد و هزینه‌ی تراکنشی
        tx_income, total_expense = show_financial_summary()

        # موجودی اولیه‌ی همه‌ی کارت‌ها
        # ⚠️ از تراکنش‌های درآمد/هزینه‌ی هر کارت، موجودی اولیه رو حساب می‌کنیم
        # راه ساده‌تر: مجموع موجودی کارت‌ها + هزینه‌ها - درآمدها = موجودی اولیه
        total_balance = sum(c.balance for c in manager.cards)
        initial_balance = total_balance - tx_income + total_expense

        # درآمد کل = موجودی اولیه + درآمدهای تراکنشی
        total_income = initial_balance + tx_income

        # مانده = درآمد کل - هزینه کل
        balance = total_income - total_expense

    except Exception:
        total_income = total_expense = balance = 0

    stats = [
        ("💵", "درآمد کل", f"{total_income:,.0f}", COLOR_SUCCESS),
        ("💸", "هزینه کل", f"{total_expense:,.0f}", COLOR_DANGER),
        ("💰", "مانده", f"{balance:,.0f}", COLOR_INFO),
        ("🏦", "کارت‌ها", f"{len(manager.cards)}", COLOR_WARNING),
    ]

    for icon, label, value, color in stats:
        card = ctk.CTkFrame(stats_frame, corner_radius=15, fg_color=color)
        card.pack(side="right", expand=True, fill="x", padx=5)

        ctk.CTkLabel(card, text=icon, font=("Tahoma", 22),
                     text_color="white").pack(pady=(10, 0))
        ctk.CTkLabel(card, text=value, font=("Tahoma", 14, "bold"),
                     text_color="white").pack(pady=(2, 0))
        ctk.CTkLabel(card, text=label, font=("Tahoma", 10),
                     text_color="white").pack(pady=(0, 10))

    # =========================
    # منوی اصلی
    # =========================
    ctk.CTkLabel(window, text="━━━  منوی اصلی  ━━━",
                 font=("Tahoma", 14, "bold"),
                 text_color=("#1E293B", "#E2E8F0")).pack(pady=(20, 10))

    buttons_frame = ctk.CTkFrame(window, fg_color="transparent")
    buttons_frame.pack(pady=10, padx=30)

    buttons = [
        ("💳  ثبت کارت بانکی",   COLOR_PRIMARY, open_add_card),
        ("📋  نمایش کارت‌ها",     COLOR_INFO,    open_accounts),
        ("💵  ثبت درآمد",         COLOR_SUCCESS, open_income),
        ("💸  ثبت هزینه",         COLOR_DANGER,  open_expense),
        ("🔁  انتقال بین کارت‌ها", COLOR_WARNING, open_transfer),
        ("🐷  پس‌انداز",           COLOR_PINK,    open_savings_menu),
        ("📊  گزارش‌ها",           COLOR_INDIGO,  open_reports),
        ("🔍  جستجوی تراکنش‌ها",  COLOR_CYAN,    open_search),
        ("💾  پشتیبان‌گیری",       COLOR_SUCCESS, open_backup_manager),
        ("❌  خروج",               COLOR_DANGER,  window.destroy),
    ]

    for i, (text, color, command) in enumerate(buttons):
        row = i // 2
        col = i % 2

        ctk.CTkButton(
            buttons_frame,
            text=text,
            width=BUTTON_WIDTH,
            height=BUTTON_HEIGHT,
            corner_radius=BUTTON_CORNER,
            font=("Tahoma", 13, "bold"),
            fg_color=color,
            hover_color=color,
            command=command
        ).grid(row=row, column=col, padx=10, pady=8)

    # =========================
    # فوتر
    # =========================
    ctk.CTkLabel(window, text="نسخه 1.0 — ساخته‌شده با ❤️",
                 font=("Tahoma", 10),
                 text_color=("#94A3B8", "#64748B")).pack(side="bottom", pady=10)
# =====================================================
# شروع برنامه
# =====================================================

open_home()
window.mainloop()
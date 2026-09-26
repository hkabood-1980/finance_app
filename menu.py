# menu.py
"""منوی خط فرمان"""

from models import BankCard, Transaction
from datetime import datetime

from database import (
    add_account,
    load_accounts,
    add_transaction,
    update_balance,
    delete_account,
)

from services import (
    select_account,
    show_transaction_report,
    show_financial_summary,
    show_account_report,
    show_search_by_date,
    show_search_by_date_range,
    show_search_by_type,
    show_search_by_description,
    edit_account,
    show_account,
    register_saving,
    register_transaction,
    register_transfer,
    set_savings_account,
    get_savings_account_id,
)

from reports import get_category_report


# =====================================================
# ثبت کارت بانکی
# =====================================================

def menu_add_account(manager):
    name = input("نام کارت: ")
    bank = input("نام بانک: ")
    card_number = input("شماره کارت: ")
    balance = float(input("موجودی اولیه: "))
    account_type = input("نوع حساب: ")

    account_id = add_account(name, bank, card_number, balance, account_type)

    card = BankCard(
        name=name, balance=balance, bank=bank,
        card_number=card_number, account_type=account_type,
        account_id=account_id
    )

    manager.add_card(card)
    print("✅ کارت با موفقیت ثبت شد.")


# =====================================================
# نمایش کارت‌ها
# =====================================================

def menu_show_accounts(manager):
    if len(manager.cards) == 0:
        print("هیچ کارتی ثبت نشده است.")
        return

    print("\n===== کارت‌های بانکی =====")
    for card in manager.cards:
        print("-" * 50)
        print(f"شناسه: {card.id}")
        print(f"نام: {card.name}")
        print(f"بانک: {card.bank}")
        print(f"شماره کارت: {card.card_number}")
        print(f"نوع حساب: {card.account_type}")
        print(f"موجودی: {card.balance:,.0f} تومان")


# =====================================================
# ویرایش کارت
# =====================================================

def menu_edit_account(manager):
    account_id = int(input("شناسه کارت: "))

    account = show_account(account_id)
    if account is None:
        return

    name = input(f"نام ({account[1]}): ") or account[1]
    bank = input(f"بانک ({account[2]}): ") or account[2]
    card_number = input(f"شماره کارت ({account[3]}): ") or account[3]

    balance_input = input(f"موجودی ({account[4]}): ")
    balance = float(balance_input) if balance_input else account[4]

    account_type = input(f"نوع حساب ({account[5]}): ") or account[5]

    edit_account(account_id, name, bank, card_number, balance, account_type)

    for card in manager.cards:
        if card.id == account_id:
            card.name = name
            card.bank = bank
            card.card_number = card_number
            card.balance = balance
            card.account_type = account_type
            break

    print("✅ کارت با موفقیت ویرایش شد.")


# =====================================================
# حذف کارت
# =====================================================

def menu_delete_account(manager):
    account_id = int(input("شناسه کارتی که می‌خواهید حذف کنید: "))

    result = delete_account(account_id)
    if result is False:
        print("❌ این حساب دارای تراکنش است و قابل حذف نیست.")
        return

    manager.cards = [c for c in manager.cards if c.id != account_id]
    print("✅ کارت با موفقیت حذف شد.")


# =====================================================
# ثبت درآمد
# =====================================================

def menu_income(manager):
    if len(manager.cards) == 0:
        print("ابتدا یک کارت ثبت کنید.")
        return

    print("\n===== کارت‌ها =====")
    for i, card in enumerate(manager.cards):
        print(f"{i + 1}- {card.name}")

    card_number = int(input("شماره کارت را انتخاب کنید: "))
    amount = int(input("مبلغ درآمد: "))
    category = input("دسته‌بندی: ")
    place = input("محل: ")
    description = input("توضیحات: ")

    card = manager.cards[card_number - 1]
    date = datetime.now().strftime("%Y-%m-%d %H:%M")

    try:
        register_transaction(
            card.id, date, "درآمد", category,
            amount, place, description
        )
    except ValueError as e:
        print(f"❌ {e}")
        return

    card.balance += amount
    print("✅ درآمد با موفقیت ثبت شد.")


# =====================================================
# ثبت هزینه
# =====================================================

def menu_expense(manager):
    if len(manager.cards) == 0:
        print("ابتدا یک کارت ثبت کنید.")
        return

    print("\n===== کارت‌ها =====")
    for i, card in enumerate(manager.cards):
        print(f"{i + 1}- {card.name}")

    card_number = int(input("شماره کارت را انتخاب کنید: "))
    amount = int(input("مبلغ هزینه: "))
    category = input("دسته‌بندی هزینه: ")
    place = input("محل: ")
    description = input("توضیح: ")

    card = manager.cards[card_number - 1]
    date = datetime.now().strftime("%Y-%m-%d %H:%M")

    try:
        register_transaction(
            card.id, date, "هزینه", category,
            amount, place, description
        )
    except ValueError as e:
        print(f"❌ {e}")
        return

    card.balance -= amount
    print("✅ هزینه با موفقیت ثبت شد.")


# =====================================================
# انتقال بین کارت‌ها
# =====================================================

def menu_transfer(manager):
    if len(manager.cards) < 2:
        print("حداقل دو کارت لازم است.")
        return

    print("\n===== کارت‌ها =====")
    for i, card in enumerate(manager.cards):
        print(f"{i + 1}- {card.name}")

    source = int(input("شماره کارت مبدا: ")) - 1
    destination = int(input("شماره کارت مقصد: ")) - 1
    amount = int(input("مبلغ انتقال: "))
    description = input("توضیحات: ")

    source_card = manager.cards[source]
    destination_card = manager.cards[destination]

    date = datetime.now().strftime("%Y-%m-%d %H:%M")

    try:
        register_transfer(
            source_card.id, destination_card.id,
            date, amount, description
        )
    except ValueError as e:
        print(f"❌ {e}")
        return

    source_card.balance -= amount
    destination_card.balance += amount

    print("✅ انتقال با موفقیت انجام شد.")


# =====================================================
# گزارش‌ها
# =====================================================

def menu_reports():
    print("\n===== گزارش‌ها =====")
    print("1- گزارش همه تراکنش‌ها")
    print("2- خلاصه مالی")
    print("3- گزارش یک حساب")
    print("4- گزارش دسته‌بندی هزینه‌ها")

    report_choice = input("انتخاب: ").strip()

    if report_choice == "1":
        report = show_transaction_report()
        if not report:
            print("داده‌ای وجود ندارد.")
        else:
            for row in report:
                print(row)

    elif report_choice == "2":
        income, expense = show_financial_summary()
        print("\n===== خلاصه مالی =====")
        print(f"درآمد : {income:,.0f}")
        print(f"هزینه : {expense:,.0f}")
        print(f"مانده : {income - expense:,.0f}")

    elif report_choice == "3":
        account_id = int(input("شناسه حساب: "))
        report = show_account_report(account_id)
        if not report:
            print("تراکنشی وجود ندارد.")
        else:
            for row in report:
                print(row)

    elif report_choice == "4":
        account_id = int(input("شناسه حساب: "))
        start_date = input("از تاریخ: ")
        end_date = input("تا تاریخ: ")

        report = get_category_report(account_id, start_date, end_date)
        if not report:
            print("داده‌ای وجود ندارد.")
        else:
            for category, total in report:
                print(f"{category} : {total:,.0f}")


# =====================================================
# جستجو
# =====================================================

def menu_search():
    account_id = select_account()
    if account_id is None:
        return

    print("\n===== جستجو =====")
    print("1- بر اساس تاریخ")
    print("2- بر اساس بازه تاریخ")
    print("3- بر اساس نوع")
    print("4- بر اساس توضیحات")

    choice = input("انتخاب: ")

    if choice == "1":
        date = input("تاریخ: ")
        show_search_by_date(account_id, date)

    elif choice == "2":
        start = input("از تاریخ: ")
        end = input("تا تاریخ: ")
        show_search_by_date_range(account_id, start, end)

    elif choice == "3":
        trans_type = input("نوع تراکنش: ")
        show_search_by_type(account_id, trans_type)

    elif choice == "4":
        text = input("توضیحات: ")
        show_search_by_description(account_id, text)


# =====================================================
# تعیین حساب پس‌انداز
# =====================================================

def menu_set_savings_account():
    current_id = get_savings_account_id()
    if current_id is not None:
        account = show_account(current_id)
        print("\n(حساب بالا، حساب پس‌انداز فعلی است)")
    else:
        print("\nهنوز هیچ حساب پس‌اندازی تعیین نشده است.")

    print("\nیک حساب را به‌عنوان حساب پس‌انداز جدید انتخاب کنید (یا Enter برای انصراف):")
    accounts = load_accounts()
    if not accounts:
        print("هیچ حسابی ثبت نشده است.")
        return

    for account in accounts:
        print(f"{account[0]} - {account[1]} ({account[2]})")

    choice = input("شناسه حساب: ").strip()
    if not choice:
        return

    try:
        account_id = int(choice)
        set_savings_account(account_id)
        print("✅ حساب پس‌انداز با موفقیت تعیین شد.")
    except ValueError as e:
        print(f"❌ {e}")


# =====================================================
# پس‌انداز
# =====================================================

def menu_saving(manager):
    account_id = select_account()
    if account_id is None:
        return

    try:
        amount = float(input("مبلغ پس‌انداز: "))
        category = input("دسته‌بندی: ")
        place = input("محل: ")
        description = input("توضیحات: ")

        register_saving(
            account_id=account_id,
            amount=amount,
            category=category,
            place=place,
            description=description,
            date=datetime.now().strftime("%Y-%m-%d %H:%M")
        )

        # بازخوانی manager از دیتابیس
        manager.reload_from_db()

        print("✅ پس‌انداز با موفقیت ثبت شد.")

    except ValueError as e:
        print(f"❌ {e}")


# =====================================================
# مدیریت تراکنش‌ها
# =====================================================

def menu_transaction():
    while True:
        print("\n===== مدیریت تراکنش‌ها =====")
        print("1- ویرایش تراکنش")
        print("2- حذف تراکنش")
        print("3- بازگشت")

        choice = input("انتخاب شما: ")

        if choice == "1":
            print("ویرایش تراکنش (به زودی)")
        elif choice == "2":
            print("حذف تراکنش (به زودی)")
        elif choice == "3":
            break
        else:
            print("انتخاب نامعتبر است.")
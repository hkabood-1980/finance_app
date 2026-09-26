# main.py
"""نقطه ورود برنامه مدیریت مالی (خط فرمان)"""

from models import BankCard, FinanceManager
from database import load_accounts, create_tables
from backup import create_backup, should_auto_backup
from menu import (
    menu_add_account,
    menu_show_accounts,
    menu_edit_account,
    menu_delete_account,
    menu_income,
    menu_expense,
    menu_transfer,
    menu_saving,
    menu_reports,
    menu_search,
    menu_transaction,
    menu_set_savings_account,
)


def main():
    create_tables()

    # پشتیبان خودکار
    if should_auto_backup():
        filename = create_backup()
        if filename:
            print(f"📦 پشتیبان خودکار ساخته شد: {filename}")

    manager = FinanceManager()

    accounts = load_accounts()
    for account in accounts:
        id_, name, bank, card_number, balance, account_type = account
        card = BankCard(
            name=name, balance=balance, bank=bank,
            card_number=card_number,
            account_type=account_type, account_id=id_
        )
        manager.add_card(card)

    while True:
        print("\n===== برنامه مدیریت مالی =====")
        print("1- ثبت کارت بانکی")
        print("2- نمایش موجودی کارت‌ها")
        print("3- ویرایش کارت بانکی")
        print("4- حذف کارت بانکی")
        print("5- ثبت درآمد")
        print("6- ثبت هزینه")
        print("7- انتقال بین کارت‌ها")
        print("8- ثبت پس انداز")
        print("9- گزارش‌ها")
        print("10- جستجوی تراکنش‌ها")
        print("11- مدیریت تراکنش‌ها")
        print("12- تعیین/نمایش حساب پس‌انداز")
        print("13- خروج")

        choice = input("انتخاب شما: ")

        if choice == "1":
            menu_add_account(manager)
        elif choice == "2":
            menu_show_accounts(manager)
        elif choice == "3":
            menu_edit_account(manager)
        elif choice == "4":
            menu_delete_account(manager)
        elif choice == "5":
            menu_income(manager)
        elif choice == "6":
            menu_expense(manager)
        elif choice == "7":
            menu_transfer(manager)
        elif choice == "8":
            menu_saving(manager)
        elif choice == "9":
            menu_reports()
        elif choice == "10":
            menu_search()
        elif choice == "11":
            menu_transaction()
        elif choice == "12":
            menu_set_savings_account()
        elif choice == "13":
            print("خدانگهدار")
            break


if __name__ == "__main__":
    main()
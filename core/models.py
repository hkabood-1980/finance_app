# models.py
"""کلاس‌های مدل برنامه"""

from datetime import datetime


class BankCard:

    def __init__(self, name, balance=0, bank="", card_number="",
                 account_type="", account_id=None):
        self.id = account_id
        self.name = name
        self.balance = balance
        self.bank = bank
        self.card_number = card_number
        self.account_type = account_type

    def deposit(self, amount):
        self.balance += amount

    def withdraw(self, amount):
        if amount <= self.balance:
            self.balance -= amount
            return True
        return False

    def show_balance(self):
        print(f"{self.name}: {self.balance:,} تومان")

    def transfer(self, destination_card, amount):
        if amount <= 0:
            print("مبلغ نامعتبر است.")
            return False
        if self.balance < amount:
            print("موجودی کافی نیست.")
            return False

        self.balance -= amount
        destination_card.balance += amount
        return True

    def edit(self, name=None, balance=None):
        if name is not None:
            self.name = name
        if balance is not None:
            self.balance = balance


class Transaction:
    def __init__(self, trans_type, amount, card_name,
                 category="", place="", description=""):
        self.trans_type = trans_type
        self.amount = amount
        self.card_name = card_name
        self.category = category
        self.place = place
        self.description = description
        self.date = datetime.now().strftime("%Y-%m-%d %H:%M")


class FinanceManager:
    def __init__(self):
        self.cards = []
        self.transactions = []

    def add_card(self, card):
        self.cards.append(card)

    def add_transaction(self, transaction):
        self.transactions.append(transaction)

    def show_cards(self):
        if not self.cards:
            print("هنوز کارتی ثبت نشده است.")
            return
        for card in self.cards:
            print(f"{card.name} : {card.balance:,} تومان")

    def reload_from_db(self):
        """
        بازخوانی کارت‌ها از دیتابیس.
        مفید پس از عملیاتی که موجودی‌ها را در دیتابیس تغییر می‌دهد.
        """
        from database import load_accounts
        self.cards.clear()
        for account in load_accounts():
            account_id, name, bank, card_number, balance, account_type = account
            card = BankCard(
                name=name, balance=balance, bank=bank,
                card_number=card_number,
                account_type=account_type, account_id=account_id
            )
            self.add_card(card)

    # =====================================================
    # جستجو بر اساس id یا name
    # =====================================================

    def find_card(self, identifier):
        for card in self.cards:
            if card.id == identifier:
                return card

        for card in self.cards:
            if card.name == identifier:
                return card

        return None

    def find_card_by_name(self, name):
        for card in self.cards:
            if card.name == name:
                return card
        return None

    def find_card_by_id(self, card_id):
        for card in self.cards:
            if card.id == card_id:
                return card
        return None

    def delete_card(self, identifier):
        card = self.find_card(identifier)
        if card:
            self.cards.remove(card)
            return True
        return False

    def edit_card(self, identifier, new_name=None, new_balance=None):
        card = self.find_card(identifier)
        if card is None:
            return False

        if new_name is not None:
            card.name = new_name
        if new_balance is not None:
            card.balance = new_balance
        return True

    def show_transactions(self):
        if not self.transactions:
            print("هیچ تراکنشی ثبت نشده است.")
            return

        for t in self.transactions:
            print("-" * 40)
            print(f"تاریخ: {t.date}")
            print(f"نوع: {t.trans_type}")
            print(f"مبلغ: {t.amount:,}")
            print(f"کارت: {t.card_name}")
            print(f"دسته: {t.category}")
            print(f"توضیح: {t.description}")
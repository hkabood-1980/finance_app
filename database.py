# database.py
"""ماژول دیتابیس برنامه مدیریت مالی"""


import os
import sys
import sqlite3

def get_db_path():
    """مسیر دیتابیس در AppData (قابل نوشتن)"""
    if getattr(sys, 'frozen', False):
        # حالت exe: در AppData کاربر ذخیره کن
        app_dir = os.path.join(os.environ['APPDATA'], 'FinanceApp')
    else:
        # حالت اجرا از سورس: پوشه‌ی data کنار پروژه
        app_dir = os.path.join(os.path.dirname(__file__), 'data')
    
    os.makedirs(app_dir, exist_ok=True)
    return os.path.join(app_dir, 'finance.db')

DB_NAME = get_db_path()

def get_connection():
    """ایجاد اتصال به دیتابیس"""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def create_tables():
    """ایجاد جدول‌های برنامه"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accounts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        bank TEXT,
        card_number TEXT,
        balance REAL DEFAULT 0,
        type TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        account_id INTEGER,
        date TEXT NOT NULL,
        type TEXT NOT NULL,
        category TEXT,
        amount REAL NOT NULL,
        place TEXT,
        description TEXT,
        balance_after REAL,
        FOREIGN KEY(account_id) REFERENCES accounts(id)
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings(
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    conn.commit()
    conn.close()


# =====================================================
# تنظیمات برنامه
# =====================================================

def set_setting(key, value):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO settings (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (key, str(value)))
    conn.commit()
    conn.close()


def get_setting(key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


# =====================================================
# توابع مربوط به حساب‌ها
# =====================================================

def add_account(name, bank, card_number, balance, account_type):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO accounts
        (name, bank, card_number, balance, type)
        VALUES (?, ?, ?, ?, ?)
    """, (name, bank, card_number, balance, account_type))

    account_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return account_id


def load_accounts():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, bank, card_number, balance, type
        FROM accounts
    """)
    accounts = cursor.fetchall()
    conn.close()
    return accounts


def get_account_by_id(account_id, conn=None):
    own_connection = conn is None
    if own_connection:
        conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, bank, card_number, balance, type
        FROM accounts
        WHERE id = ?
    """, (account_id,))

    account = cursor.fetchone()
    if own_connection:
        conn.close()
    return account


def update_account(account_id, name, bank, card_number, balance, account_type,
                   conn=None):
    own_connection = conn is None
    if own_connection:
        conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE accounts
        SET name = ?, bank = ?, card_number = ?, balance = ?, type = ?
        WHERE id = ?
    """, (name, bank, card_number, balance, account_type, account_id))

    if own_connection:
        conn.commit()
        conn.close()


def update_balance(account_id, new_balance):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE accounts
        SET balance = ?
        WHERE id = ?
    """, (new_balance, account_id))

    conn.commit()
    conn.close()


def delete_account(account_id):
    """حذف حساب فقط اگر تراکنش نداشته باشد"""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM transactions WHERE account_id = ?
    """, (account_id,))

    transaction_count = cursor.fetchone()[0]

    if transaction_count > 0:
        conn.close()
        return False

    cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    conn.commit()
    conn.close()
    return True


# =====================================================
# توابع مربوط به تراکنش‌ها
# =====================================================

def add_transaction(account_id, date, trans_type, category, amount,
                    place, description, balance_after, conn=None):
    own_connection = conn is None
    if own_connection:
        conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO transactions
           (account_id, date, type, category, amount,
            place, description, balance_after)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (account_id, date, trans_type, category, amount,
          place, description, balance_after))

    transaction_id = cursor.lastrowid

    if own_connection:
        conn.commit()
        conn.close()
    return transaction_id


def get_transactions():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, account_id, date, type, category,
               amount, place, description, balance_after
        FROM transactions
        ORDER BY date DESC
    """)
    transactions = cursor.fetchall()
    conn.close()
    return transactions


def get_transactions_by_account(account_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, account_id, date, type, category,
               amount, place, description
        FROM transactions
        WHERE account_id = ?
        ORDER BY date DESC
    """, (account_id,))

    transactions = cursor.fetchall()
    conn.close()
    return transactions


def get_transaction_by_id(transaction_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, account_id, date, type, category,
               amount, place, description
        FROM transactions
        WHERE id = ?
    """, (transaction_id,))

    transaction = cursor.fetchone()
    conn.close()
    return transaction


def update_transaction(transaction_id, account_id, date,
                       trans_type, category, amount,
                       place, description, balance_after=None):
    conn = get_connection()
    cursor = conn.cursor()

    if balance_after is not None:
        cursor.execute("""
            UPDATE transactions
            SET account_id = ?, date = ?, type = ?, category = ?,
                amount = ?, place = ?, description = ?, balance_after = ?
            WHERE id = ?
        """, (account_id, date, trans_type, category, amount,
              place, description, balance_after, transaction_id))
    else:
        cursor.execute("""
            UPDATE transactions
            SET account_id = ?, date = ?, type = ?, category = ?,
                amount = ?, place = ?, description = ?
            WHERE id = ?
        """, (account_id, date, trans_type, category, amount,
              place, description, transaction_id))

    conn.commit()
    conn.close()


def delete_transaction(transaction_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    conn.commit()
    deleted = cursor.rowcount
    conn.close()
    return deleted > 0


def get_last_transaction_id():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM transactions ORDER BY id DESC LIMIT 1
    """)

    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None


# =====================================================
# جستجوها
# =====================================================

def search_by_date(account_id, date):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, account_id, date, type, category,
               amount, place, description
        FROM transactions
        WHERE account_id = ? AND date = ?
        ORDER BY date DESC
    """, (account_id, date))

    transactions = cursor.fetchall()
    conn.close()
    return transactions


def search_by_date_range(account_id, start_date, end_date):
    if len(end_date) == 10:
        end_date_full = end_date + " 23:59"
    else:
        end_date_full = end_date

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, account_id, date, type, category,
               amount, place, description
        FROM transactions
        WHERE account_id = ?
        AND date >= ?
        AND date <= ?
        ORDER BY date ASC
    """, (account_id, start_date, end_date_full))

    transactions = cursor.fetchall()
    conn.close()
    return transactions


def search_by_type(account_id, trans_type):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, account_id, date, type, category,
               amount, place, description
        FROM transactions
        WHERE account_id = ? AND type = ?
        ORDER BY date DESC
    """, (account_id, trans_type))

    transactions = cursor.fetchall()
    conn.close()
    return transactions


def search_by_description(account_id, text):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, account_id, date, type, category,
               amount, place, description
        FROM transactions
        WHERE account_id = ? AND description LIKE ?
        ORDER BY date DESC
    """, (account_id, f"%{text}%"))

    transactions = cursor.fetchall()
    conn.close()
    return transactions


def search_transactions(start_date=None, end_date=None, trans_type=None,
                        category=None, min_amount=None, max_amount=None):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        SELECT
            transactions.id,
            accounts.name,
            transactions.date,
            transactions.type,
            transactions.category,
            transactions.amount,
            transactions.place,
            transactions.description
        FROM transactions
        JOIN accounts ON transactions.account_id = accounts.id
        WHERE 1=1
    """
    params = []

    if start_date:
        query += " AND transactions.date >= ?"
        params.append(start_date)
    if end_date:
        if len(end_date) == 10:
            end_date = end_date + " 23:59"
        query += " AND transactions.date <= ?"
        params.append(end_date)
    if trans_type:
        query += " AND transactions.type = ?"
        params.append(trans_type)
    if category:
        query += " AND transactions.category = ?"
        params.append(category)
    if min_amount is not None:
        query += " AND transactions.amount >= ?"
        params.append(min_amount)
    if max_amount is not None:
        query += " AND transactions.amount <= ?"
        params.append(max_amount)

    query += " ORDER BY transactions.date DESC"

    cursor.execute(query, params)
    result = cursor.fetchall()
    conn.close()
    return result


# =====================================================
# آمار کلی
# =====================================================

def get_total_income():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'درآمد'")
    total = cursor.fetchone()[0]
    conn.close()
    return total or 0


def get_total_expense():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'هزینه'")
    total = cursor.fetchone()[0]
    conn.close()
    return total or 0


def get_total_balance():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT SUM(balance) FROM accounts")
    total = cursor.fetchone()[0]
    conn.close()
    return total or 0


def get_expense_by_category():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT category, SUM(amount)
        FROM transactions
        WHERE type = 'هزینه'
        GROUP BY category
    """)

    result = cursor.fetchall()
    conn.close()
    return result


def get_last_transactions(num):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, account_id, date, type, category,
               amount, place, description, balance_after
        FROM transactions
        ORDER BY date DESC
        LIMIT ?
    """, (num,))

    result = cursor.fetchall()
    conn.close()
    return result


if __name__ == "__main__":
    create_tables()
    print("دیتابیس و جدول‌ها با موفقیت ایجاد شدند.")
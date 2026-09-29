# reports.py
"""گزارش‌ها"""

from core.database import get_connection


def get_financial_report(account_id, start_date, end_date):
    if len(end_date) == 10:
        end_date = end_date + " 23:59"

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            SUM(CASE WHEN type = 'درآمد' THEN amount ELSE 0 END),
            SUM(CASE WHEN type = 'هزینه' THEN amount ELSE 0 END)
        FROM transactions
        WHERE account_id = ?
        AND date >= ? AND date <= ?
    """, (account_id, start_date, end_date))

    result = cursor.fetchone()
    conn.close()

    income = result[0] if result[0] else 0
    expense = result[1] if result[1] else 0
    balance = income - expense

    return income, expense, balance


def get_transaction_report():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            transactions.id,
            accounts.name,
            accounts.bank,
            transactions.type,
            transactions.category,
            transactions.amount,
            transactions.place,
            transactions.description,
            transactions.date
        FROM transactions
        JOIN accounts ON transactions.account_id = accounts.id
        ORDER BY transactions.date DESC
    """)

    result = cursor.fetchall()
    conn.close()
    return result


def get_monthly_report(year, month):
    conn = get_connection()
    cursor = conn.cursor()

    month_str = f"{year}-{month:02d}"

    cursor.execute("""
        SELECT
            accounts.name,
            type,
            category,
            amount,
            date
        FROM transactions
        JOIN accounts ON transactions.account_id = accounts.id
        WHERE substr(date, 1, 7) = ?
        ORDER BY date DESC
    """, (month_str,))

    result = cursor.fetchall()
    conn.close()
    return result


def get_category_report(account_id, start_date, end_date):
    if len(end_date) == 10:
        end_date = end_date + " 23:59"

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT category, SUM(amount)
        FROM transactions
        WHERE account_id = ?
        AND type = 'هزینه'
        AND date >= ? AND date <= ?
        GROUP BY category
        ORDER BY SUM(amount) DESC
    """, (account_id, start_date, end_date))

    result = cursor.fetchall()
    conn.close()
    return result


def get_financial_summary():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE type = 'درآمد'
    """)
    total_income = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COALESCE(SUM(amount), 0)
        FROM transactions
        WHERE type = 'هزینه'
    """)
    total_expense = cursor.fetchone()[0]

    conn.close()
    return total_income, total_expense


def get_account_report(account_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            accounts.name,
            accounts.bank,
            transactions.type,
            transactions.category,
            transactions.amount,
            transactions.place,
            transactions.description,
            transactions.date
        FROM transactions
        JOIN accounts ON transactions.account_id = accounts.id
        WHERE accounts.id = ?
        ORDER BY transactions.date DESC
    """, (account_id,))

    result = cursor.fetchall()
    conn.close()
    return result
# services.py
"""سرویس‌های منطق کسب‌وکار"""

from core.validators import (
    validate_account,
    validate_amount,
    validate_transaction_type,
)

from core.database import (
    add_transaction,
    search_transactions,
    search_by_date,
    search_by_date_range,
    search_by_description,
    search_by_type,
    update_account,
    get_account_by_id,
    update_balance,
    load_accounts,
    set_setting,
    get_setting,
    get_connection,
)

from core.reports import (
    get_transaction_report,
    get_financial_summary,
    get_account_report,
    get_category_report,
)

# =====================================================
# نمایش گزارش‌ها
# =====================================================

def show_account_report(account_id):
    return get_account_report(account_id)


def show_financial_summary():
    return get_financial_summary()


def show_transaction_report():
    return get_transaction_report()


def show_category_report(account_id, start_date, end_date):
    return get_category_report(account_id, start_date, end_date)


# =====================================================
# ثبت تراکنش (درآمد / هزینه / پس‌انداز)
# =====================================================

def register_transaction(account_id, date, trans_type, category,
                         amount, place, description):
    if not validate_account(account_id):
        raise ValueError("شناسه حساب معتبر نیست.")

    if not validate_amount(amount):
        raise ValueError("مبلغ باید بزرگ‌تر از صفر باشد.")

    if trans_type not in ("درآمد", "هزینه", "پس‌انداز"):
        raise ValueError("نوع تراکنش باید درآمد، هزینه یا پس‌انداز باشد.")

    conn = get_connection()
    try:
        account = get_account_by_id(account_id, conn=conn)
        if account is None:
            raise ValueError("حساب پیدا نشد.")

        current_balance = account[4]

        if trans_type == "درآمد":
            new_balance = current_balance + amount
        else:
            if current_balance < amount:
                raise ValueError("موجودی حساب کافی نیست.")
            new_balance = current_balance - amount

        add_transaction(
            account_id, date, trans_type, category,
            amount, place, description, new_balance, conn=conn
        )

        update_account(
            account_id, account[1], account[2],
            account[3], new_balance, account[5], conn=conn
        )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return True


# =====================================================
# ثبت انتقال بین دو حساب
# =====================================================

def register_transfer(source_account_id, destination_account_id,
                      date, amount, description=""):
    if not validate_account(source_account_id):
        raise ValueError("حساب مبدأ معتبر نیست.")

    if not validate_account(destination_account_id):
        raise ValueError("حساب مقصد معتبر نیست.")

    if source_account_id == destination_account_id:
        raise ValueError("حساب مبدأ و مقصد نمی‌توانند یکسان باشند.")

    if not validate_amount(amount):
        raise ValueError("مبلغ باید بزرگ‌تر از صفر باشد.")

    conn = get_connection()
    try:
        source_account = get_account_by_id(source_account_id, conn=conn)
        destination_account = get_account_by_id(destination_account_id, conn=conn)

        if source_account is None:
            raise ValueError("حساب مبدأ پیدا نشد.")
        if destination_account is None:
            raise ValueError("حساب مقصد پیدا نشد.")

        source_balance = source_account[4]
        if source_balance < amount:
            raise ValueError("موجودی حساب مبدأ کافی نیست.")

        new_source_balance = source_balance - amount
        new_destination_balance = destination_account[4] + amount

        update_account(
            source_account_id, source_account[1], source_account[2],
            source_account[3], new_source_balance, source_account[5],
            conn=conn
        )

        update_account(
            destination_account_id, destination_account[1],
            destination_account[2], destination_account[3],
            new_destination_balance, destination_account[5],
            conn=conn
        )

        add_transaction(
            source_account_id, date, "انتقال", "انتقال",
            amount, "", description, new_source_balance, conn=conn
        )

        add_transaction(
            destination_account_id, date, "انتقال", "انتقال",
            amount, "", description, new_destination_balance, conn=conn
        )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return True


# =====================================================
# حساب پس‌انداز ثابت
# =====================================================

SAVINGS_ACCOUNT_SETTING_KEY = "savings_account_id"


def set_savings_account(account_id):
    if not validate_account(account_id):
        raise ValueError("شناسه حساب معتبر نیست.")
    set_setting(SAVINGS_ACCOUNT_SETTING_KEY, account_id)
    return True


def get_savings_account_id():
    value = get_setting(SAVINGS_ACCOUNT_SETTING_KEY)
    if value is None:
        return None
    account_id = int(value)
    if get_account_by_id(account_id) is None:
        return None
    return account_id


# =====================================================
# ثبت پس‌انداز
# =====================================================

def register_saving(account_id, amount, category, place, description, date):
    savings_account_id = get_savings_account_id()
    if savings_account_id is None:
        raise ValueError("ابتدا باید یک حساب پس‌انداز تعیین کنید.")

    if not validate_account(account_id):
        raise ValueError("شناسه حساب معتبر نیست.")

    if account_id == savings_account_id:
        raise ValueError("حساب مبدأ نمی‌تواند همان حساب پس‌انداز باشد.")

    if not validate_amount(amount):
        raise ValueError("مبلغ معتبر نیست.")

    conn = get_connection()
    try:
        source_account = get_account_by_id(account_id, conn=conn)
        savings_account = get_account_by_id(savings_account_id, conn=conn)

        if source_account is None:
            raise ValueError("حساب مبدأ پیدا نشد.")
        if savings_account is None:
            raise ValueError("حساب پس‌انداز پیدا نشد.")

        source_balance = source_account[4]
        if source_balance < amount:
            raise ValueError("موجودی حساب مبدأ کافی نیست.")

        new_source_balance = source_balance - amount
        new_savings_balance = savings_account[4] + amount

        update_account(
            source_account[0], source_account[1], source_account[2],
            source_account[3], new_source_balance, source_account[5],
            conn=conn
        )
        update_account(
            savings_account[0], savings_account[1], savings_account[2],
            savings_account[3], new_savings_balance, savings_account[5],
            conn=conn
        )

        add_transaction(
            account_id, date, "پس‌انداز", category,
            amount, place, description, new_source_balance, conn=conn
        )
        add_transaction(
            savings_account_id, date, "پس‌انداز", category,
            amount, place, description, new_savings_balance, conn=conn
        )

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return True


# =====================================================
# توابع کمکی ویرایش تراکنش
# =====================================================

MOVE_TYPES = ("انتقال", "پس‌انداز")


def _fetch_transaction(conn, transaction_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, account_id, date, type, category, amount, place, description
        FROM transactions
        WHERE id = ?
    """, (transaction_id,))
    return cursor.fetchone()


def _find_paired_transaction(conn, transaction):
    t_id, account_id, date, trans_type, _, amount, _, _ = transaction

    if trans_type not in MOVE_TYPES:
        return None

    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, account_id, date, type, category, amount, place, description
        FROM transactions
        WHERE date = ? AND type = ? AND amount = ?
          AND account_id != ? AND id != ?
        ORDER BY ABS(id - ?) ASC
        LIMIT 1
    """, (date, trans_type, amount, account_id, t_id, t_id))

    return cursor.fetchone()


def get_transaction_sides(transaction_id):
    conn = get_connection()
    try:
        transaction = _fetch_transaction(conn, transaction_id)
        if transaction is None:
            return None, None

        pair = _find_paired_transaction(conn, transaction)
        if pair is None:
            return transaction[1], None

        if transaction[0] < pair[0]:
            return transaction[1], pair[1]
        return pair[1], transaction[1]
    finally:
        conn.close()


def apply_transaction_edit(transaction_id, new_type, new_category,
                           new_amount, new_place, new_description,
                           new_dest_account_id=None):
    conn = get_connection()
    try:
        cursor = conn.cursor()

        transaction = _fetch_transaction(conn, transaction_id)
        if transaction is None:
            raise ValueError("تراکنش پیدا نشد.")

        _, t_account_id, t_date, t_type, _, t_amount, _, _ = transaction
        pair = _find_paired_transaction(conn, transaction)

        if pair is not None and transaction[0] < pair[0]:
            origin_tx, dest_tx = transaction, pair
        elif pair is not None:
            origin_tx, dest_tx = pair, transaction
        else:
            origin_tx, dest_tx = transaction, None

        balances = {}

        def balance_of(account_id):
            if account_id not in balances:
                account = get_account_by_id(account_id, conn=conn)
                if account is None:
                    raise ValueError("یکی از حساب‌های این تراکنش پیدا نشد.")
                balances[account_id] = account[4]
            return balances[account_id]

        if dest_tx is not None:
            balances[origin_tx[1]] = balance_of(origin_tx[1]) + t_amount
            balances[dest_tx[1]] = balance_of(dest_tx[1]) - t_amount
        elif t_type == "درآمد":
            balances[t_account_id] = balance_of(t_account_id) - t_amount
        else:
            balances[t_account_id] = balance_of(t_account_id) + t_amount

        if new_type in MOVE_TYPES:
            origin_account_id = origin_tx[1]

            if new_type == "پس‌انداز":
                destination_account_id = get_savings_account_id()
                if destination_account_id is None:
                    raise ValueError("ابتدا باید یک حساب پس‌انداز تعیین کنید.")
            else:
                destination_account_id = new_dest_account_id

            if destination_account_id is None:
                raise ValueError("حساب مقصد را انتخاب کنید.")
            if destination_account_id == origin_account_id:
                raise ValueError("حساب مبدأ و مقصد نمی‌توانند یکسان باشند.")

            balances[origin_account_id] = \
                balance_of(origin_account_id) - new_amount
            balances[destination_account_id] = \
                balance_of(destination_account_id) + new_amount

            cursor.execute("""
                UPDATE transactions
                SET account_id = ?, date = ?, type = ?, category = ?,
                    amount = ?, place = ?, description = ?, balance_after = ?
                WHERE id = ?
            """, (origin_account_id, t_date, new_type, new_category,
                  new_amount, new_place, new_description,
                  balances[origin_account_id], origin_tx[0]))

            if dest_tx is not None:
                cursor.execute("""
                    UPDATE transactions
                    SET account_id = ?, date = ?, type = ?, category = ?,
                        amount = ?, place = ?, description = ?,
                        balance_after = ?
                    WHERE id = ?
                """, (destination_account_id, t_date, new_type, new_category,
                      new_amount, new_place, new_description,
                      balances[destination_account_id], dest_tx[0]))
            else:
                cursor.execute("""
                    INSERT INTO transactions
                       (account_id, date, type, category, amount,
                        place, description, balance_after)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (destination_account_id, t_date, new_type, new_category,
                      new_amount, new_place, new_description,
                      balances[destination_account_id]))
        else:
            if new_type == "درآمد":
                balances[t_account_id] = balance_of(t_account_id) + new_amount
            else:
                balances[t_account_id] = balance_of(t_account_id) - new_amount

            cursor.execute("""
                UPDATE transactions
                SET account_id = ?, date = ?, type = ?, category = ?,
                    amount = ?, place = ?, description = ?, balance_after = ?
                WHERE id = ?
            """, (t_account_id, t_date, new_type, new_category,
                  new_amount, new_place, new_description,
                  balances[t_account_id], transaction_id))

            if pair is not None:
                cursor.execute("DELETE FROM transactions WHERE id = ?",
                               (pair[0],))

        for account_id, balance in balances.items():
            if balance < 0:
                account = get_account_by_id(account_id, conn=conn)
                account_name = account[1] if account else account_id
                raise ValueError(
                    f"موجودی حساب «{account_name}» برای این تغییر کافی نیست."
                )

        for account_id, balance in balances.items():
            cursor.execute("UPDATE accounts SET balance = ? WHERE id = ?",
                           (balance, account_id))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return True


# =====================================================
# ✅ تابع جدید: حذف تراکنش با بازگرداندن اثر
# =====================================================

def delete_transaction_with_revert(transaction_id):
    """
    حذف یک تراکنش و برگرداندن اثر آن روی موجودی حساب‌ها.
    برای انتقال/پس‌انداز، هر دو طرف حذف می‌شوند.
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        transaction = _fetch_transaction(conn, transaction_id)
        if transaction is None:
            raise ValueError("تراکنش پیدا نشد.")

        _, t_account_id, t_date, t_type, _, t_amount, _, _ = transaction
        pair = _find_paired_transaction(conn, transaction)

        balances = {}

        def balance_of(account_id):
            if account_id not in balances:
                account = get_account_by_id(account_id, conn=conn)
                if account is None:
                    raise ValueError("یکی از حساب‌ها پیدا نشد.")
                balances[account_id] = account[4]
            return balances[account_id]

        # برگرداندن اثر تراکنش
        if pair is not None:
            # انتقال/پس‌انداز: هر دو طرف
            balances[t_account_id] = balance_of(t_account_id) + t_amount
            balances[pair[1]] = balance_of(pair[1]) - t_amount
            cursor.execute("DELETE FROM transactions WHERE id = ?", (pair[0],))
        elif t_type == "درآمد":
            balances[t_account_id] = balance_of(t_account_id) - t_amount
        else:  # هزینه
            balances[t_account_id] = balance_of(t_account_id) + t_amount

        # حذف تراکنش اصلی
        cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))

        # بررسی منفی نشدن
        for account_id, balance in balances.items():
            if balance < 0:
                account = get_account_by_id(account_id, conn=conn)
                account_name = account[1] if account else account_id
                raise ValueError(
                    f"موجودی حساب «{account_name}» برای حذف کافی نیست."
                )

        # بروزرسانی موجودی‌ها
        for account_id, balance in balances.items():
            cursor.execute("UPDATE accounts SET balance = ? WHERE id = ?",
                           (balance, account_id))

        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    return True


# =====================================================
# جستجوها
# =====================================================

def show_search_result(start_date=None, end_date=None, trans_type=None,
                       category=None, min_amount=None, max_amount=None):
    result = search_transactions(
        start_date, end_date, trans_type, category, min_amount, max_amount
    )

    if not result:
        print("\nهیچ تراکنشی پیدا نشد.")
        return

    print("\n===== نتیجه جستجو =====")
    for row in result:
        print("-" * 60)
        print(f"شناسه: {row[0]}")
        print(f"حساب: {row[1]}")
        print(f"تاریخ: {row[2]}")
        print(f"نوع: {row[3]}")
        print(f"دسته‌بندی: {row[4]}")
        print(f"مبلغ: {row[5]:,.0f} تومان")
        print(f"محل: {row[6]}")
        print(f"توضیحات: {row[7]}")


def search_date(account_id, date):
    return search_by_date(account_id, date)


def show_search_by_date(account_id, date):
    print_transactions(search_by_date(account_id, date))


def show_search_by_date_range(account_id, start_date, end_date):
    print_transactions(search_by_date_range(account_id, start_date, end_date))


def show_search_by_type(account_id, trans_type):
    print_transactions(search_by_type(account_id, trans_type))


def show_search_by_description(account_id, text):
    print_transactions(search_by_description(account_id, text))


def print_transaction(row):
    print("-" * 60)
    print(f"شناسه: {row[0]}")
    print(f"حساب: {row[1]}")
    print(f"تاریخ: {row[2]}")
    print(f"نوع: {row[3]}")
    print(f"دسته‌بندی: {row[4]}")
    print(f"مبلغ: {row[5]:,.0f} تومان")
    print(f"محل: {row[6]}")
    print(f"توضیحات: {row[7]}")


def print_transactions(result):
    if not result:
        print("تراکنشی یافت نشد.")
        return
    for row in result:
        print_transaction(row)


# =====================================================
# انتخاب حساب و ویرایش
# =====================================================

def select_account():
    accounts = load_accounts()

    if not accounts:
        print("هیچ حسابی ثبت نشده است.")
        return None

    print("\n===== حساب‌ها =====")
    for account in accounts:
        print(f"{account[0]} - {account[1]} ({account[2]})")

    while True:
        try:
            account_id = int(input("شناسه حساب را وارد کنید: "))
            for account in accounts:
                if account[0] == account_id:
                    return account_id
            print("شناسه حساب معتبر نیست.")
        except ValueError:
            print("لطفاً یک عدد وارد کنید.")


def edit_account(account_id, name, bank, card_number, balance, account_type):
    update_account(account_id, name, bank, card_number, balance, account_type)
    print("کارت با موفقیت ویرایش شد.")


def show_account(account_id):
    account = get_account_by_id(account_id)
    if account is None:
        print("کارتی با این شناسه پیدا نشد.")
        return None

    print("\n===== اطلاعات کارت =====")
    print(f"شناسه: {account[0]}")
    print(f"نام: {account[1]}")
    print(f"بانک: {account[2]}")
    print(f"شماره کارت: {account[3]}")
    print(f"موجودی: {account[4]:,.0f}")
    print(f"نوع حساب: {account[5]}")

    return account
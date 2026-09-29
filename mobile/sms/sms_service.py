# sms/sms_service.py
"""سرویس مدیریت پیامک‌های بانکی"""

import json
from datetime import datetime
from core import database, services
from sms import sms_parser



def add_sms_to_queue(sender, body):
    """
    پیامک جدید رو به صف اضافه می‌کنه.
    
    اگر شماره حساب قبلاً به کارتی وصل شده باشد،
    خودکار ثبت می‌شود و به صف نمی‌رود.
    
    خروجی:
    - sms_id اگر به صف اضافه شد
    - ("auto", account_id) اگر خودکار ثبت شد
    - None اگر غیربانکی یا تکراری بود
    """
    # چک بانکی
    if not sms_parser.is_bank_sms(body, sender):
        return None
    
    # پارس
    parsed = sms_parser.parse_sms(body, sender)
    if not parsed:
        return None
    
    # چک تکراری
    ref_code = parsed.get("reference_code")
    if ref_code:
        conn = database.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id FROM sms_queue
            WHERE body LIKE ? AND status != 'rejected'
        """, (f"%{ref_code}%",))
        if cursor.fetchone():
            conn.close()
            return None
        conn.close()
    
    # چک اتصال خودکار
    account_number = parsed.get("account_number")
    if account_number:
        mapped_account_id = get_mapped_account(account_number)
        if mapped_account_id:
            # خودکار ثبت کن
            try:
                # اضافه به صف با status approved
                conn = database.get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO sms_queue
                    (sender, body, received_at, status, parsed_amount,
                     parsed_type, parsed_card, account_id, raw_parsed)
                    VALUES (?, ?, ?, 'approved', ?, ?, ?, ?, ?)
                """, (
                    sender, body,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    parsed.get("amount"),
                    parsed.get("type"),
                    parsed.get("card_last4"),
                    mapped_account_id,
                    json.dumps(parsed, ensure_ascii=False, default=str),
                ))
                sms_id = cursor.lastrowid
                conn.commit()
                conn.close()
                
                # ثبت تراکنش
                services.register_transaction(
                    account_id=mapped_account_id,
                    date=datetime.now().strftime("%Y-%m-%d %H:%M"),
                    trans_type=parsed.get("type", "هزینه"),
                    category="پیامک بانکی (خودکار)",
                    amount=parsed.get("amount", 0),
                    place=parsed.get("bank", ""),
                    description=body[:100],
                )
                
                return ("auto", mapped_account_id)
            except Exception as e:
                print(f"خطا در ثبت خودکار: {e}")
                # اگر خطا خورد، به صف عادی اضافه کن
                pass
    
    # اضافه به صف عادی
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO sms_queue
        (sender, body, received_at, status, parsed_amount,
         parsed_type, parsed_card, raw_parsed)
        VALUES (?, ?, ?, 'pending', ?, ?, ?, ?)
    """, (
        sender, body,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        parsed.get("amount"),
        parsed.get("type"),
        parsed.get("card_last4"),
        json.dumps(parsed, ensure_ascii=False, default=str),
    ))
    sms_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return sms_id


def get_pending_sms():
    """لیست پیامک‌های در انتظار تأیید"""
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, sender, body, received_at, parsed_amount,
               parsed_type, parsed_card
        FROM sms_queue
        WHERE status = 'pending'
        ORDER BY received_at DESC
    """)
    result = cursor.fetchall()
    conn.close()
    return result


def get_all_sms(limit=50):
    """همه‌ی پیامک‌ها"""
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, sender, body, received_at, status,
               parsed_amount, parsed_type, parsed_card
        FROM sms_queue
        ORDER BY received_at DESC
        LIMIT ?
    """, (limit,))
    result = cursor.fetchall()
    conn.close()
    return result


def find_matching_account(card_last4):
    """پیدا کردن کارتی که ۴ رقم آخرش با پیامک مطابقت داره"""
    if not card_last4:
        return None
    
    accounts = database.load_accounts()
    for acc in accounts:
        card_number = acc[3] or ""
        if card_number.endswith(card_last4):
            return acc[0]
    
    return None



def approve_sms(sms_id, account_id, save_mapping=True):
    """
    تأیید پیامک و ثبت.
    
    اگر save_mapping=True باشه، اتصال شماره حساب به کارت
    ذخیره می‌شه تا دفعه‌ی بعد خودکار انجام بشه.
    """
    conn = database.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT body, parsed_amount, parsed_type, parsed_card,
               raw_parsed, sender
        FROM sms_queue
        WHERE id = ?
    """, (sms_id,))
    
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise ValueError("پیامک پیدا نشد.")
    
    body, amount, trans_type, card_last4, raw_parsed, sender = row
    
    if not amount or not trans_type:
        conn.close()
        raise ValueError("اطلاعات پیامک کامل نیست.")
    
    # بررسی کارت
    account = database.get_account_by_id(account_id)
    if not account:
        conn.close()
        raise ValueError("کارت پیدا نشد.")
    
    # ثبت تراکنش
    try:
        parsed = json.loads(raw_parsed) if raw_parsed else {}
        
        services.register_transaction(
            account_id=account_id,
            date=datetime.now().strftime("%Y-%m-%d %H:%M"),
            trans_type=trans_type,
            category="پیامک بانکی",
            amount=amount,
            place=parsed.get("bank", ""),
            description=body[:100],
        )
    except Exception as e:
        conn.close()
        raise ValueError(f"خطا در ثبت: {e}")
    
    # به‌روزرسانی وضعیت
    cursor.execute("""
        UPDATE sms_queue
        SET status = 'approved', account_id = ?
        WHERE id = ?
    """, (account_id, sms_id))
    conn.commit()
    conn.close()
    
    # ذخیره اتصال (یادگیری)
    if save_mapping:
        parsed = json.loads(raw_parsed) if raw_parsed else {}
        account_number = parsed.get("account_number")
        bank_name = parsed.get("bank", "") or sms_parser.detect_bank(sender, body)
        
        if account_number:
            save_account_mapping(
                account_number=account_number,
                card_last4=card_last4 or "",
                account_id=account_id,
                bank_name=bank_name,
                auto_approve=1,
            )
        elif card_last4:
            # اگر فقط ۴ رقم آخر داشتیم
            save_account_mapping(
                account_number=f"card_{card_last4}",
                card_last4=card_last4,
                account_id=account_id,
                bank_name=bank_name,
                auto_approve=1,
            )
    
    return True  

def reject_sms(sms_id):
    """رد پیامک"""
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE sms_queue
        SET status = 'rejected'
        WHERE id = ?
    """, (sms_id,))
    conn.commit()
    conn.close()
    return True


def get_sms_count():
    """تعداد پیامک‌های در انتظار"""
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM sms_queue WHERE status = 'pending'")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def delete_sms(sms_id):
    """حذف کامل پیامک از صف"""
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sms_queue WHERE id = ?", (sms_id,))
    conn.commit()
    conn.close()
    return True

def save_account_mapping(account_number, card_last4, account_id,
                          bank_name="", auto_approve=1):
    """
    ذخیره‌ی اتصال شماره حساب به کارت.
    """
    conn = database.get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO sms_account_mapping
        (account_number, card_last4, account_id, bank_name,
         auto_approve, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(account_number) DO UPDATE SET
            account_id = excluded.account_id,
            auto_approve = excluded.auto_approve
    """, (
        account_number, card_last4, account_id, bank_name,
        auto_approve,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    ))
    
    conn.commit()
    conn.close()
    return True


def get_mapped_account(account_number):
    """
    پیدا کردن کارت متصل به شماره حساب.
    خروجی: account_id یا None
    """
    if not account_number:
        return None
    
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT account_id FROM sms_account_mapping
        WHERE account_number = ? AND auto_approve = 1
    """, (account_number,))
    row = cursor.fetchone()
    conn.close()
    
    return row[0] if row else None


def get_all_mappings():
    """لیست همه‌ی اتصال‌ها"""
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.id, m.account_number, m.card_last4,
               m.account_id, a.name, m.bank_name, m.auto_approve
        FROM sms_account_mapping m
        LEFT JOIN accounts a ON m.account_id = a.id
        ORDER BY m.created_at DESC
    """)
    result = cursor.fetchall()
    conn.close()
    return result


def delete_mapping(mapping_id):
    """حذف اتصال"""
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sms_account_mapping WHERE id = ?",
                   (mapping_id,))
    conn.commit()
    conn.close()
    return True


def update_mapping_auto_approve(mapping_id, auto_approve):
    """تغییر وضعیت ثبت خودکار"""
    conn = database.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE sms_account_mapping
        SET auto_approve = ?
        WHERE id = ?
    """, (auto_approve, mapping_id))
    conn.commit()
    conn.close()
    return True
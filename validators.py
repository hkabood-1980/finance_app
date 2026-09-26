# validators.py
"""اعتبارسنجی ورودی‌ها"""

from database import get_account_by_id


def validate_account(account_id):
    """بررسی وجود حساب با شناسه مشخص"""
    if account_id is None:
        return False
    account = get_account_by_id(account_id)
    return account is not None


def validate_amount(amount):
    """بررسی معتبر بودن مبلغ"""
    try:
        amount = float(amount)
        return amount > 0
    except (ValueError, TypeError):
        return False


def validate_transaction_type(trans_type):
    """بررسی معتبر بودن نوع تراکنش"""
    valid_types = ["درآمد", "هزینه", "انتقال", "پس‌انداز"]
    return trans_type in valid_types
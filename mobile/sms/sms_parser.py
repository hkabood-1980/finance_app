# sms/sms_parser.py
"""
پارسر هوشمند پیامک بانکی — پشتیبانی از همه‌ی بانک‌های ایرانی
"""

import re


# =====================================================
# ۱. نرمال‌سازی متن
# =====================================================

def normalize_text(text):
    """نرمال‌سازی کامل متن پیامک"""
    if not text:
        return ""
    
    # حذف کاراکترهای مخفی Unicode
    invisible_chars = [
        "\u200b", "\u200c", "\u200d",
        "\u200e", "\u200f",
        "\u202a", "\u202b", "\u202c",
        "\u202d", "\u202e",
        "\u2066", "\u2067", "\u2068", "\u2069",
        "\ufeff",
    ]
    for char in invisible_chars:
        text = text.replace(char, "")
    
    # حروف عربی → فارسی
    replacements = {
        "ي": "ی", "ك": "ک", "ﻻ": "لا",
        "ة": "ه", "ۀ": "ه", "ؤ": "و",
        "إ": "ا", "أ": "ا", "ٱ": "ا",
    }
    for arabic, persian in replacements.items():
        text = text.replace(arabic, persian)
    
    # اعداد فارسی/عربی → انگلیسی
    persian_digits = "۰۱۲۳۴۵۶۷۸۹"
    arabic_digits = "٠١٢٣٤٥٦٧٨٩"
    for i in range(10):
        text = text.replace(persian_digits[i], str(i))
        text = text.replace(arabic_digits[i], str(i))
    
    # جداکننده‌های عددی
    text = text.replace("،", ",").replace("٬", ",")
    
    # یکسان‌سازی فاصله‌ها
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text)
    
    return text.strip()


# =====================================================
# ۲. تشخیص پیامک بانکی
# =====================================================

NON_BANK_SENDERS = [
    "ایرانسل", "همراه اول", "رایتل", "شاتل", "آسیاتک",
    "MTN", "MCI", "Irancell", "Rightel",
    "دیجی‌کالا", "بامیلو", "اسنپ", "تپسی",
    "اسنپ‌فود", "علی‌بابا", "کافه‌بازار",
]

NON_BANK_KEYWORDS = [
    "رمز پویا", "رمز پويا", "رمز یکبار مصرف",
    "اعتبار تا", "کد تایید", "کد ورود", "OTP",
    "شماره تایید", "کد فعال‌سازی", "کد فعال سازی",
    "تخفیف", "حراج", "فروش ویژه", "کد تخفیف",
]

BANK_KEYWORDS = [
    "بانک", "حساب", "کارت", "مانده", "موجودی",
    "واریز", "برداشت", "بستانکار", "بدهکار",
    "خرید", "پرداخت", "انتقال",
    "ریال", "تومان",
]


def is_bank_sms(body, sender=""):
    """تشخیص اینکه پیامک بانکی است یا نه"""
    if not body:
        return False
    
    text = normalize_text(body)
    
    for non_bank in NON_BANK_SENDERS:
        if non_bank in sender or non_bank in text:
            return False
    
    for keyword in NON_BANK_KEYWORDS:
        if keyword in text:
            return False
    
    bank_score = sum(1 for kw in BANK_KEYWORDS if kw in text)
    return bank_score >= 2


# =====================================================
# ۳. استخراج مبلغ (الگوی جدید و دقیق)
# =====================================================

def extract_amount(text):
    """
    استخراج مبلغ از متن پیامک.
    خروجی: (amount, unit, type, account_number, card_last4)
    
    ترتیب اولویت:
    1. الگوی جمله‌ای: "برداشت از کارت X به مبلغ Y"
    2. الگوی کلید:مقدار: "واریز:150,000,000" یا "برداشت:12,814,500"
    3. الگوی علامت: "+25,000,000" یا "-10,000,000"
    4. الگوی عمومی: "مبلغ X"
    """
    
    # =====================================================
    # ۱. الگوی جمله‌ای (اقتصاد نوین)
    # =====================================================
    sentence = re.search(
        r"(?:برداشت|واریز|خرید|پرداخت|دریافت|کسر|افزایش)\s+از\s+کارت\s+(\d{10,})\s+به\s+مبلغ\s+([\d,]+(?:\.\d+)?)\s*(ریال|تومان)?",
        text
    )
    if sentence:
        account = sentence.group(1)
        amount = float(sentence.group(2).replace(",", ""))
        unit = sentence.group(3) if sentence.group(3) else "ریال"
        # نوع از کلمه
        if "برداشت" in text or "خرید" in text or "پرداخت" in text:
            trans_type = "هزینه"
        else:
            trans_type = "درآمد"
        return amount, unit, trans_type, account, account[-4:]
    
  
    # =====================================================
    # ۲. الگوی کلید:مقدار با علامت بعد (ملی)
    # =====================================================
    keyword_sign = re.search(
        r"(?:واریز|برداشت|پرداخت|دریافت|کسر|افزایش|خرید|خريد|انتقال|انتقالی)\s*[:\s]\s*([\d,]+(?:\.\d+)?)\s*([+-])",
        text
    )
    if keyword_sign:
        amount = float(keyword_sign.group(1).replace(",", ""))
        sign = keyword_sign.group(2)
        unit = "ریال"
        trans_type = "درآمد" if sign == "+" else "هزینه"
        return amount, unit, trans_type, None, None
    
    # =====================================================
    # ۳. الگوی کلید:مقدار ساده (سپه، صادرات)
    # =====================================================
    keyword_pattern = re.search(
        r"(?:واریز|برداشت|پرداخت|دریافت|کسر|افزایش|خرید|خريد|انتقال|انتقالی)\s*[:\s]\s*([\d,]+(?:\.\d+)?)\s*(ریال|تومان)?",
        text
    )
    if keyword_pattern:
        amount = float(keyword_pattern.group(1).replace(",", ""))
        unit = keyword_pattern.group(2) if keyword_pattern.group(2) else "ریال"
        
        # نوع از کلمه
        if "واریز" in text or "دریافت" in text or "افزایش" in text:
            trans_type = "درآمد"
        else:
            trans_type = "هزینه"
        
        return amount, unit, trans_type, None, None      
    
    # =====================================================
    # ۳. الگوی علامت (پاسارگاد، ملی)
    # =====================================================
    # علامت قبل: +25,000,000
    sign_before = re.search(
        r"(?:^|\s)([+-])\s*([\d,]+(?:\.\d+)?)\s*(ریال|تومان)?",
        text
    )
    # علامت بعد: 4,548,650+
    sign_after = re.search(
        r"([\d,]+(?:\.\d+)?)\s*([+-])(?:\s|$)",
        text
    )
    
    if sign_before:
        sign = sign_before.group(1)
        amount = float(sign_before.group(2).replace(",", ""))
        unit = sign_before.group(3) if sign_before.group(3) else "ریال"
        trans_type = "درآمد" if sign == "+" else "هزینه"
        return amount, unit, trans_type, None, None
    
    if sign_after:
        amount = float(sign_after.group(1).replace(",", ""))
        sign = sign_after.group(2)
        unit = "ریال"
        trans_type = "درآمد" if sign == "+" else "هزینه"
        return amount, unit, trans_type, None, None
    
    # =====================================================
    # ۴. الگوی عمومی (مبلغ X)
    # =====================================================
    general = re.search(
        r"مبلغ\s*[:\s]\s*([\d,]+(?:\.\d+)?)\s*(ریال|تومان)?",
        text
    )
    if general:
        amount = float(general.group(1).replace(",", ""))
        unit = general.group(2) if general.group(2) else "ریال"
        return amount, unit, None, None, None
    
    # =====================================================
    # ۵. الگوی X ریال / تومان
    # =====================================================
    unit_pattern = re.search(
        r"([\d,]+(?:\.\d+)?)\s*(ریال|تومان)",
        text
    )
    if unit_pattern:
        amount = float(unit_pattern.group(1).replace(",", ""))
        unit = unit_pattern.group(2)
        return amount, unit, None, None, None
    
    return None, None, None, None, None


# =====================================================
# ۴. استخراج کد پیگیری
# =====================================================

def extract_reference(text):
    """استخراج کد پیگیری"""
    patterns = [
        r"(\d+\.\d+\.\d+\.\d+)",  # پاسارگاد
        r"رمز\s*[:\s]\s*(\d+)",  # صادرات
        r"کد\s*پیگیری\s*[:\s]\s*(\d+)",
        r"کدپیگیری\s*[:\s]\s*(\d+)",
        r"شماره\s*پیگیری\s*[:\s]\s*(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


# =====================================================
# ۵. استخراج مانده
# =====================================================

def extract_balance(text):
    """استخراج مانده"""
    match = re.search(
        r"مانده\s*[:\s]\s*([\d,]+(?:\.\d+)?)\s*(ریال|تومان)?",
        text
    )
    if match:
        balance = float(match.group(1).replace(",", ""))
        unit = match.group(2) if match.group(2) else "ریال"
        if unit == "ریال":
            balance = balance / 10
        return balance
    return None


# =====================================================
# ۶. استخراج شماره کارت
# =====================================================

def extract_card(text):
    """استخراج شماره کارت/حساب"""
    patterns = [
        r"از\s+کارت\s+(\d{13,})",
        r"کارت\s+(\d{13,})",
        r"حساب\s*[:\s]\s*(\d{10,})",
        r"حساب\s*[:\s]\s*(\d{4,})",
        r"کارت\s*[:\s]\s*(\d{4})\b",
        r"\*+(\d{4})\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            number = match.group(1)
            if len(number) >= 10:
                return number, number[-4:]
            return None, number
    return None, None


# =====================================================
# ۷. تابع اصلی پارس
# =====================================================

def parse_sms(body, sender=""):
    """پارس کامل پیامک بانکی"""
    if not body:
        return None
    
    if not is_bank_sms(body, sender):
        return None
    
    text = normalize_text(body)
    
    result = {
        "amount": None,
        "amount_unit": None,
        "type": None,
        "account_number": None,
        "card_last4": None,
        "balance": None,
        "reference_code": None,
        "raw": body,
        "normalized": text,
    }
    
    # ۱. استخراج مبلغ + نوع + شماره کارت
    amount, unit, trans_type, account, card_last4 = extract_amount(text)
    
    if amount is not None:
        if unit == "ریال":
            amount = amount / 10
            unit = "تومان"
        result["amount"] = amount
        result["amount_unit"] = unit
        result["type"] = trans_type
    
    if account:
        result["account_number"] = account
        result["card_last4"] = card_last4
    
    # ۲. اگر مبلغ از علامت تشخیص داده نشد، از کلمات کلیدی
    if result["type"] is None:
        income_kw = ["واریز", "بستانکار", "دریافت", "افزایش",
                     "دستورپرداخت وارده", "واریزی"]
        expense_kw = ["برداشت", "بدهکار", "پرداخت", "خرید", "خريد",
                      "کسر", "کسری", "پایانه فروش", "هزینه"]
        
        for kw in income_kw:
            if kw in text:
                result["type"] = "درآمد"
                break
        
        if result["type"] is None:
            for kw in expense_kw:
                if kw in text:
                    result["type"] = "هزینه"
                    break
    
    # ۳. اگر شماره کارت هنوز پیدا نشده
    if not result["card_last4"]:
        account, card_last4 = extract_card(text)
        if account:
            result["account_number"] = account
        if card_last4:
            result["card_last4"] = card_last4
    
    # ۴. مانده
    result["balance"] = extract_balance(text)
    
    # ۵. کد پیگیری
    result["reference_code"] = extract_reference(text)
    
    return result


# =====================================================
# ۸. تشخیص بانک
# =====================================================

BANK_SIGNATURES = {
    "سپه": ["سپه", "98300017"],
    "ملت": ["ملت", "98300098"],
    "صادرات": ["صادرات", "98300012"],
    "ملی": ["ملی", "98300011"],
    "پاسارگاد": ["پاسارگاد", "100085"],
    "پارسیان": ["پارسیان"],
    "سامان": ["سامان"],
    "تجارت": ["تجارت", "98300020"],
    "کشاورزی": ["کشاورزی", "98300016"],
    "رفاه": ["رفاه", "98300013"],
    "مسکن": ["مسکن"],
    "شهر": ["شهر"],
    "اقتصاد نوین": ["اقتصاد نوین", "اقتصادنوين"],
    "دی": ["بانک دی"],
    "سینا": ["سینا"],
    "آینده": ["آینده"],
    "قوامین": ["قوامین"],
    "حکمت": ["حکمت"],
    "ایران زمین": ["ایران زمین"],
    "کارآفرین": ["کارآفرین"],
    "گردشگری": ["گردشگری"],
    "صنعت و معدن": ["صنعت و معدن"],
    "پست بانک": ["پست بانک"],
    "بلوبانک": ["بلوبانک"],
    "رسالت": ["رسالت"],
    "مهر ایران": ["مهر ایران"],
}


def detect_bank(sender, body):
    """تشخیص نام بانک"""
    text = normalize_text(body)
    
    for bank_name, signatures in BANK_SIGNATURES.items():
        for sig in signatures:
            if sig in text:
                return bank_name
    
    for bank_name, signatures in BANK_SIGNATURES.items():
        for sig in signatures:
            if sig in sender:
                return bank_name
    
    return "نامشخص"


# =====================================================
# ۹. محاسبه اطمینان
# =====================================================

def calculate_confidence(parsed):
    """سطح اطمینان پارس"""
    if not parsed:
        return 0
    score = 0
    if parsed.get("amount"):
        score += 1
    if parsed.get("type"):
        score += 1
    if parsed.get("account_number") or parsed.get("card_last4"):
        score += 1
    if parsed.get("balance") or parsed.get("reference_code"):
        score += 1
    return score / 4


# =====================================================
# ۱۰. تست
# =====================================================

if __name__ == "__main__":
    samples = [
        ("98300017", """بانک سپه
واريز:150,000,000ريال
حساب:111560500251813
مانده:152,706,899
7/1-22:11
دستورپرداخت وارده پل کدپيگيري 1405070101330342"""),

        ("98300017", """بانک سپه
برداشت:12,814,500
حساب :‪111560500251813‬
مانده:139,892,399
7/1-22:36"""),

        ("100085", """777.888.15477428.1
-10,000,000
06/30_20:30
مانده: 273,968
بانک پاسارگاد"""),

        ("98300012", """بانک صادرات
پرداخت
قبوض تلفن ثابت
مبلغ 6,490,000
رمز 6103301"""),

        ("100085", """بانک اقتصادنوين
برداشت از کارت  6274124000706998 به مبلغ 1,500,000 ريال،
تاريخ 1404/1/11-14:58
مانده: 21,312,620 ريال"""),

        ("98300011", """بانك ملي ايران
انتقال:1,450,000+
حساب:09005
مانده:2,874,382
0322-19:43"""),

        ("1000", """خريد
ايرانسل
مبلغ: 263,732 ريال
رمز پويا:358591
اعتبار تا:17:40:16"""),
    ]

    for sender, body in samples:
        print("=" * 60)
        print(f"📩 از {sender}:")
        print(body[:80])
        print()

        parsed = parse_sms(body, sender)
        if parsed:
            print(f"   💰 مبلغ: {parsed['amount']:,.0f} {parsed['amount_unit']}")
            print(f"   🏷️ نوع: {parsed['type']}")
            if parsed.get('card_last4'):
                print(f"   💳 کارت: *{parsed['card_last4']}")
            if parsed.get('balance'):
                print(f"   📊 مانده: {parsed['balance']:,.0f}")
            if parsed.get('reference_code'):
                print(f"   🔖 پیگیری: {parsed['reference_code']}")
            print(f"   🏛️ بانک: {detect_bank(sender, body)}")
            print(f"   ✅ اطمینان: {calculate_confidence(parsed) * 100:.0f}%")
        else:
            print("   ❌ پیامک بانکی نیست")
        print()
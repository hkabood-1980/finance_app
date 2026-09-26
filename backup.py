# backup.py
"""
ماژول پشتیبان‌گیری و بازگردانی دیتابیس
پشتیبان‌ها به‌صورت فایل zip ذخیره می‌شوند.
"""
import sys
import os
import zipfile
import shutil
from datetime import datetime


# حداکثر تعداد پشتیبان‌های نگه‌داشته‌شده
MAX_BACKUPS = 10

# پسوند فایل پشتیبان
BACKUP_EXT = ".zip"

def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.join(os.environ['APPDATA'], 'FinanceApp')
    return os.path.join(os.path.dirname(__file__), 'data')

DB_NAME = os.path.join(get_app_dir(), 'finance.db')
BACKUP_DIR = os.path.join(get_app_dir(), 'backups')

def ensure_backup_dir():
    """اطمینان از وجود پوشه‌ی پشتیبان"""
    os.makedirs(BACKUP_DIR, exist_ok=True)


def get_backup_filename():
    """ساخت نام فایل پشتیبان با تاریخ و ساعت"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"backup_{timestamp}{BACKUP_EXT}"


def get_backup_path(filename):
    """مسیر کامل فایل پشتیبان"""
    return os.path.join(BACKUP_DIR, filename)


def create_backup():
    """
    ساخت نسخه‌ی پشتیبان از دیتابیس فعلی به‌صورت zip.
    خروجی: نام فایل پشتیبان یا None اگر دیتابیس وجود نداشت.
    """
    if not os.path.exists(DB_NAME):
        print("⚠️ دیتابیس اصلی وجود ندارد.")
        return None

    ensure_backup_dir()

    filename = get_backup_filename()
    backup_path = get_backup_path(filename)

    try:
        # ذخیره در zip
        with zipfile.ZipFile(backup_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(DB_NAME, arcname="finance.db")

        print(f"✅ پشتیبان ساخته شد: {filename}")

        # حذف پشتیبان‌های قدیمی اگر از حد گذشت
        cleanup_old_backups()

        return filename

    except Exception as e:
        print(f"❌ خطا در ساخت پشتیبان: {e}")
        return None


def list_backups():
    """
    لیست همه‌ی پشتیبان‌ها به ترتیب جدیدترین.
    خروجی: لیست دیکشنری با اطلاعات هر پشتیبان
    """
    ensure_backup_dir()

    backups = []

    for filename in os.listdir(BACKUP_DIR):
        if not filename.endswith(BACKUP_EXT):
            continue

        filepath = get_backup_path(filename)

        try:
            size = os.path.getsize(filepath)
            mtime = os.path.getmtime(filepath)
            date = datetime.fromtimestamp(mtime)

            backups.append({
                "filename": filename,
                "path": filepath,
                "size": size,
                "size_kb": round(size / 1024, 1),
                "date": date.strftime("%Y-%m-%d %H:%M:%S"),
                "timestamp": mtime,
            })
        except OSError:
            continue

    backups.sort(key=lambda x: x["timestamp"], reverse=True)
    return backups


def restore_backup(filename):
    """
    بازگردانی دیتابیس از یک فایل zip پشتیبان.
    خروجی: True اگر موفق، False اگر ناموفق.
    """
    backup_path = get_backup_path(filename)

    if not os.path.exists(backup_path):
        print(f"❌ فایل پشتیبان پیدا نشد: {filename}")
        return False

    try:
        # از دیتابیس فعلی هم پشتیبان بگیر (قبل از بازگردانی)
        if os.path.exists(DB_NAME):
            create_backup()
            print("ℹ️ از دیتابیس فعلی هم پشتیبان گرفته شد.")

        # استخراج zip و کپی روی دیتابیس اصلی
        with zipfile.ZipFile(backup_path, "r") as zf:
            with zf.open("finance.db") as src, open(DB_NAME, "wb") as dst:
                shutil.copyfileobj(src, dst)

        print(f"✅ دیتابیس از {filename} بازگردانی شد.")
        return True

    except Exception as e:
        print(f"❌ خطا در بازگردانی: {e}")
        return False


def delete_backup(filename):
    """
    حذف یک فایل پشتیبان.
    خروجی: True اگر موفق، False اگر ناموفق.
    """
    backup_path = get_backup_path(filename)

    if not os.path.exists(backup_path):
        print(f"❌ فایل پیدا نشد: {filename}")
        return False

    try:
        os.remove(backup_path)
        print(f"✅ پشتیبان حذف شد: {filename}")
        return True

    except Exception as e:
        print(f"❌ خطا در حذف: {e}")
        return False


def cleanup_old_backups():
    """حذف پشتیبان‌های قدیمی اگر تعداد از MAX_BACKUPS گذشت"""
    backups = list_backups()

    if len(backups) <= MAX_BACKUPS:
        return

    for backup in backups[MAX_BACKUPS:]:
        delete_backup(backup["filename"])
        print(f"🗑️ پشتیبان قدیمی حذف شد: {backup['filename']}")


def get_backup_count():
    """تعداد پشتیبان‌های موجود"""
    return len(list_backups())


def get_database_size():
    """حجم دیتابیس اصلی به کیلوبایت"""
    if not os.path.exists(DB_NAME):
        return 0
    return round(os.path.getsize(DB_NAME) / 1024, 1)


def should_auto_backup(hours=24):
    """
    آیا باید پشتیبان خودکار بگیریم؟
    اگر آخرین پشتیبان بیشتر از `hours` ساعت پیش بوده، True.
    """
    if not os.path.exists(DB_NAME):
        return False

    backups = list_backups()
    if not backups:
        return True

    last_backup_time = backups[0]["timestamp"]
    now = datetime.now().timestamp()
    return now - last_backup_time > hours * 3600


if __name__ == "__main__":
    print("📦 ماژول پشتیبان‌گیری (نسخه zip)")
    print(f"تعداد پشتیبان‌ها: {get_backup_count()}")
    print(f"حجم دیتابیس: {get_database_size()} KB")
    print(f"آیا پشتیبان خودکار لازم است؟ {should_auto_backup()}")

    name = create_backup()
    print(f"پشتیبان جدید: {name}")

    print("\n📋 لیست پشتیبان‌ها:")
    for b in list_backups():
        print(f"  - {b['filename']} ({b['size_kb']} KB) - {b['date']}")
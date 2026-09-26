# convert_icon.py
"""
تبدیل عکس png به فایل ico واقعی برای آیکون برنامه
"""

import os
from PIL import Image


def convert_to_ico(source_path="icon.png", output_path="icon.ico"):
    """تبدیل عکس png/jpg به ico چند‌اندازه"""
    
    # چک کردن وجود فایل ورودی
    if not os.path.exists(source_path):
        print(f"❌ فایل ورودی پیدا نشد: {source_path}")
        print("\n💡 راه‌حل:")
        print("   1. عکس png خود را با نام 'icon.png' در همین پوشه بگذار")
        print("   2. یا در کد، نام فایل را عوض کن")
        return False
    
    try:
        # باز کردن عکس
        img = Image.open(source_path)
        
        print(f"📷 فایل ورودی: {source_path}")
        print(f"   فرمت: {img.format}")
        print(f"   اندازه: {img.size[0]}x{img.size[1]}")
        print(f"   حالت: {img.mode}")
        print()
        
        # تبدیل به RGBA (برای شفافیت)
        if img.mode != "RGBA":
            img = img.convert("RGBA")
            print("🔄 تبدیل به RGBA انجام شد")
        
        # ذخیره به ico با چند اندازه
        sizes = [
            (256, 256),
            (128, 128),
            (64, 64),
            (48, 48),
            (32, 32),
            (16, 16),
        ]
        
        img.save(output_path, format="ICO", sizes=sizes)
        
        # بررسی نتیجه
        size_kb = os.path.getsize(output_path) / 1024
        print(f"✅ فایل ico ساخته شد: {output_path}")
        print(f"📦 حجم: {size_kb:.1f} KB")
        print(f"📐 اندازه‌ها: {', '.join(f'{s[0]}x{s[1]}' for s in sizes)}")
        
        return True
    
    except Exception as e:
        print(f"❌ خطا در تبدیل: {e}")
        return False


def verify_ico(icon_path="icon.ico"):
    """بررسی معتبر بودن فایل ico"""
    if not os.path.exists(icon_path):
        print(f"❌ فایل پیدا نشد: {icon_path}")
        return False
    
    with open(icon_path, "rb") as f:
        header = f.read(4)
    
    if header == b"\x00\x00\x01\x00":
        print(f"✅ فایل {icon_path} واقعاً ico است")
        return True
    else:
        print(f"❌ فایل {icon_path} ico نیست!")
        print(f"   header: {header.hex()}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("🎨 تبدیل عکس به آیکون ico")
    print("=" * 50)
    print()
    
    # تبدیل
    success = convert_to_ico("icon.png", "icon.ico")
    
    print()
    
    # بررسی
    if success:
        verify_ico("icon.ico")
    
    print()
    print("=" * 50)
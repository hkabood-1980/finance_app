# theme.py
"""
تنظیمات ظاهری برنامه — رنگ‌ها، فونت‌ها، تم‌ها
"""

import customtkinter as ctk


# =====================================================
# حالت ظاهری و تم رنگی
# =====================================================

APPEARANCE_MODE = "light"   # "light" یا "dark" یا "system"
COLOR_THEME = "blue"        # "blue", "green", "dark-blue"


def setup_appearance():
    """تنظیم حالت اولیه‌ی برنامه"""
    ctk.set_appearance_mode(APPEARANCE_MODE)
    ctk.set_default_color_theme("blue")


def toggle_appearance():
    """تغییر بین حالت روشن و تاریک"""
    current = ctk.get_appearance_mode()
    new_mode = "light" if current == "Dark" else "dark"
    ctk.set_appearance_mode(new_mode)
    return new_mode


# =====================================================
# رنگ‌های شاد و مدرن
# =====================================================

# رنگ اصلی (آبی درخشان)
COLOR_PRIMARY = "#3B82F6"
COLOR_PRIMARY_HOVER = "#2563EB"

# رنگ موفقیت (سبز)
COLOR_SUCCESS = "#10B981"
COLOR_SUCCESS_HOVER = "#059669"

# رنگ خطر (قرمز)
COLOR_DANGER = "#EF4444"
COLOR_DANGER_HOVER = "#DC2626"

# رنگ هشدار (نارنجی)
COLOR_WARNING = "#F59E0B"
COLOR_WARNING_HOVER = "#D97706"

# رنگ اطلاعات (بنفش)
COLOR_INFO = "#8B5CF6"
COLOR_INFO_HOVER = "#7C3AED"

# رنگ‌های تزئینی
COLOR_PINK = "#EC4899"
COLOR_CYAN = "#06B6D4"
COLOR_INDIGO = "#6366F1"

# رنگ‌های پس‌زمینه
BG_LIGHT = "#F8FAFC"
BG_DARK = "#0F172A"

# رنگ متن
TEXT_PRIMARY = "#1E293B"
TEXT_SECONDARY = "#64748B"
TEXT_WHITE = "#FFFFFF"


# =====================================================
# فونت‌ها
# =====================================================

FONT_FAMILY = "Tahoma"          # روی همه سیستم‌ها هست
FONT_FAMILY_FALLBACK = "Vazirmatn"  # اگر نصب باشد

FONT_TITLE = (FONT_FAMILY, 24, "bold")
FONT_SUBTITLE = (FONT_FAMILY, 16, "bold")
FONT_HEADING = (FONT_FAMILY, 14, "bold")
FONT_BODY = (FONT_FAMILY, 12)
FONT_SMALL = (FONT_FAMILY, 10)
FONT_BUTTON = (FONT_FAMILY, 13, "bold")


# =====================================================
# اندازه‌ها
# =====================================================

BUTTON_WIDTH = 200
BUTTON_HEIGHT = 45
BUTTON_CORNER = 12

WINDOW_WIDTH = 900
WINDOW_HEIGHT = 750
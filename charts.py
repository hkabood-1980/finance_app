# charts.py
"""ماژول رسم نمودارهای مالی"""

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from datetime import datetime
from database import get_connection


def setup_persian_font():
    try:
        persian_fonts = [
            'Tahoma', 'B Nazanin', 'BNazanin', 'B Mitra', 'B Yekan',
            'B Shahrzad', 'B Zar', 'Mitra', 'Yekan', 'Shahrzad',
            'Zar', 'Segoe UI', 'DejaVu Sans', 'Arial'
        ]

        available_fonts = [f.name for f in fm.fontManager.ttflist]
        found_font = None

        for font in persian_fonts:
            if font in available_fonts:
                found_font = font
                break

        if found_font:
            plt.rcParams['font.family'] = [found_font]
        else:
            plt.rcParams['font.family'] = ['DejaVu Sans', 'sans-serif']

        plt.rcParams['axes.unicode_minus'] = False

    except Exception as e:
        print(f"⚠️ خطا در تنظیم فونت: {e}")
        plt.rcParams['font.family'] = ['DejaVu Sans', 'sans-serif']
        plt.rcParams['axes.unicode_minus'] = False


# =====================================================
# دریافت داده‌ها
# =====================================================

def get_monthly_data(account_id, year, month):
    conn = get_connection()
    cursor = conn.cursor()

    month_str = f"{year}-{month:02d}"

    cursor.execute("""
        SELECT type, SUM(amount)
        FROM transactions
        WHERE account_id = ?
        AND substr(date, 1, 7) = ?
        GROUP BY type
    """, (account_id, month_str))

    result = cursor.fetchall()
    conn.close()

    data = {'درآمد': 0, 'هزینه': 0}
    for row in result:
        if row[0] in data:
            data[row[0]] = row[1]

    return data


def get_yearly_data(account_id, year):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT strftime('%m', date) as month, type, SUM(amount)
        FROM transactions
        WHERE account_id = ?
        AND strftime('%Y', date) = ?
        GROUP BY month, type
        ORDER BY month
    """, (account_id, str(year)))

    result = cursor.fetchall()
    conn.close()

    months = list(range(1, 13))
    income = [0] * 12
    expense = [0] * 12

    for row in result:
        month_idx = int(row[0]) - 1
        if row[1] == 'درآمد':
            income[month_idx] = row[2]
        elif row[1] == 'هزینه':
            expense[month_idx] = row[2]

    return months, income, expense


def get_category_chart_data(account_id, start_date, end_date):
    from reports import get_category_report
    return get_category_report(account_id, start_date, end_date)


# =====================================================
# رسم نمودارها
# =====================================================

def draw_pie_chart(data, title="نمودار دایره‌ای", account_name=""):
    setup_persian_font()

    if not data or sum(data.values()) == 0:
        print("داده‌ای برای نمایش وجود ندارد.")
        return

    labels = list(data.keys())
    values = list(data.values())
    colors = ['#4CAF50', '#f44336', '#2196F3', '#FF9800']

    plt.figure(figsize=(8, 8))
    wedges, texts, autotexts = plt.pie(
        values, labels=labels, autopct='%1.1f%%',
        colors=colors[:len(labels)], startangle=90,
        textprops={'fontsize': 12}
    )

    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(14)
        autotext.set_weight('bold')

    plt.title(f"{title}\n{account_name}", fontsize=16, pad=20)
    plt.axis('equal')
    plt.tight_layout()
    plt.show()


def draw_bar_chart(months, income, expense,
                   title="نمودار دخل و خرج", account_name=""):
    setup_persian_font()

    if sum(income) == 0 and sum(expense) == 0:
        print("داده‌ای برای نمایش وجود ندارد.")
        return

    x = range(len(months))
    width = 0.35

    fig, ax = plt.subplots(figsize=(14, 7))

    bars1 = ax.bar(x, income, width, label='درآمد', color='#4CAF50')
    bars2 = ax.bar([i + width for i in x], expense, width,
                   label='هزینه', color='#f44336')

    ax.set_xlabel('ماه', fontsize=12)
    ax.set_ylabel('مبلغ (تومان)', fontsize=12)
    ax.set_title(f"{title}\n{account_name}", fontsize=16, pad=20)
    ax.set_xticks([i + width/2 for i in x])
    ax.set_xticklabels([f"{i:02d}" for i in months])
    ax.legend(fontsize=12)
    ax.grid(True, alpha=0.3)

    max_inc = max(income) if max(income) > 0 else 1
    max_exp = max(expense) if max(expense) > 0 else 1

    for i, (inc, exp) in enumerate(zip(income, expense)):
        if inc > 0:
            ax.text(i, inc + max_inc/50, f'{inc:,.0f}',
                    ha='center', va='bottom', fontsize=9)
        if exp > 0:
            ax.text(i + width, exp + max_exp/50, f'{exp:,.0f}',
                    ha='center', va='bottom', fontsize=9)

    plt.tight_layout()
    plt.show()


def draw_donut_chart(data, title="نمودار دوناتی", account_name=""):
    setup_persian_font()

    if not data or sum(data.values()) == 0:
        print("داده‌ای برای نمایش وجود ندارد.")
        return

    labels = list(data.keys())
    values = list(data.values())
    colors = ['#4CAF50', '#f44336', '#2196F3', '#FF9800',
              '#9C27B0', '#00BCD4']

    plt.figure(figsize=(9, 9))
    wedges, texts, autotexts = plt.pie(
        values, labels=labels, autopct='%1.1f%%',
        colors=colors[:len(labels)], startangle=90,
        wedgeprops={'width': 0.5}, textprops={'fontsize': 11}
    )

    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontsize(13)
        autotext.set_weight('bold')

    plt.title(f"{title}\n{account_name}", fontsize=16, pad=20)
    plt.axis('equal')
    plt.tight_layout()
    plt.show()


def draw_combined_chart(months, income, expense,
                        title="نمودار ترکیبی", account_name=""):
    setup_persian_font()

    if sum(income) == 0 and sum(expense) == 0:
        print("داده‌ای برای نمایش وجود ندارد.")
        return

    x = list(range(len(months)))
    width = 0.35

    fig, ax1 = plt.subplots(figsize=(14, 7))

    bars1 = ax1.bar(x, income, width, label='درآمد',
                    color='#4CAF50', alpha=0.8)
    bars2 = ax1.bar([i + width for i in x], expense, width,
                    label='هزینه', color='#f44336', alpha=0.8)

    ax1.set_xlabel('ماه', fontsize=12)
    ax1.set_ylabel('مبلغ (تومان)', fontsize=12)
    ax1.set_title(f"{title}\n{account_name}", fontsize=16, pad=20)
    ax1.set_xticks([i + width/2 for i in x])
    ax1.set_xticklabels([f"{i:02d}" for i in months])
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    balance = [income[i] - expense[i] for i in range(len(months))]
    line, = ax2.plot(x, balance, 'b-', linewidth=2,
                     label='مانده', marker='o', markersize=8)
    ax2.set_ylabel('مانده (تومان)', fontsize=12, color='blue')
    ax2.tick_params(axis='y', labelcolor='blue')

    # ادغام legend دو محور
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2,
               loc='upper left', fontsize=11)

    plt.tight_layout()
    plt.show()


# =====================================================
# توابع نمایشی برای GUI
# =====================================================

def show_monthly_chart(account_id, account_name, year, month):
    data = get_monthly_data(account_id, year, month)
    title = f"دخل و خرج - {year}/{month:02d}"
    draw_pie_chart(data, title, account_name)


def show_yearly_chart(account_id, account_name, year):
    months, income, expense = get_yearly_data(account_id, year)
    title = f"دخل و خرج سالانه - {year}"
    draw_combined_chart(months, income, expense, title, account_name)


def show_category_chart(account_id, account_name, start_date, end_date):
    data = get_category_chart_data(account_id, start_date, end_date)
    data_dict = {row[0]: row[1] for row in data}
    title = f"دسته‌بندی هزینه‌ها"
    draw_donut_chart(data_dict, title, account_name)


if __name__ == "__main__":
    from database import create_tables
    create_tables()
    print("✅ ماژول نمودارها بارگذاری شد.")
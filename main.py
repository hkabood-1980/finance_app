# main.py
"""نقطه ورود نسخه موبایل برنامه مدیریت مالی"""

import flet as ft
import flet_charts as fch
from datetime import datetime

from core import database, services, reports
from sms import sms_parser, sms_service


# =====================================================
# رنگ‌های برنامه
# =====================================================

COLOR_PRIMARY = "#3B82F6"
COLOR_PRIMARY_DARK = "#2563EB"
COLOR_SUCCESS = "#06855A"
COLOR_DANGER = "#FC0707"
COLOR_INFO = "#4A0599"
COLOR_WARNING = "#F59E0B"
COLOR_INDIGO = "#D13E94"
COLOR_BG = "#F0F4F8"
COLOR_SUCCESS1 ="#DD18C3"
COLOR_SMS = "#0F1AB6"

def main(page: ft.Page):
    """تابع اصلی Flet"""
    database.create_tables()
    
    # =====================================================
    # تنظیمات صفحه
    # =====================================================
    page.title = "💰 مدیریت مالی"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = COLOR_BG
    page.window.width = 400
    page.window.height = 700

    # =====================================================
    # توابع کمکی
    # =====================================================

    def get_stats():
        """دریافت آمار برای نمایش در صفحه اصلی"""
        try:
            income, expense = services.show_financial_summary()
            accounts = database.load_accounts()
            total_balance = sum(acc[4] for acc in accounts)
            return {
                "income": income,
                "expense": expense,
                "balance": total_balance,
                "cards": len(accounts),
            }
        except Exception as e:
            print(f"خطا: {e}")
            return {"income": 0, "expense": 0, "balance": 0, "cards": 0}

    def show_snack(text, color=COLOR_SUCCESS):
        """نمایش پیام با روش جدید Flet"""
        snack = ft.SnackBar(
            content=ft.Text(text, color=ft.Colors.WHITE),
            bgcolor=color,
        )
        page.overlay.append(snack)
        snack.open = True
        page.update()

    def make_stat_card(icon, label, value, color):
        """کارت آمار با گرادیانت و سایه"""
        return ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text(icon, size=26),
                    width=50, height=50,
                    border_radius=25,
                    bgcolor=ft.Colors.with_opacity(0.25, ft.Colors.WHITE),
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Container(height=5),
                ft.Text(
                    value,
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                ),
                ft.Text(
                    label,
                    size=11,
                    color=ft.Colors.with_opacity(0.9, ft.Colors.WHITE),
                ),
            ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=3,
            ),
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=[color, ft.Colors.with_opacity(0.8, color)],
            ),
            border_radius=18,
            padding=15,
            alignment=ft.Alignment.CENTER,
            expand=True,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=10,
                color=ft.Colors.with_opacity(0.25, color),
                offset=ft.Offset(0, 4),
            ),
        )

    def make_menu_button(icon, label, color, on_click):
        """دکمه‌ی منو با سایه و انیمیشن"""

        def on_hover(e):
            e.control.scale = 1.03 if e.data == "true" else 1.0
            e.control.update()

        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Text(icon, size=24),
                    width=45, height=45,
                    border_radius=22,
                    bgcolor=ft.Colors.with_opacity(0.25, ft.Colors.WHITE),
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Text(
                    label,
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                ),
                ft.Icon(
                    ft.Icons.ARROW_BACK_IOS_NEW,
                    color=ft.Colors.with_opacity(0.5, ft.Colors.WHITE),
                    size=16,
                ),
            ], spacing=15),
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=[color, ft.Colors.with_opacity(0.85, color)],
            ),
            border_radius=15,
            padding=15,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=12,
                color=ft.Colors.with_opacity(0.35, color),
                offset=ft.Offset(0, 5),
            ),
            on_click=on_click,
            on_hover=on_hover,
            ink=True,
            animate_scale=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            scale=1.0,
        )

    def make_header(title, back_func, color=COLOR_PRIMARY):
        """هدر با گرادیانت و سایه"""
        return ft.Container(
            content=ft.Row([
                ft.IconButton(
                    icon=ft.Icons.ARROW_BACK,
                    icon_color=ft.Colors.WHITE,
                    icon_size=24,
                    on_click=lambda e: back_func(),
                ),
                ft.Text(
                    title,
                    size=18,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE,
                ),
            ]),
            padding=ft.Padding.symmetric(horizontal=10, vertical=12),
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_LEFT,
                end=ft.Alignment.BOTTOM_RIGHT,
                colors=[color, ft.Colors.with_opacity(0.85, color)],
            ),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=8,
                color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                offset=ft.Offset(0, 3),
            ),
        )

    # =====================================================
    # صفحه‌ی اصلی (خانه)
    # =====================================================
    def build_home_view():
        stats = get_stats()

        return ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        make_stat_card("💵", "درآمد", f"{stats['income']:,.0f}", COLOR_SUCCESS),
                        make_stat_card("💸", "هزینه", f"{stats['expense']:,.0f}", COLOR_DANGER),
                    ], spacing=10),
                    ft.Row([
                        make_stat_card("💰", "مانده", f"{stats['balance']:,.0f}", COLOR_INFO),
                        make_stat_card("🏦", "کارت‌ها", str(stats['cards']), COLOR_WARNING),
                    ], spacing=10),
                ], spacing=10),
                padding=15,
            ),

            ft.Container(
                content=ft.Column([
                    ft.Text("━━━ منوی اصلی ━━━", size=14,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER),
                    ft.Container(height=10),

                    make_menu_button("💳", "نمایش کارت‌ها", COLOR_PRIMARY,
                                     lambda e: go_to_cards()),
                    make_menu_button("➕", "ثبت کارت جدید", COLOR_SUCCESS1,
                                     lambda e: go_to_add_card()),
                    make_menu_button("💵", "ثبت درآمد", COLOR_SUCCESS,
                                     lambda e: go_to_transaction("درآمد")),
                    make_menu_button("💸", "ثبت هزینه", COLOR_DANGER,
                                     lambda e: go_to_transaction("هزینه")),
                    make_menu_button("📊", "گزارش‌ها", COLOR_INFO,
                                     lambda e: go_to_reports()),
                    make_menu_button("📩", "پیامک‌های بانکی", COLOR_WARNING,
                                     lambda e: go_to_sms()),
                   
                    make_menu_button("🔗", "اتصال‌های پیامک", COLOR_SMS,
                                     lambda e: go_to_mappings()),
                ], spacing=8),
                padding=15,
            ),
        ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # =====================================================
    # صفحه‌ی کارت‌ها
    # =====================================================
    def build_cards_view():
        accounts = database.load_accounts()

        if not accounts:
            cards_list = [
                ft.Container(
                    content=ft.Column([
                        ft.Text("🏦", size=60),
                        ft.Text("هنوز هیچ کارتی ثبت نشده", size=16,
                                color=ft.Colors.GREY_600),
                        ft.Container(height=20),
                        ft.Button(
                            "➕ ثبت کارت جدید",
                            on_click=lambda e: go_to_add_card(),
                            bgcolor=COLOR_SUCCESS,
                            color=ft.Colors.WHITE,
                        ),
                    ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=40,
                )
            ]
        else:
            cards_list = []
            for acc in accounts:
                acc_id, name, bank, card_num, balance, acc_type = acc

                def make_card_click(aid):
                    return lambda e: go_to_card_detail(aid)

                cards_list.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(f"💳 {name}", size=16,
                                        weight=ft.FontWeight.BOLD),
                                ft.Text(f"{balance:,.0f} تومان", size=14,
                                        color=COLOR_SUCCESS,
                                        weight=ft.FontWeight.BOLD),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Text(f"🏦 {bank} | 💳 {card_num}",
                                    size=12, color=ft.Colors.GREY_600),
                            ft.Container(height=5),
                            ft.Row([
                                ft.Text("برای ویرایش کلیک کنید →",
                                        size=10,
                                        color=ft.Colors.GREY_400),
                            ], alignment=ft.MainAxisAlignment.END),
                        ], spacing=5),
                        bgcolor=ft.Colors.WHITE,
                        border_radius=12,
                        padding=15,
                        margin=ft.Margin.only(bottom=10),
                        on_click=make_card_click(acc_id),
                        ink=True,
                        shadow=ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=8,
                            color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                            offset=ft.Offset(0, 3),
                        ),
                    )
                )

        return ft.Column([
            make_header("💳 کارت‌های بانکی", go_to_home),
            ft.Container(
                content=ft.Column(cards_list, spacing=5),
                padding=15,
                expand=True,
            ),
        ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # =====================================================
    # صفحه‌ی جزئیات کارت
    # =====================================================
    def build_card_detail_view(account_id):
        account = database.get_account_by_id(account_id)
        if not account:
            show_snack("❌ کارت پیدا نشد", COLOR_DANGER)
            go_to_cards()
            return ft.Container()

        acc_id, name, bank, card_num, balance, acc_type = account

        name_field = ft.TextField(
            label="نام حساب",
            value=name,
            border_radius=10,
            filled=True,
            bgcolor=ft.Colors.WHITE,
        )

        bank_field = ft.TextField(
            label="نام بانک",
            value=bank,
            border_radius=10,
            filled=True,
            bgcolor=ft.Colors.WHITE,
        )

        card_field = ft.TextField(
            label="شماره کارت",
            value=card_num,
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10,
            filled=True,
            bgcolor=ft.Colors.WHITE,
        )

        type_field = ft.TextField(
            label="نوع حساب",
            value=acc_type,
            border_radius=10,
            filled=True,
            bgcolor=ft.Colors.WHITE,
        )

        balance_display = ft.Container(
            content=ft.Column([
                ft.Text("💰 موجودی فعلی", size=12, color=ft.Colors.GREY_600),
                ft.Text(f"{balance:,.0f} تومان", size=22,
                        weight=ft.FontWeight.BOLD,
                        color=COLOR_SUCCESS),
            ], spacing=2),
            bgcolor=ft.Colors.with_opacity(0.1, COLOR_SUCCESS),
            border_radius=12,
            padding=20,
            alignment=ft.Alignment.CENTER,
        )

        def save_changes(e):
            new_name = name_field.value.strip() if name_field.value else ""
            new_bank = bank_field.value.strip() if bank_field.value else ""
            new_card = card_field.value.strip() if card_field.value else ""
            new_type = type_field.value.strip() if type_field.value else ""

            if not new_name:
                show_snack("❌ نام حساب را وارد کنید", COLOR_DANGER)
                return
            if not new_bank:
                show_snack("❌ نام بانک را وارد کنید", COLOR_DANGER)
                return
            if not new_card:
                show_snack("❌ شماره کارت را وارد کنید", COLOR_DANGER)
                return

            try:
                database.update_account(
                    acc_id, new_name, new_bank, new_card,
                    balance, new_type
                )
                show_snack("✅ کارت ویرایش شد", COLOR_SUCCESS)
                go_to_cards()
            except Exception as ex:
                show_snack(f"❌ خطا: {ex}", COLOR_DANGER)

        def confirm_delete(e):
            def on_confirm(ev):
                dialog.open = False
                page.update()

                result = database.delete_account(acc_id)
                if result:
                    show_snack("✅ کارت حذف شد", COLOR_SUCCESS)
                    go_to_cards()
                else:
                    show_snack("❌ امکان حذف نیست (تراکنش دارد)", COLOR_DANGER)

            def on_cancel(ev):
                dialog.open = False
                page.update()

            dialog = ft.AlertDialog(
                title=ft.Text("⚠️ تأیید حذف"),
                content=ft.Text(
                    f"آیا مطمئن هستید که می‌خواهید کارت «{name}» حذف شود؟\n\n"
                    "⚠️ اگر تراکنش داشته باشد، حذف نمی‌شود."
                ),
                actions=[
                    ft.TextButton("انصراف", on_click=on_cancel),
                    ft.TextButton(
                        "حذف",
                        on_click=on_confirm,
                        style=ft.ButtonStyle(color=COLOR_DANGER),
                    ),
                ],
            )
            page.overlay.append(dialog)
            dialog.open = True
            page.update()

        return ft.Column([
            make_header(f"💳 {name}", go_to_cards, COLOR_PRIMARY),
            ft.Container(
                content=ft.Column([
                    balance_display,
                    ft.Container(height=20),

                    ft.Text("✏️ ویرایش اطلاعات", size=14,
                            weight=ft.FontWeight.BOLD),
                    ft.Divider(),
                    name_field,
                    ft.Container(height=10),
                    bank_field,
                    ft.Container(height=10),
                    card_field,
                    ft.Container(height=10),
                    type_field,
                    ft.Container(height=20),

                    ft.Button(
                        "✅ ذخیره تغییرات",
                        on_click=save_changes,
                        bgcolor=COLOR_SUCCESS,
                        color=ft.Colors.WHITE,
                        height=50,
                        width=350,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=12),
                        ),
                    ),

                    ft.Container(height=15),

                    ft.Button(
                        "🗑️ حذف کارت",
                        on_click=confirm_delete,
                        bgcolor=COLOR_DANGER,
                        color=ft.Colors.WHITE,
                        height=50,
                        width=350,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=12),
                        ),
                    ),
                ], spacing=5),
                padding=20,
                expand=True,
            ),
        ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # =====================================================
    # صفحه‌ی ثبت کارت جدید
    # =====================================================
    def build_add_card_view():
        name_field = ft.TextField(
            label="نام حساب", hint_text="حساب اصلی",
            border_radius=10, filled=True, bgcolor=ft.Colors.WHITE,
        )
        bank_field = ft.TextField(
            label="نام بانک", hint_text="ملت",
            border_radius=10, filled=True, bgcolor=ft.Colors.WHITE,
        )
        card_field = ft.TextField(
            label="شماره کارت", hint_text="1234567890",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10, filled=True, bgcolor=ft.Colors.WHITE,
        )
        balance_field = ft.TextField(
            label="موجودی اولیه", hint_text="0",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=10, filled=True, bgcolor=ft.Colors.WHITE,
        )
        type_field = ft.TextField(
            label="نوع حساب", hint_text="جاری",
            border_radius=10, filled=True, bgcolor=ft.Colors.WHITE,
        )

        def save_card(e):
            name = name_field.value.strip() if name_field.value else ""
            bank = bank_field.value.strip() if bank_field.value else ""
            card_num = card_field.value.strip() if card_field.value else ""
            balance_str = balance_field.value.strip() if balance_field.value else "0"
            acc_type = type_field.value.strip() if type_field.value else ""

            if not name:
                show_snack("❌ نام حساب را وارد کنید", COLOR_DANGER)
                return
            if not bank:
                show_snack("❌ نام بانک را وارد کنید", COLOR_DANGER)
                return
            if not card_num:
                show_snack("❌ شماره کارت را وارد کنید", COLOR_DANGER)
                return

            try:
                balance = float(balance_str) if balance_str else 0
                if balance < 0:
                    raise ValueError
            except ValueError:
                show_snack("❌ موجودی باید عددی مثبت باشد", COLOR_DANGER)
                return

            try:
                database.add_account(name, bank, card_num, balance, acc_type)
                show_snack(f"✅ کارت «{name}» ثبت شد", COLOR_SUCCESS)
                go_to_cards()
            except Exception as ex:
                show_snack(f"❌ خطا: {ex}", COLOR_DANGER)

        return ft.Column([
            make_header("➕ ثبت کارت جدید", go_to_cards),
            ft.Container(
                content=ft.Column([
                    name_field, ft.Container(height=10),
                    bank_field, ft.Container(height=10),
                    card_field, ft.Container(height=10),
                    balance_field, ft.Container(height=10),
                    type_field, ft.Container(height=20),
                    ft.Button(
                        "✅ ذخیره کارت",
                        on_click=save_card,
                        bgcolor=COLOR_SUCCESS,
                        color=ft.Colors.WHITE,
                        height=50, width=350,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=12),
                            elevation=5,
                        ),
                    ),
                ], spacing=5),
                padding=20,
                expand=True,
            ),
        ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # =====================================================
    # صفحه‌ی ثبت درآمد/هزینه
    # =====================================================
    def build_transaction_view(trans_type):
        accounts = database.load_accounts()

        if not accounts:
            return ft.Column([
                make_header(f"ثبت {trans_type}", go_to_home,
                            COLOR_SUCCESS if trans_type == "درآمد" else COLOR_DANGER),
                ft.Container(
                    content=ft.Column([
                        ft.Text("⚠️ ابتدا یک کارت ثبت کنید",
                                size=16, color=COLOR_DANGER),
                        ft.Container(height=20),
                        ft.Button(
                            "➕ ثبت کارت",
                            on_click=lambda e: go_to_add_card(),
                            bgcolor=COLOR_SUCCESS,
                            color=ft.Colors.WHITE,
                        ),
                    ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    padding=40,
                ),
            ], expand=True)

        card_names = [acc[1] for acc in accounts]
        card_dropdown = ft.Dropdown(
            label="انتخاب کارت",
            options=[ft.DropdownOption(name) for name in card_names],
            value=card_names[0],
            border_radius=10, filled=True, bgcolor=ft.Colors.WHITE,
        )
        amount_field = ft.TextField(label="مبلغ", hint_text="0",
                                    keyboard_type=ft.KeyboardType.NUMBER,
                                    border_radius=10, filled=True, bgcolor=ft.Colors.WHITE)
        category_field = ft.TextField(label="دسته‌بندی", hint_text="حقوق / غذا",
                                      border_radius=10, filled=True, bgcolor=ft.Colors.WHITE)
        place_field = ft.TextField(label="محل (اختیاری)", hint_text="شرکت",
                                   border_radius=10, filled=True, bgcolor=ft.Colors.WHITE)
        description_field = ft.TextField(label="توضیحات (اختیاری)", hint_text="...",
                                         border_radius=10, filled=True, bgcolor=ft.Colors.WHITE)

        color = COLOR_SUCCESS if trans_type == "درآمد" else COLOR_DANGER

        def save_transaction(e):
            card_name = card_dropdown.value
            amount_str = amount_field.value.strip() if amount_field.value else ""
            category = category_field.value.strip() if category_field.value else ""
            place = place_field.value.strip() if place_field.value else ""
            description = description_field.value.strip() if description_field.value else ""

            if not card_name:
                show_snack("❌ یک کارت انتخاب کنید", COLOR_DANGER)
                return

            selected_card = None
            for acc in accounts:
                if acc[1] == card_name:
                    selected_card = acc
                    break

            if selected_card is None:
                show_snack("❌ کارت پیدا نشد", COLOR_DANGER)
                return

            try:
                amount = float(amount_str)
                if amount <= 0:
                    raise ValueError
            except ValueError:
                show_snack("❌ مبلغ باید عددی مثبت باشد", COLOR_DANGER)
                return

            date = datetime.now().strftime("%Y-%m-%d %H:%M")

            try:
                services.register_transaction(
                    account_id=selected_card[0], date=date,
                    trans_type=trans_type, category=category,
                    amount=amount, place=place, description=description,
                )
                show_snack(f"✅ {trans_type} {amount:,.0f} ثبت شد", COLOR_SUCCESS)
                go_to_home()
            except ValueError as ex:
                show_snack(f"❌ {ex}", COLOR_DANGER)
            except Exception as ex:
                show_snack(f"❌ خطا: {ex}", COLOR_DANGER)

        return ft.Column([
            make_header(f"➕ ثبت {trans_type}", go_to_home, color),
            ft.Container(
                content=ft.Column([
                    card_dropdown, ft.Container(height=10),
                    amount_field, ft.Container(height=10),
                    category_field, ft.Container(height=10),
                    place_field, ft.Container(height=10),
                    description_field, ft.Container(height=20),
                    ft.Button(
                        f"✅ ثبت {trans_type}",
                        on_click=save_transaction,
                        bgcolor=color,
                        color=ft.Colors.WHITE,
                        height=55,
                        width=350,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=12),
                            elevation=5,
                        ),
                    ),
                ], spacing=5),
                padding=20,
                expand=True,
            ),
        ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # =====================================================
    # صفحه‌ی گزارش‌ها (با نمودار بهینه)
    # =====================================================
    def build_reports_view():
        try:
            income, expense = services.show_financial_summary()
            balance = income - expense

            conn = database.get_connection()
            cursor = conn.cursor()

            cursor.execute("""
                SELECT category, SUM(amount) as total
                FROM transactions
                WHERE type = 'هزینه'
                GROUP BY category
                ORDER BY total DESC
                LIMIT 5
            """)
            categories = cursor.fetchall()

            cursor.execute("""
                SELECT transactions.id, accounts.name, accounts.bank,
                       transactions.type, transactions.category,
                       transactions.amount, transactions.place,
                       transactions.description, transactions.date
                FROM transactions
                JOIN accounts ON transactions.account_id = accounts.id
                ORDER BY transactions.date DESC
                LIMIT 5
            """)
            recent_transactions = cursor.fetchall()
            conn.close()
        except Exception as e:
            print(f"خطا: {e}")
            income = expense = balance = 0
            recent_transactions = []
            categories = []

        # خلاصه مالی
        summary_card = ft.Container(
            content=ft.Column([
                ft.Text("💰 خلاصه مالی", size=15, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Row([
                    ft.Text("درآمد کل:", size=13),
                    ft.Text(f"{income:,.0f} تومان", size=13,
                            color=COLOR_SUCCESS, weight=ft.FontWeight.BOLD),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Row([
                    ft.Text("هزینه کل:", size=13),
                    ft.Text(f"{expense:,.0f} تومان", size=13,
                            color=COLOR_DANGER, weight=ft.FontWeight.BOLD),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Divider(),
                ft.Row([
                    ft.Text("مانده:", size=14, weight=ft.FontWeight.BOLD),
                    ft.Text(f"{balance:,.0f} تومان", size=14,
                            color=COLOR_INFO, weight=ft.FontWeight.BOLD),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ], spacing=8),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            padding=15,
        )

        # نمودار میله‌ای
        max_value = max(income, expense, abs(balance), 1)

        bar_chart = fch.BarChart(
            groups=[
                fch.BarChartGroup(
                    x=0,
                    rods=[
                        fch.BarChartRod(
                            from_y=0, to_y=income, width=30,
                            color=COLOR_SUCCESS, border_radius=5,
                            tooltip=f"درآمد: {income:,.0f}",
                        ),
                    ],
                ),
                fch.BarChartGroup(
                    x=1,
                    rods=[
                        fch.BarChartRod(
                            from_y=0, to_y=expense, width=30,
                            color=COLOR_DANGER, border_radius=5,
                            tooltip=f"هزینه: {expense:,.0f}",
                        ),
                    ],
                ),
                fch.BarChartGroup(
                    x=2,
                    rods=[
                        fch.BarChartRod(
                            from_y=0, to_y=max(balance, 0), width=30,
                            color=COLOR_INFO, border_radius=5,
                            tooltip=f"مانده: {balance:,.0f}",
                        ),
                    ],
                ),
            ],
            border=ft.Border.all(1, ft.Colors.GREY_300),
            left_axis=fch.ChartAxis(label_size=40),
            bottom_axis=fch.ChartAxis(
                labels=[
                    fch.ChartAxisLabel(value=0, label=ft.Text("درآمد", size=10)),
                    fch.ChartAxisLabel(value=1, label=ft.Text("هزینه", size=10)),
                    fch.ChartAxisLabel(value=2, label=ft.Text("مانده", size=10)),
                ],
                label_size=30,
            ),
            max_y=max_value,
            horizontal_grid_lines=fch.ChartGridLines(
                color=ft.Colors.GREY_300, width=1,
                dash_pattern=[5, 5],
            ),
        )

        bar_card = ft.Container(
            content=ft.Column([
                ft.Text("📊 مقایسه درآمد و هزینه", size=15,
                        weight=ft.FontWeight.BOLD),
                ft.Divider(),
                ft.Container(content=bar_chart, height=200),
            ]),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            padding=15,
        )

        # نمودار دایره‌ای
        pie_colors = ["#EF4444", "#F59E0B", "#10B981", "#3B82F6", "#8B5CF6"]

        if categories:
            total_cat = sum(cat[1] for cat in categories)

            sections = []
            for i, cat in enumerate(categories):
                cat_name, value = cat[0], cat[1]
                percentage = (value / total_cat * 100) if total_cat > 0 else 0
                sections.append(
                    fch.PieChartSection(
                        value=value,
                        title=f"{percentage:.0f}%",
                        color=pie_colors[i % len(pie_colors)],
                        radius=50,
                        title_style=ft.TextStyle(
                            size=10, color=ft.Colors.WHITE,
                            weight=ft.FontWeight.BOLD,
                        ),
                    )
                )

            legend_items = []
            for i, cat in enumerate(categories):
                cat_name, value = cat[0], cat[1]
                legend_items.append(
                    ft.Row([
                        ft.Container(
                            width=12, height=12,
                            bgcolor=pie_colors[i % len(pie_colors)],
                            border_radius=3,
                        ),
                        ft.Text(f"{cat_name}: {value:,.0f}", size=11),
                    ], spacing=8)
                )

            pie_content = ft.Column([
                ft.Container(
                    content=fch.PieChart(
                        sections=sections,
                        sections_space=2,
                        center_space_radius=30,
                    ),
                    height=180,
                    alignment=ft.Alignment.CENTER,
                ),
                ft.Container(
                    content=ft.Column(legend_items, spacing=5),
                    padding=ft.Padding.only(top=10),
                ),
            ])
        else:
            pie_content = ft.Column([
                ft.Text("هنوز هزینه‌ای ثبت نشده", size=12,
                        color=ft.Colors.GREY_600),
            ])

        pie_card = ft.Container(
            content=ft.Column([
                ft.Text("🥧 دسته‌بندی هزینه‌ها", size=15,
                        weight=ft.FontWeight.BOLD),
                ft.Divider(),
                pie_content,
            ]),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            padding=15,
        )

        # تراکنش‌های اخیر
        if recent_transactions:
            tx_items = []
            for tx in recent_transactions:
                tx_type = tx[3]
                cat = tx[4]
                amount = tx[5]
                date = tx[8]

                icon = "💵" if tx_type == "درآمد" else "💸" if tx_type == "هزینه" else "🔁"
                color = (COLOR_SUCCESS if tx_type == "درآمد"
                         else COLOR_DANGER if tx_type == "هزینه"
                         else COLOR_WARNING)

                tx_items.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Text(icon, size=20),
                            ft.Column([
                                ft.Text(f"{tx_type} - {cat}", size=12,
                                        weight=ft.FontWeight.BOLD),
                                ft.Text(f"{date}", size=10,
                                        color=ft.Colors.GREY_600),
                            ], spacing=2, expand=True),
                            ft.Text(f"{amount:,.0f}", size=12,
                                    color=color, weight=ft.FontWeight.BOLD),
                        ], spacing=10),
                        bgcolor=ft.Colors.WHITE,
                        border_radius=10,
                        padding=10,
                        margin=ft.Margin.only(bottom=5),
                    )
                )
            tx_content = tx_items
        else:
            tx_content = [
                ft.Text("هنوز تراکنشی ثبت نشده", size=12,
                        color=ft.Colors.GREY_600)
            ]

        recent_card = ft.Container(
            content=ft.Column([
                ft.Text("📋 تراکنش‌های اخیر", size=15,
                        weight=ft.FontWeight.BOLD),
                ft.Divider(),
                *tx_content,
            ], spacing=5),
            bgcolor=ft.Colors.WHITE,
            border_radius=12,
            padding=15,
        )

        return ft.Column([
            make_header("📊 گزارش‌ها", go_to_home, COLOR_INFO),
            ft.Container(
                content=ft.Column([
                    summary_card,
                    ft.Container(height=15),
                    bar_card,
                    ft.Container(height=15),
                    pie_card,
                    ft.Container(height=15),
                    recent_card,
                ], spacing=5),
                padding=15,
                expand=True,
            ),
        ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # =====================================================
    # صفحه‌ی پیامک‌های بانکی
    # =====================================================
    def build_sms_view():
        pending = sms_service.get_pending_sms()

        accounts = database.load_accounts()
        card_options = [ft.DropdownOption(
            key=str(acc[0]), text=f"{acc[1]} ({acc[4]:,.0f} تومان)"
        ) for acc in accounts]

        sms_items = []

        if not pending:
            sms_items.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("📭", size=60),
                        ft.Text("پیامک جدیدی در انتظار نیست", size=16,
                                color=ft.Colors.GREY_600),
                        ft.Text("پیامک‌های بانکی به‌صورت خودکار اینجا نمایش داده می‌شوند",
                                size=12, color=ft.Colors.GREY_500,
                                text_align=ft.TextAlign.CENTER),
                    ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    padding=40,
                    alignment=ft.Alignment.CENTER,
                )
            )
        else:
            for sms in pending:
                sms_id, sender, body, received, amount, ttype, card = sms

                color = COLOR_SUCCESS if ttype == "درآمد" else COLOR_DANGER
                icon = "💵" if ttype == "درآمد" else "💸"

                card_var = ft.Dropdown(
                    label="اتصال به کارت",
                    options=card_options,
                    border_radius=10,
                    filled=True,
                    bgcolor=ft.Colors.WHITE,
                    text_size=12,
                    height=50,
                )

                def make_approve_handler(sid, cv):
                    def handler(e):
                        account_id = cv.value
                        if not account_id:
                            show_snack("❌ ابتدا یک کارت انتخاب کنید", COLOR_DANGER)
                            return
                        try:
                            sms_service.approve_sms(sid, int(account_id))
                            show_snack("✅ پیامک ثبت شد", COLOR_SUCCESS)
                            go_to_sms()
                        except Exception as ex:
                            show_snack(f"❌ {ex}", COLOR_DANGER)
                    return handler

                def make_reject_handler(sid):
                    def handler(e):
                        try:
                            sms_service.reject_sms(sid)
                            show_snack("🗑️ پیامک رد شد", COLOR_WARNING)
                            go_to_sms()
                        except Exception as ex:
                            show_snack(f"❌ {ex}", COLOR_DANGER)
                    return handler

                sms_card = ft.Container(
                    content=ft.Column([
                        ft.Row([
                            ft.Container(
                                content=ft.Text(icon, size=20),
                                width=40, height=40,
                                border_radius=20,
                                bgcolor=ft.Colors.with_opacity(0.15, color),
                                alignment=ft.Alignment.CENTER,
                            ),
                            ft.Column([
                                ft.Text(f"{ttype} - {amount:,.0f} تومان",
                                        size=14, weight=ft.FontWeight.BOLD,
                                        color=color),
                                ft.Text(f"از: {sender}  |  {received}",
                                        size=10, color=ft.Colors.GREY_600),
                            ], spacing=2, expand=True),
                        ], spacing=10),

                        ft.Container(
                            content=ft.Text(
                                body[:150] + ("..." if len(body) > 150 else ""),
                                size=11, color=ft.Colors.GREY_700,
                            ),
                            bgcolor=ft.Colors.GREY_100,
                            border_radius=8,
                            padding=10,
                        ),

                        ft.Container(height=10),
                        card_var,
                        ft.Container(height=10),
                        ft.Row([
                            ft.Button(
                                "✅ تأیید و ثبت",
                                on_click=make_approve_handler(sms_id, card_var),
                                bgcolor=COLOR_SUCCESS,
                                color=ft.Colors.WHITE,
                                height=40,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=10),
                                ),
                                expand=True,
                            ),
                            ft.Container(width=8),
                            ft.IconButton(
                                icon=ft.Icons.DELETE_OUTLINE,
                                icon_color=COLOR_DANGER,
                                tooltip="رد پیامک",
                                on_click=make_reject_handler(sms_id),
                            ),
                        ], spacing=5),
                    ], spacing=5),
                    bgcolor=ft.Colors.WHITE,
                    border_radius=15,
                    padding=15,
                    margin=ft.Margin.only(bottom=10),
                    shadow=ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=8,
                        color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                        offset=ft.Offset(0, 3),
                    ),
                )

                sms_items.append(sms_card)

        count = len(pending)

        return ft.Column([
            make_header(f"📩 پیامک‌های بانکی ({count})", go_to_home, COLOR_WARNING),
            ft.Container(
                content=ft.Column(sms_items, spacing=5),
                padding=15,
                expand=True,
            ),
        ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # =====================================================
    # صفحه‌ی اتصال‌های پیامک
    # =====================================================
    def build_mappings_view():
        mappings = sms_service.get_all_mappings()
        count = len(mappings) if mappings else 0

        items = []

        if not mappings:
            items.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("🔗", size=60),
                        ft.Text("هنوز اتصالی ذخیره نشده", size=16,
                                color=ft.Colors.GREY_600),
                        ft.Container(height=10),
                        ft.Text(
                            "وقتی پیامکی را تأیید کنید، اتصال شماره حساب به کارت ذخیره می‌شود و دفعه‌ی بعد خودکار ثبت می‌شود.",
                            size=11, color=ft.Colors.GREY_500,
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=20),
                        ft.Button(
                            "📩 رفتن به پیامک‌ها",
                            on_click=lambda e: go_to_sms(),
                            bgcolor=COLOR_WARNING,
                            color=ft.Colors.WHITE,
                            height=45,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=10),
                            ),
                        ),
                    ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5,
                    ),
                    padding=40,
                    alignment=ft.Alignment.CENTER,
                )
            )
        else:
            for m in mappings:
                m_id, acc_num, card_last4, acc_id, acc_name, bank, auto = m

                acc_num_short = acc_num
                if len(acc_num) > 15:
                    acc_num_short = f"{acc_num[:6]}...{acc_num[-4:]}"

                def make_switch_handler(mid, sw):
                    def handler(e):
                        val = 1 if sw.value else 0
                        sms_service.update_mapping_auto_approve(mid, val)
                        show_snack(
                            "✅ ثبت خودکار فعال" if val else "⏸️ ثبت خودکار غیرفعال",
                            COLOR_SUCCESS if val else COLOR_WARNING,
                        )
                    return handler

                def make_delete_handler(mid, name):
                    def handler(e):
                        def on_confirm(ev):
                            dialog.open = False
                            page.update()
                            sms_service.delete_mapping(mid)
                            show_snack("🗑️ اتصال حذف شد", COLOR_WARNING)
                            go_to_mappings()

                        def on_cancel(ev):
                            dialog.open = False
                            page.update()

                        dialog = ft.AlertDialog(
                            title=ft.Text("⚠️ تأیید حذف"),
                            content=ft.Text(
                                f"اتصال «{name}» حذف شود؟\n\n"
                                "بعد از حذف، پیامک‌های این شماره حساب دوباره نیاز به تأیید دستی دارند."
                            ),
                            actions=[
                                ft.TextButton("انصراف", on_click=on_cancel),
                                ft.TextButton(
                                    "حذف",
                                    on_click=on_confirm,
                                    style=ft.ButtonStyle(color=COLOR_DANGER),
                                ),
                            ],
                        )
                        page.overlay.append(dialog)
                        dialog.open = True
                        page.update()
                    return handler

                auto_switch = ft.Switch(
                    value=bool(auto),
                    active_color=COLOR_SUCCESS,
                )
                auto_switch.on_change = make_switch_handler(m_id, auto_switch)

                items.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Container(
                                    content=ft.Text("🏦", size=18),
                                    width=40, height=40,
                                    border_radius=20,
                                    bgcolor=ft.Colors.with_opacity(0.15, COLOR_INFO),
                                    alignment=ft.Alignment.CENTER,
                                ),
                                ft.Column([
                                    ft.Text(f"{bank or 'نامشخص'}", size=14,
                                            weight=ft.FontWeight.BOLD),
                                    ft.Text(f"→ {acc_name}", size=12,
                                            color=COLOR_SUCCESS,
                                            weight=ft.FontWeight.BOLD),
                                ], spacing=2, expand=True),
                            ], spacing=10),

                            ft.Container(
                                content=ft.Column([
                                    ft.Row([
                                        ft.Text("🔢 شماره حساب:",
                                                size=11, color=ft.Colors.GREY_600),
                                        ft.Text(acc_num_short, size=11,
                                                weight=ft.FontWeight.BOLD),
                                    ], spacing=5),
                                    ft.Row([
                                        ft.Text("💳 ۴ رقم آخر:",
                                                size=11, color=ft.Colors.GREY_600),
                                        ft.Text(f"*{card_last4 or '?'}",
                                                size=11,
                                                weight=ft.FontWeight.BOLD),
                                    ], spacing=5),
                                ], spacing=3),
                                bgcolor=ft.Colors.GREY_100,
                                border_radius=8,
                                padding=10,
                            ),

                            ft.Row([
                                ft.Row([
                                    auto_switch,
                                    ft.Text(
                                        "🔄 ثبت خودکار" if auto else "⏸️ غیرفعال",
                                        size=12,
                                        color=COLOR_SUCCESS if auto else ft.Colors.GREY_600,
                                    ),
                                ], spacing=8),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE_OUTLINE,
                                    icon_color=COLOR_DANGER,
                                    tooltip="حذف اتصال",
                                    on_click=make_delete_handler(m_id, acc_name),
                                ),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ], spacing=8),
                        bgcolor=ft.Colors.WHITE,
                        border_radius=15,
                        padding=15,
                        margin=ft.Margin.only(bottom=10),
                        shadow=ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=8,
                            color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                            offset=ft.Offset(0, 3),
                        ),
                    )
                )

        return ft.Column([
            make_header(f"🔗 اتصال‌ها ({count})", go_to_home, COLOR_INFO),
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Text("💡", size=18),
                            ft.Text(
                                "این اتصال‌ها باعث می‌شوند پیامک‌های بعدی این شماره حساب خودکار ثبت شوند.",
                                size=11, color=ft.Colors.GREY_700,
                                expand=True,
                            ),
                        ], spacing=10),
                        bgcolor=ft.Colors.with_opacity(0.1, COLOR_INFO),
                        border_radius=10,
                        padding=12,
                        margin=ft.Margin.only(bottom=15),
                    ),
                    *items,
                ], spacing=5),
                padding=15,
                expand=True,
            ),
        ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # =====================================================
    # صفحه‌ی شبیه‌ساز پیامک
    # =====================================================
    def build_simulator_view():
        sender_field = ft.TextField(
            label="شماره فرستنده",
            hint_text="مثلاً: 98300017",
            value="98300017",
            border_radius=10,
            filled=True,
            bgcolor=ft.Colors.WHITE,
        )

        body_field = ft.TextField(
            label="متن پیامک",
            hint_text="متن پیامک بانکی را وارد کنید...",
            multiline=True,
            min_lines=6,
            max_lines=10,
            border_radius=10,
            filled=True,
            bgcolor=ft.Colors.WHITE,
            value="""بانک سپه
واریز:150,000,000ریال
حساب:111560500251813
مانده:152,706,899
7/1-22:11""",
        )

        result_container = ft.Container(
            content=ft.Text("منتظر ارسال...", size=12, color=ft.Colors.GREY_600),
            bgcolor=ft.Colors.GREY_100,
            border_radius=10,
            padding=15,
            margin=ft.Margin.only(top=10),
        )

        def send_sms(e):
            sender = sender_field.value.strip() if sender_field.value else ""
            body = body_field.value.strip() if body_field.value else ""

            if not sender:
                show_snack("❌ شماره فرستنده را وارد کنید", COLOR_DANGER)
                return
            if not body:
                show_snack("❌ متن پیامک را وارد کنید", COLOR_DANGER)
                return

            result = sms_service.add_sms_to_queue(sender, body)

            if isinstance(result, tuple) and result[0] == "auto":
                account_id = result[1]
                account = database.get_account_by_id(account_id)
                account_name = account[1] if account else "?"

                result_container.content = ft.Text(
                    f"""✅ ثبت خودکار!
📩 پیامک به کارت «{account_name}» ثبت شد
(چون قبلاً این شماره حساب به این کارت وصل شده بود)""",
                    size=12, color=COLOR_SUCCESS,
                )
                show_snack(f"✅ خودکار به «{account_name}» ثبت شد", COLOR_SUCCESS)

            elif result:
                parsed = sms_parser.parse_sms(body, sender)
                result_container.content = ft.Text(
                    f"""📩 پیامک در صف انتظار
🆔 شناسه: #{result}
💰 مبلغ: {parsed.get('amount', 0):,.0f} تومان
🏷️ نوع: {parsed.get('type', '?')}
🏛️ بانک: {sms_parser.detect_bank(sender, body)}

💡 راهنما: برای ثبت خودکار، پیامک را در صفحه‌ی پیامک‌ها تأیید کنید.""",
                    size=12, color=COLOR_INFO,
                )
                show_snack("📩 پیامک در صف", COLOR_INFO)

            else:
                result_container.content = ft.Text(
                    "❌ پیامک بانکی نیست یا تکراری است",
                    size=12, color=COLOR_DANGER,
                )
                show_snack("❌ پیامک رد شد", COLOR_DANGER)

            result_container.update()

        def load_sample(index):
            samples = [
                ("98300017", """بانک سپه
واریز:150,000,000ریال
حساب:111560500251813
مانده:152,706,899
7/1-22:11"""),
                ("98300017", """بانک سپه
برداشت:12,814,500
حساب :111560500251813
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
                ("1000", """خريد
ايرانسل
مبلغ: 263,732 ريال
رمز پويا:358591
اعتبار تا:17:40:16"""),
            ]
            sender_field.value = samples[index][0]
            body_field.value = samples[index][1]
            sender_field.update()
            body_field.update()
            show_snack(f"📋 نمونه {index + 1} بارگذاری شد")

        sample_buttons = ft.Row([
            ft.Button("سپه واریز", on_click=lambda e: load_sample(0),
                              bgcolor=COLOR_SUCCESS, color=ft.Colors.WHITE, height=35),
            ft.Button("سپه برداشت", on_click=lambda e: load_sample(1),
                              bgcolor=COLOR_DANGER, color=ft.Colors.WHITE, height=35),
            ft.Button("پاسارگاد", on_click=lambda e: load_sample(2),
                              bgcolor=COLOR_INFO, color=ft.Colors.WHITE, height=35),
            ft.Button("صادرات", on_click=lambda e: load_sample(3),
                              bgcolor=COLOR_WARNING, color=ft.Colors.WHITE, height=35),
            ft.Button("ایرانسل", on_click=lambda e: load_sample(4),
                              bgcolor=ft.Colors.GREY_500, color=ft.Colors.WHITE, height=35),
        ], spacing=5, wrap=True)

        return ft.Column([
            make_header("🧪 شبیه‌ساز پیامک بانکی", go_to_home, COLOR_INDIGO),
            ft.Container(
                content=ft.Column([
                    ft.Text("📋 نمونه‌های آماده:", size=13,
                            weight=ft.FontWeight.BOLD),
                    sample_buttons,
                    ft.Divider(),
                    sender_field,
                    ft.Container(height=10),
                    body_field,
                    ft.Container(height=15),
                    ft.Button(
                        "📩 ارسال پیامک",
                        on_click=send_sms,
                        bgcolor=COLOR_INDIGO,
                        color=ft.Colors.WHITE,
                        height=50,
                        width=350,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=12),
                            elevation=5,
                        ),
                    ),
                    ft.Container(height=10),
                    result_container,
                ], spacing=5),
                padding=20,
                expand=True,
            ),
        ],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )

    # =====================================================
    # Navigation
    # =====================================================
    def go_to_home():
        page.clean()
        page.appbar = app_bar
        page.add(build_home_view())
        page.update()

    def go_to_cards():
        page.clean()
        page.appbar = None
        page.add(build_cards_view())
        page.update()

    def go_to_add_card():
        page.clean()
        page.appbar = None
        page.add(build_add_card_view())
        page.update()

    def go_to_transaction(trans_type):
        page.clean()
        page.appbar = None
        page.add(build_transaction_view(trans_type))
        page.update()

    def go_to_reports():
        page.clean()
        page.appbar = None
        page.add(build_reports_view())
        page.update()

    def go_to_sms():
        page.clean()
        page.appbar = None
        page.add(build_sms_view())
        page.update()

    def go_to_mappings():
        page.clean()
        page.appbar = None
        page.add(build_mappings_view())
        page.update()

    def go_to_card_detail(account_id):
        page.clean()
        page.appbar = None
        page.add(build_card_detail_view(account_id))
        page.update()

    # =====================================================
    # AppBar
    # =====================================================
    app_bar = ft.AppBar(
        title=ft.Text(
            "💰 مدیریت مالی",
            weight=ft.FontWeight.BOLD,
            size=20,
        ),
        bgcolor=COLOR_PRIMARY,
        color=ft.Colors.WHITE,
        center_title=True,
    )

    # =====================================================
    # شروع
    # =====================================================
    page.appbar = app_bar
    page.add(build_home_view())


if __name__ == "__main__":
    ft.run(main)
import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import sys
import atexit
import signal
import shutil
import threading
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path

try:
    from plyer import notification
    HAS_PLYER = True
except ImportError:
    HAS_PLYER = False


# ─── Папка для данных ────────────────────────────────────────
def get_app_dir():
    app_name = "ApplePlanner"
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        path = Path(base) / app_name
    elif sys.platform == "darwin":
        path = Path.home() / "Library" / "Application Support" / app_name
    else:
        base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
        path = Path(base) / app_name

    try:
        path.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[!] Не удалось создать {path}: {e}")
        if getattr(sys, "frozen", False):
            fallback = Path(sys.executable).parent / app_name
        else:
            fallback = Path(os.path.abspath(__file__)).parent / app_name
        fallback.mkdir(parents=True, exist_ok=True)
        return fallback
    return path


APP_DIR = get_app_dir()
DATA_FILE = str(APP_DIR / "tasks.json")
SETTINGS_FILE = str(APP_DIR / "settings.json")
BACKUP_FILE = str(APP_DIR / "tasks.backup.json")


# ─── Языки ────────────────────────────────────────────────────
TRANSLATIONS = {
    "ru": {
        "app_title": "Apple Planner",
        "tab_week": "Расписание недели",
        "tab_tasks": "Все задачи",
        "tab_settings": "Кастомизация",
        "today": "Сегодня",
        "new_goal": "Новая цель",
        "all_tasks": "Все задачи",
        "mark_done": "Отметить выполненной",
        "skip": "Пропустить",
        "delete": "Удалить",
        "done_col": "СТАТУС",
        "type_col": "ТИП",
        "name_col": "НАЗВАНИЕ",
        "when_col": "КОГДА",
        "status_done": "✓ Выполнено",
        "status_pending": "◌ Ожидает",
        "status_skipped": "⊘ Пропущено",
        "type_once": "Разово",
        "type_weekly": "Еженедельно",
        "sec_theme": "Оформление",
        "sec_theme_sub": "Выберите палитру приложения",
        "sec_font": "Типографика",
        "sec_font_sub": "Гарнитура и размер шрифта",
        "sec_lang": "Язык",
        "sec_lang_sub": "Язык интерфейса",
        "sec_misc": "Дополнительно",
        "sec_misc_sub": "Поведение интерфейса",
        "sec_data": "Данные",
        "sec_data_sub": "Где хранятся ваши задачи",
        "font_family": "Гарнитура",
        "font_size": "Размер",
        "font_preview": "Пример текста задачи",
        "font_preview_sub": "Так будет выглядеть текст в задачах",
        "show_weekend": "Показывать субботу и воскресенье в расписании",
        "autosave_on": "Автоматическое сохранение включено",
        "autosave_desc": "Все цели хранятся в системной папке и сохраняются при каждом действии",
        "open_folder": "Открыть папку с данными",
        "reset_settings": "Сбросить настройки",
        "reset_confirm": "Сбросить настройки оформления?",
        "new_dialog_title": "Новая цель",
        "new_dialog_sub": "Укажите, что и когда вы хотите делать",
        "field_what": "Что делаем?",
        "field_repeat": "Повтор",
        "field_every_week": "Каждую неделю",
        "field_once": "Разово (с датой)",
        "field_weekday": "День недели",
        "field_date": "Дата (ГГГГ-ММ-ДД)",
        "field_time": "Время",
        "quick": "Быстро:",
        "btn_save": "Сохранить",
        "btn_cancel": "Отмена",
        "btn_close": "Закрыть",
        "btn_done": "Выполнено",
        "btn_skip": "Пропустить",
        "task_details": "Детали задачи",
        "task_type": "Тип",
        "task_when": "Когда",
        "warn_name": "Введите название цели",
        "warn_date": "Неверный формат даты",
        "warn_time": "Неверное время",
        "pick_task": "Выберите задачу",
        "pick": "Выбор",
        "notify_title": "Напоминание",
        "notify_error": "Ошибка",
        "notify_cant_open": "Не удалось открыть папку",
        "quick_create": "Создать цель",
        "quick_once": "Разово на этот день",
        "quick_weekly": "Каждую неделю в этот день",
        "quick_time": "Время",
    },
    "en": {
        "app_title": "Apple Planner",
        "tab_week": "Week schedule",
        "tab_tasks": "All tasks",
        "tab_settings": "Customization",
        "today": "Today",
        "new_goal": "New goal",
        "all_tasks": "All tasks",
        "mark_done": "Mark as done",
        "skip": "Skip",
        "delete": "Delete",
        "done_col": "STATUS",
        "type_col": "TYPE",
        "name_col": "NAME",
        "when_col": "WHEN",
        "status_done": "✓ Done",
        "status_pending": "◌ Pending",
        "status_skipped": "⊘ Skipped",
        "type_once": "One-time",
        "type_weekly": "Weekly",
        "sec_theme": "Appearance",
        "sec_theme_sub": "Choose the app palette",
        "sec_font": "Typography",
        "sec_font_sub": "Font family and size",
        "sec_lang": "Language",
        "sec_lang_sub": "Interface language",
        "sec_misc": "Additional",
        "sec_misc_sub": "Interface behavior",
        "sec_data": "Data",
        "sec_data_sub": "Where your tasks are stored",
        "font_family": "Family",
        "font_size": "Size",
        "font_preview": "Sample task text",
        "font_preview_sub": "This is how the text will look",
        "show_weekend": "Show Saturday and Sunday in schedule",
        "autosave_on": "Autosave is enabled",
        "autosave_desc": "All goals are stored in a system folder and saved on each action",
        "open_folder": "Open data folder",
        "reset_settings": "Reset settings",
        "reset_confirm": "Reset appearance settings?",
        "new_dialog_title": "New goal",
        "new_dialog_sub": "Specify what and when you want to do",
        "field_what": "What to do?",
        "field_repeat": "Repeat",
        "field_every_week": "Every week",
        "field_once": "One-time (with date)",
        "field_weekday": "Weekday",
        "field_date": "Date (YYYY-MM-DD)",
        "field_time": "Time",
        "quick": "Quick:",
        "btn_save": "Save",
        "btn_cancel": "Cancel",
        "btn_close": "Close",
        "btn_done": "Done",
        "btn_skip": "Skip",
        "task_details": "Task details",
        "task_type": "Type",
        "task_when": "When",
        "warn_name": "Enter a goal name",
        "warn_date": "Invalid date format",
        "warn_time": "Invalid time",
        "pick_task": "Select a task",
        "pick": "Selection",
        "notify_title": "Reminder",
        "notify_error": "Error",
        "notify_cant_open": "Could not open folder",
        "quick_create": "Create goal",
        "quick_once": "One-time on this day",
        "quick_weekly": "Every week on this day",
        "quick_time": "Time",
    },
}

WEEKDAYS_FULL = {
    "ru": ["Понедельник", "Вторник", "Среда", "Четверг",
           "Пятница", "Суббота", "Воскресенье"],
    "en": ["Monday", "Tuesday", "Wednesday", "Thursday",
           "Friday", "Saturday", "Sunday"],
}
WEEKDAYS_MINI = {
    "ru": ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"],
    "en": ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"],
}
MONTHS = {
    "ru": ["января", "февраля", "марта", "апреля", "мая", "июня",
           "июля", "августа", "сентября", "октября", "ноября", "декабря"],
    "en": ["January", "February", "March", "April", "May", "June",
           "July", "August", "September", "October", "November", "December"],
}


def L(key, lang):
    return TRANSLATIONS.get(lang, TRANSLATIONS["ru"]).get(key, key)


# ─── Темы ─────────────────────────────────────────────────────
THEMES = {
    "Apple Planner (Violet)": {
        "bg": "#0b0817", "bg_soft": "#100c20", "card": "#151029",
        "card2": "#1c1537", "card3": "#241c45",
        "text": "#ddd6f0", "subtext": "#8b82b8", "muted": "#544d80",
        "accent": "#a78bfa", "accent2": "#c4b1ff", "accent_dk": "#7c5ce0",
        "danger": "#f472b6", "danger2": "#ec4899", "success": "#9d7bff",
        "grid": "#1e1840", "grid_soft": "#171233",
        "today": "#a78bfa", "today_bg": "#161029",
    },
    "Forest Green": {
        "bg": "#f2f8f4", "bg_soft": "#e8f2ec", "card": "#ffffff",
        "card2": "#eef6f1", "card3": "#dcece3",
        "text": "#1a2e24", "subtext": "#4a6d5a", "muted": "#8aa89a",
        "accent": "#22c55e", "accent2": "#4ade80", "accent_dk": "#16a34a",
        "danger": "#ef4444", "danger2": "#dc2626", "success": "#10b981",
        "grid": "#d4e6db", "grid_soft": "#e8f2ec",
        "today": "#16a34a", "today_bg": "#e0f2e7",
    },
    "Ocean Blue": {
        "bg": "#061321", "bg_soft": "#0a1b2c", "card": "#0e2235",
        "card2": "#142d44", "card3": "#1a3854",
        "text": "#d0e4f5", "subtext": "#7a9ab8", "muted": "#4a6d8a",
        "accent": "#5fb3f5", "accent2": "#8ecafc", "accent_dk": "#2d87d6",
        "danger": "#f87171", "danger2": "#ef4444", "success": "#34d399",
        "grid": "#173049", "grid_soft": "#0f2435",
        "today": "#5fb3f5", "today_bg": "#0e2235",
    },
    "Sunset Orange": {
        "bg": "#170d0a", "bg_soft": "#201310", "card": "#2a1a14",
        "card2": "#35221a", "card3": "#422a20",
        "text": "#f5dfd0", "subtext": "#b88c78", "muted": "#7a5c4d",
        "accent": "#ff9b5c", "accent2": "#ffb988", "accent_dk": "#d97742",
        "danger": "#f472b6", "danger2": "#ec4899", "success": "#facc15",
        "grid": "#3a2620", "grid_soft": "#2a1a14",
        "today": "#ff9b5c", "today_bg": "#2a1a14",
    },
    "Monochrome": {
        "bg": "#0d0d10", "bg_soft": "#131317", "card": "#18181d",
        "card2": "#1f1f26", "card3": "#282830",
        "text": "#e5e5ea", "subtext": "#9a9aa5", "muted": "#5c5c66",
        "accent": "#c4c4cf", "accent2": "#e0e0e8", "accent_dk": "#8a8a96",
        "danger": "#f87171", "danger2": "#ef4444", "success": "#a3e635",
        "grid": "#24242c", "grid_soft": "#1a1a20",
        "today": "#c4c4cf", "today_bg": "#18181d",
    },
    "Lavender": {
        "bg": "#100b18", "bg_soft": "#181020", "card": "#1f1429",
        "card2": "#291a36", "card3": "#352244",
        "text": "#eadbf5", "subtext": "#b090c4", "muted": "#6f5a80",
        "accent": "#d8a4f0", "accent2": "#e8c1fa", "accent_dk": "#b070d4",
        "danger": "#f472b6", "danger2": "#ec4899", "success": "#c084fc",
        "grid": "#332040", "grid_soft": "#251835",
        "today": "#d8a4f0", "today_bg": "#1f1429",
    },
    "Розовая (Sakura)": {
        "bg": "#131020", "bg_soft": "#1a1628", "card": "#232136",
        "card2": "#2a273f", "card3": "#34314a",
        "text": "#e0def4", "subtext": "#b8b0d8", "muted": "#7a7294",
        "accent": "#eb6f92", "accent2": "#f08ba9", "accent_dk": "#d55b7e",
        "danger": "#ebbcba", "danger2": "#d7a8a6", "success": "#9ccfd8",
        "grid": "#3a3754", "grid_soft": "#2f2c48",
        "today": "#f6c177", "today_bg": "#332c3f",
    },
    "Светлая": {
        "bg": "#f7f7fb", "bg_soft": "#efeff5", "card": "#ffffff",
        "card2": "#f2f2f8", "card3": "#e8e8f2",
        "text": "#1c1c2e", "subtext": "#5c5c78", "muted": "#9696ae",
        "accent": "#7c5cff", "accent2": "#9d85ff", "accent_dk": "#5b3fd6",
        "danger": "#ff4d6d", "danger2": "#e63456", "success": "#22c55e",
        "grid": "#e0e0ec", "grid_soft": "#eeeeF5",
        "today": "#ff9500", "today_bg": "#fff4e0",
    },
    "Nord": {
        "bg": "#242933", "bg_soft": "#2a303c", "card": "#2e3440",
        "card2": "#3b4252", "card3": "#434c5e",
        "text": "#eceff4", "subtext": "#d8dee9", "muted": "#7b88a1",
        "accent": "#88c0d0", "accent2": "#a3d4e0", "accent_dk": "#6fa8b8",
        "danger": "#bf616a", "danger2": "#a54b53", "success": "#a3be8c",
        "grid": "#4c566a", "grid_soft": "#3d4552",
        "today": "#ebcb8b", "today_bg": "#3d3a33",
    },
}

FONTS = ["Segoe UI", "Arial", "Helvetica", "Verdana",
         "Tahoma", "Courier New", "Georgia", "Consolas",
         "Inter", "SF Pro Display", "Roboto"]

LANGUAGES = {"ru": "Русский", "en": "English"}

DEFAULT_SETTINGS = {
    "theme": "Apple Planner (Violet)",
    "font_family": "Segoe UI",
    "font_size": 10,
    "show_weekend": True,
    "language": "ru",
}


# ─── RoundedButton ────────────────────────────────────────────
class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command, bg, fg, hover_bg=None,
                 font=("Segoe UI", 10), width=150, height=38,
                 radius=10, icon="", **kwargs):
        super().__init__(parent, width=width, height=height,
                         bg=parent.cget("bg"), highlightthickness=0,
                         bd=0, **kwargs)
        self.command = command
        self.bg_color = bg
        self.fg_color = fg
        self.hover_bg = hover_bg or self._lighten(bg)
        self.radius = radius
        self.text = f"{icon} {text}".strip() if icon else text
        self.font = font
        self.w = width
        self.h = height

        self._draw(self.bg_color)
        self.bind("<Button-1>", lambda e: self.command())
        self.bind("<Enter>", lambda e: self._draw(self.hover_bg))
        self.bind("<Leave>", lambda e: self._draw(self.bg_color))
        self.configure(cursor="hand2")

    def _lighten(self, hex_color, amount=0.15):
        try:
            hex_color = hex_color.lstrip("#")
            r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            r = min(255, int(r + (255 - r) * amount))
            g = min(255, int(g + (255 - g) * amount))
            b = min(255, int(b + (255 - b) * amount))
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return hex_color

    def _round_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1 + r, y1, x1 + r, y1, x2 - r, y1, x2 - r, y1,
            x2, y1, x2, y1 + r, x2, y1 + r, x2, y2 - r,
            x2, y2 - r, x2, y2, x2 - r, y2, x2 - r, y2,
            x1 + r, y2, x1 + r, y2, x1, y2, x1, y2 - r,
            x1, y2 - r, x1, y1 + r, x1, y1 + r, x1, y1,
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _draw(self, color):
        self.delete("all")
        self._round_rect(1, 1, self.w - 1, self.h - 1, self.radius,
                         fill=color, outline="")
        self.create_text(self.w / 2, self.h / 2, text=self.text,
                         fill=self.fg_color, font=self.font)

    def set_colors(self, bg, fg, hover_bg=None):
        self.bg_color = bg
        self.fg_color = fg
        self.hover_bg = hover_bg or self._lighten(bg)
        self._draw(bg)


class RoundedFrame(tk.Canvas):
    def __init__(self, parent, bg, radius=14, border=None, border_width=0, **kwargs):
        parent_bg = parent.cget("bg") if hasattr(parent, "cget") else "#000000"
        super().__init__(parent, bg=parent_bg, highlightthickness=0, bd=0, **kwargs)
        self.frame_bg = bg
        self.radius = radius
        self.border = border
        self.border_width = border_width
        self.inner = tk.Frame(self, bg=bg)
        self.bind("<Configure>", self._redraw)

    def _redraw(self, event=None):
        try:
            self.delete("bg")
            w = self.winfo_width()
            h = self.winfo_height()
            if w < 10 or h < 10:
                return
            r = min(self.radius, w // 2, h // 2)
            points = [
                r, 0, r, 0, w - r, 0, w - r, 0,
                w, 0, w, r, w, r, w, h - r,
                w, h - r, w, h, w - r, h, w - r, h,
                r, h, r, h, 0, h, 0, h - r,
                0, h - r, 0, r, 0, r, 0, 0,
            ]
            self.create_polygon(points, smooth=True, fill=self.frame_bg,
                                 outline=self.border if self.border else "",
                                 width=self.border_width, tags="bg")
            self.tag_lower("bg")
            self.inner.place(x=self.border_width + 2,
                             y=self.border_width + 2,
                             width=max(1, w - 2 * (self.border_width + 2)),
                             height=max(1, h - 2 * (self.border_width + 2)))
        except Exception:
            pass


# ─── Чипсы дня недели ────────────────────────────────────────
class WeekdayPicker(tk.Frame):
    def __init__(self, parent, colors, font_getter, lang, initial=None):
        super().__init__(parent, bg=colors["card"])
        self.c = colors
        self.font_getter = font_getter
        self.lang = lang
        self.selected = initial if initial is not None else datetime.now().weekday()
        self.buttons = []

        for i, name in enumerate(WEEKDAYS_MINI[lang]):
            is_weekend = i >= 5
            btn = tk.Label(
                self, text=name,
                bg=colors["card2"],
                fg=colors["text"] if not is_weekend else colors["muted"],
                font=font_getter(0, "bold"),
                padx=14, pady=8, cursor="hand2",
            )
            btn.pack(side="left", padx=3)
            btn.bind("<Button-1>", lambda e, idx=i: self.select(idx))
            self.buttons.append(btn)

        self._refresh()

    def select(self, idx):
        self.selected = idx
        self._refresh()

    def _refresh(self):
        c = self.c
        for i, btn in enumerate(self.buttons):
            try:
                if i == self.selected:
                    btn.configure(bg=c["accent"], fg=c["bg"])
                else:
                    is_weekend = i >= 5
                    btn.configure(
                        bg=c["card2"],
                        fg=c["muted"] if is_weekend else c["text"],
                    )
            except Exception:
                pass

    def get(self):
        return WEEKDAYS_FULL[self.lang][self.selected]


# ─── Селектор времени ────────────────────────────────────────
class TimePicker(tk.Frame):
    def __init__(self, parent, colors, font_getter, lang, initial="09:00"):
        super().__init__(parent, bg=colors["card"])
        self.c = colors
        self.font_getter = font_getter
        self.lang = lang

        try:
            h, m = map(int, initial.split(":"))
        except Exception:
            h, m = 9, 0
        self.hour = h
        self.minute = m

        row = tk.Frame(self, bg=colors["card"])
        row.pack(anchor="w")

        self.hour_lbl = tk.Label(row, text=f"{h:02d}", bg=colors["card2"],
                                  fg=colors["text"], font=font_getter(3, "bold"),
                                  padx=12, pady=6, cursor="hand2")
        self.hour_lbl.pack(side="left")
        self.hour_lbl.bind("<Button-1>", lambda e: self.spin_hour(1))
        self.hour_lbl.bind("<Button-3>", lambda e: self.spin_hour(-1))
        self.hour_lbl.bind("<MouseWheel>",
                            lambda e: self.spin_hour(1 if e.delta > 0 else -1))

        tk.Label(row, text=":", bg=colors["card"], fg=colors["text"],
                 font=font_getter(3, "bold")).pack(side="left", padx=4)

        self.min_lbl = tk.Label(row, text=f"{m:02d}", bg=colors["card2"],
                                 fg=colors["text"], font=font_getter(3, "bold"),
                                 padx=12, pady=6, cursor="hand2")
        self.min_lbl.pack(side="left")
        self.min_lbl.bind("<Button-1>", lambda e: self.spin_min(5))
        self.min_lbl.bind("<Button-3>", lambda e: self.spin_min(-5))
        self.min_lbl.bind("<MouseWheel>",
                           lambda e: self.spin_min(5 if e.delta > 0 else -5))

        arrows = tk.Frame(row, bg=colors["card"])
        arrows.pack(side="left", padx=(10, 0))
        up = tk.Label(arrows, text="▲", bg=colors["card"], fg=colors["muted"],
                       font=font_getter(-1), cursor="hand2")
        up.pack()
        up.bind("<Button-1>", lambda e: self.spin_hour(1))
        dn = tk.Label(arrows, text="▼", bg=colors["card"], fg=colors["muted"],
                       font=font_getter(-1), cursor="hand2")
        dn.pack()
        dn.bind("<Button-1>", lambda e: self.spin_hour(-1))

        arrows2 = tk.Frame(row, bg=colors["card"])
        arrows2.pack(side="left", padx=(6, 0))
        up2 = tk.Label(arrows2, text="▲", bg=colors["card"], fg=colors["muted"],
                        font=font_getter(-1), cursor="hand2")
        up2.pack()
        up2.bind("<Button-1>", lambda e: self.spin_min(5))
        dn2 = tk.Label(arrows2, text="▼", bg=colors["card"], fg=colors["muted"],
                        font=font_getter(-1), cursor="hand2")
        dn2.pack()
        dn2.bind("<Button-1>", lambda e: self.spin_min(-5))

        presets = tk.Frame(self, bg=colors["card"])
        presets.pack(anchor="w", pady=(10, 0))
        tk.Label(presets, text=L("quick", lang), bg=colors["card"],
                 fg=colors["muted"],
                 font=font_getter(-2)).pack(side="left", padx=(0, 6))

        for label, hh, mm in [("08:00", 8, 0), ("12:00", 12, 0),
                               ("15:00", 15, 0), ("18:00", 18, 0),
                               ("20:00", 20, 0), ("21:00", 21, 0)]:
            b = tk.Label(presets, text=label, bg=colors["card2"],
                          fg=colors["subtext"], font=font_getter(-1),
                          padx=8, pady=3, cursor="hand2")
            b.pack(side="left", padx=2)
            b.bind("<Button-1>", lambda e, h=hh, m=mm: self.set_time(h, m))

    def spin_hour(self, delta):
        self.hour = (self.hour + delta) % 24
        self._update()

    def spin_min(self, delta):
        self.minute = (self.minute + delta) % 60
        self._update()

    def set_time(self, h, m):
        self.hour, self.minute = h, m
        self._update()

    def _update(self):
        self.hour_lbl.config(text=f"{self.hour:02d}")
        self.min_lbl.config(text=f"{self.minute:02d}")

    def get(self):
        return f"{self.hour:02d}:{self.minute:02d}"


# ─── Основное приложение ─────────────────────────────────────
class TaskScheduler:
    def __init__(self, root):
        self.root = root
        self.root.geometry("1180x780")
        self.root.minsize(980, 660)

        self.settings = self.load_settings()
        self.lang = self.settings.get("language", "ru")
        self.tasks = self.load_tasks()
        self.c = THEMES.get(self.settings["theme"], THEMES["Apple Planner (Violet)"])

        self.root.title(f"🍎 {L('app_title', self.lang)}")

        print("=" * 60)
        print(f"📁 Папка данных: {APP_DIR}")
        print(f"📋 Файл задач:   {DATA_FILE}")
        print(f"📦 Загружено задач: {len(self.tasks)}")
        print("=" * 60)

        self._apply_window_bg()
        self.build_ui()
        self.refresh_week_view()
        self.refresh_tasks_list()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        atexit.register(self.force_save_all)

        try:
            signal.signal(signal.SIGINT, self._signal_handler)
        except (ValueError, AttributeError):
            pass

        self.running = True
        threading.Thread(target=self.check_loop, daemon=True).start()
        self.root.after(60000, self.auto_refresh)

    # ─── Данные ──────────────────────────────────────────────
    def _safe_load_json(self, path, default=None, backup_path=None):
        default = default if default is not None else []
        if not os.path.exists(path):
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not isinstance(data, type(default)):
                    raise ValueError("Неверный формат")
                return data
        except Exception as e:
            print(f"[!] Ошибка чтения {path}: {e}")
            if backup_path and os.path.exists(backup_path):
                try:
                    with open(backup_path, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass
            return default

    def _safe_save_json(self, path, data, make_backup=False):
        try:
            tmp_path = path + ".tmp"
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            if make_backup and os.path.exists(path):
                try:
                    shutil.copy2(path, BACKUP_FILE)
                except Exception:
                    pass
            os.replace(tmp_path, path)
            return True
        except Exception as e:
            print(f"[!] Ошибка сохранения {path}: {e}")
            return False

    def load_settings(self):
        data = self._safe_load_json(SETTINGS_FILE, default={})
        merged = DEFAULT_SETTINGS.copy()
        if isinstance(data, dict):
            merged.update(data)
        return merged

    def save_settings(self):
        self._safe_save_json(SETTINGS_FILE, self.settings)

    def load_tasks(self):
        data = self._safe_load_json(DATA_FILE, default=[], backup_path=BACKUP_FILE)
        if not isinstance(data, list):
            return []
        valid = []
        for t in data:
            if not isinstance(t, dict):
                continue
            if "id" not in t or "name" not in t or "type" not in t:
                continue
            if t["type"] not in ("once", "weekly"):
                continue
            if "skipped" not in t:
                t["skipped"] = False
            valid.append(t)
        return valid

    def save_tasks(self):
        self._safe_save_json(DATA_FILE, self.tasks, make_backup=True)

    def force_save_all(self):
        try:
            self.save_tasks()
            self.save_settings()
            print(f"[✓] Данные сохранены: {APP_DIR}")
        except Exception as e:
            print(f"[!] Ошибка финального сохранения: {e}")

    def on_close(self):
        self.running = False
        self.force_save_all()
        try:
            self.root.destroy()
        except Exception:
            pass

    def _signal_handler(self, signum, frame):
        self.force_save_all()
        try:
            self.root.quit()
        except Exception:
            pass

    def _apply_window_bg(self):
        self.root.configure(bg=self.c["bg"])

    def font(self, size_delta=0, weight="normal"):
        return (self.settings["font_family"],
                self.settings["font_size"] + size_delta, weight)

    def open_data_folder(self):
        try:
            path = str(APP_DIR)
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except Exception as e:
            messagebox.showerror(L("notify_error", self.lang),
                                  f"{L('notify_cant_open', self.lang)}: {e}")

    # ─── UI ──────────────────────────────────────────────────
    def build_ui(self):
        c = self.c

        top = tk.Frame(self.root, bg=c["bg"])
        top.pack(fill="x", padx=28, pady=(22, 10))

        title_row = tk.Frame(top, bg=c["bg"])
        title_row.pack(side="left")
        tk.Label(title_row, text="🍎", bg=c["bg"], fg=c["text"],
                 font=(self.settings["font_family"], 16)).pack(side="left")
        tk.Label(title_row, text=" " + L("app_title", self.lang),
                 bg=c["bg"], fg=c["text"],
                 font=self.font(8, "bold")).pack(side="left")

        right = tk.Frame(top, bg=c["bg"])
        right.pack(side="right")
        now = datetime.now()
        months = MONTHS[self.lang]
        today_str = f"{now.day} {months[now.month - 1]} {now.year}"
        tk.Label(right, text=f"● {today_str}", bg=c["bg"], fg=c["accent"],
                 font=self.font(0, "bold")).pack(anchor="e")

        tk.Frame(self.root, bg=c["grid"], height=1).pack(fill="x", padx=28)

        self.tab_bar = tk.Frame(self.root, bg=c["bg"])
        self.tab_bar.pack(fill="x", padx=28, pady=(14, 10))

        self.current_tab = "week"
        self.tab_buttons = {}
        for key, label_key, icon in [
            ("week", "tab_week", "▦"),
            ("tasks", "tab_tasks", "☰"),
            ("settings", "tab_settings", "✦"),
        ]:
            btn = RoundedButton(
                self.tab_bar, text=L(label_key, self.lang), icon=icon,
                command=lambda k=key: self.switch_tab(k),
                bg=c["bg"], fg=c["muted"], hover_bg=c["card"],
                font=self.font(0, "bold"), width=200, height=40, radius=12,
            )
            btn.pack(side="left", padx=(0, 8))
            self.tab_buttons[key] = btn

        self.update_tab_styles()

        self.content = tk.Frame(self.root, bg=c["bg"])
        self.content.pack(fill="both", expand=True, padx=28, pady=(0, 20))

        self.tab_week = tk.Frame(self.content, bg=c["bg"])
        self.tab_tasks = tk.Frame(self.content, bg=c["bg"])
        self.tab_settings = tk.Frame(self.content, bg=c["bg"])

        self.build_week_tab()
        self.build_tasks_tab()
        self.build_settings_tab()
        self.switch_tab("week")

    def update_tab_styles(self):
        c = self.c
        for key, btn in self.tab_buttons.items():
            if key == self.current_tab:
                btn.set_colors(c["card2"], c["accent"], c["card3"])
            else:
                btn.set_colors(c["bg"], c["muted"], c["card"])

    def switch_tab(self, key):
        self.current_tab = key
        for frame in (self.tab_week, self.tab_tasks, self.tab_settings):
            frame.pack_forget()
        target = {"week": self.tab_week, "tasks": self.tab_tasks,
                  "settings": self.tab_settings}[key]
        target.pack(fill="both", expand=True)
        self.update_tab_styles()
        if key == "week":
            self.refresh_week_view()
        elif key == "tasks":
            self.refresh_tasks_list()

    # ─── Вкладка "Неделя" ────────────────────────────────────
    def build_week_tab(self):
        c = self.c

        nav = tk.Frame(self.tab_week, bg=c["bg"])
        nav.pack(fill="x", pady=(0, 14))

        left_nav = tk.Frame(nav, bg=c["bg"])
        left_nav.pack(side="left")

        # Стрелки: листание недели по 7 дней
        RoundedButton(left_nav, text="", icon="‹",
                      command=lambda: self.shift_week(-7),
                      bg=c["card"], fg=c["text"], hover_bg=c["card2"],
                      font=self.font(2, "bold"),
                      width=44, height=40, radius=12).pack(side="left")

        RoundedButton(left_nav, text=L("today", self.lang), command=self.go_today,
                      bg=c["card"], fg=c["text"], hover_bg=c["card2"],
                      font=self.font(0, "bold"),
                      width=110, height=40, radius=12).pack(side="left", padx=6)

        RoundedButton(left_nav, text="", icon="›",
                      command=lambda: self.shift_week(7),
                      bg=c["card"], fg=c["text"], hover_bg=c["card2"],
                      font=self.font(2, "bold"),
                      width=44, height=40, radius=12).pack(side="left")

        self.week_range_label = tk.Label(nav, text="", bg=c["bg"],
                                          fg=c["subtext"],
                                          font=self.font(1, "bold"))
        self.week_range_label.pack(side="left", padx=18)

        RoundedButton(nav, text=L("new_goal", self.lang), icon="+",
                      command=self.open_add_dialog,
                      bg=c["accent_dk"], fg="#ffffff",
                      hover_bg=c["accent"],
                      font=self.font(0, "bold"),
                      width=160, height=40, radius=12).pack(side="right")

        self.schedule_container = tk.Frame(self.tab_week, bg=c["bg"])
        self.schedule_container.pack(fill="both", expand=True)

        today = datetime.now()
        self.week_start = today - timedelta(days=today.weekday())

    def refresh_week_view(self):
        c = self.c
        try:
            for w in self.schedule_container.winfo_children():
                w.destroy()
        except Exception:
            return

        end = self.week_start + timedelta(days=6)
        months = MONTHS[self.lang]

        if self.week_start.month == end.month:
            rng = f"{self.week_start.day}–{end.day} {months[end.month - 1]} {end.year}"
        else:
            rng = (f"{self.week_start.day} {months[self.week_start.month - 1]} — "
                   f"{end.day} {months[end.month - 1]} {end.year}")
        self.week_range_label.config(text=rng)

        days_to_show = 7 if self.settings.get("show_weekend", True) else 5

        header = tk.Frame(self.schedule_container, bg=c["bg"])
        header.pack(fill="x", pady=(0, 6))

        corner = tk.Frame(header, bg=c["bg"], width=54)
        corner.pack(side="left")
        corner.pack_propagate(False)

        for i in range(days_to_show):
            day_date = self.week_start + timedelta(days=i)
            is_today = day_date.date() == datetime.now().date()
            is_weekend = i >= 5

            col = tk.Frame(header, bg=c["bg"])
            col.pack(side="left", fill="x", expand=True, padx=2)

            card_bg = c["card"]
            card = tk.Frame(col, bg=card_bg, height=54, cursor="hand2")
            card.pack(fill="x")
            card.pack_propagate(False)

            if is_today:
                stripe = tk.Frame(card, bg=c["accent"], height=2)
                stripe.pack(fill="x")

            inner = tk.Frame(card, bg=card_bg, cursor="hand2")
            inner.pack(expand=True)

            if is_today:
                day_color = c["accent"]
                date_color = c["accent"]
            elif is_weekend:
                day_color = c["muted"]
                date_color = c["subtext"]
            else:
                day_color = c["subtext"]
                date_color = c["text"]

            day_lbl = tk.Label(inner, text=WEEKDAYS_MINI[self.lang][i],
                                bg=card_bg, fg=day_color,
                                font=(self.settings["font_family"],
                                      self.settings["font_size"] - 2),
                                cursor="hand2")
            day_lbl.pack()
            date_lbl = tk.Label(inner, text=day_date.strftime("%d"), bg=card_bg,
                                 fg=date_color,
                                 font=(self.settings["font_family"],
                                       self.settings["font_size"] + 2,
                                       "bold"),
                                 cursor="hand2")
            date_lbl.pack()

            for w in (card, inner, day_lbl, date_lbl):
                w.bind("<Button-1>",
                        lambda e, d=day_date: self.open_quick_create(d, None))

        body_wrap = tk.Frame(self.schedule_container, bg=c["bg"])
        body_wrap.pack(fill="both", expand=True)

        canvas = tk.Canvas(body_wrap, bg=c["bg"], highlightthickness=0)
        sb = tk.Scrollbar(body_wrap, orient="vertical", command=canvas.yview,
                          bd=0, width=6)
        inner_canvas = tk.Frame(canvas, bg=c["bg"])

        inner_canvas.bind("<Configure>",
                           lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        window_id = canvas.create_window((0, 0), window=inner_canvas, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        canvas.bind("<Configure>",
                     lambda e: canvas.itemconfig(window_id, width=e.width))

        def _wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind("<MouseWheel>", _wheel)

        start_hour, end_hour = 6, 23
        row_height = 44

        for hour in range(start_hour, end_hour + 1):
            row = tk.Frame(inner_canvas, bg=c["bg"], height=row_height)
            row.pack(fill="x")
            row.pack_propagate(False)

            tk.Label(row, text=f"{hour:02d}:00", bg=c["bg"], fg=c["muted"],
                     font=(self.settings["font_family"], 9),
                     width=6, anchor="e").pack(side="left", padx=(0, 6))

            for i in range(days_to_show):
                day_date = self.week_start + timedelta(days=i)
                is_today = day_date.date() == datetime.now().date()

                cell = tk.Frame(row, bg=c["grid_soft"] if not is_today
                                 else c["card2"],
                                 height=row_height - 2, cursor="hand2")
                cell.pack(side="left", fill="both", expand=True, padx=1, pady=1)
                cell.pack_propagate(False)

                day_tasks = self.get_tasks_for_day(day_date, hour)

                if not day_tasks:
                    cell.bind("<Button-1>",
                               lambda e, d=day_date, h=hour:
                               self.open_quick_create(d, h))
                else:
                    for t in day_tasks:
                        self.render_task_in_cell(cell, t)

        tk.Frame(inner_canvas, bg=c["bg"], height=20).pack()

    def get_tasks_for_day(self, day_date, hour):
        result = []
        for t in self.tasks:
            if t.get("done"):
                continue
            if t["type"] == "once":
                try:
                    dt = datetime.strptime(t["datetime"], "%Y-%m-%d %H:%M")
                except ValueError:
                    continue
                if dt.date() == day_date.date() and dt.hour == hour:
                    result.append((dt, t))
            elif t["type"] == "weekly":
                wd_full = WEEKDAYS_FULL["ru"]
                try:
                    wd = wd_full.index(t["weekday"])
                except (ValueError, KeyError):
                    wd = -1
                if wd != day_date.weekday():
                    continue
                try:
                    h, m = map(int, t["time"].split(":"))
                except ValueError:
                    continue
                if h == hour:
                    result.append((day_date.replace(hour=h, minute=m), t))
        result.sort(key=lambda x: x[0])
        return [t for _, t in result]

    def render_task_in_cell(self, parent, task):
        c = self.c
        is_weekly = task["type"] == "weekly"
        is_skipped = task.get("skipped", False)

        if is_skipped:
            block_color = c["card2"]
            text_color = c["muted"]
        else:
            block_color = c["accent_dk"] if is_weekly else c["card3"]
            text_color = "#ffffff" if is_weekly else c["text"]

        block = tk.Frame(parent, bg=block_color, cursor="hand2")
        block.pack(fill="both", expand=True, padx=2, pady=2)

        short = task["name"]
        if len(short) > 20:
            short = short[:18] + "…"

        if is_skipped:
            icon = "⊘"
        elif is_weekly:
            icon = "↻"
        else:
            icon = "•"

        lbl = tk.Label(block, text=f"{icon} {short}", bg=block_color,
                        fg=text_color,
                        font=(self.settings["font_family"],
                              self.settings["font_size"] - 2),
                        anchor="w", cursor="hand2", padx=6)
        lbl.pack(fill="both", expand=True)

        def click(e): self.open_task_menu(task)
        def enter(e):
            if is_skipped:
                h = c["card3"]
            else:
                h = c["accent"] if is_weekly else c["card2"]
            block.configure(bg=h)
            lbl.configure(bg=h)
        def leave(e):
            block.configure(bg=block_color)
            lbl.configure(bg=block_color)

        for w in (block, lbl):
            w.bind("<Button-1>", click)
        block.bind("<Enter>", enter); block.bind("<Leave>", leave)
        lbl.bind("<Enter>", enter); lbl.bind("<Leave>", leave)

    # ─── Мини-меню создания по клику ─────────────────────────
    def open_quick_create(self, day_date, hour):
        c = self.c

        pre_hour = hour if hour is not None else 9
        pre_time = f"{pre_hour:02d}:00"

        win = tk.Toplevel(self.root)
        win.title(L("quick_create", self.lang))
        win.geometry("420x420")
        win.configure(bg=c["bg"])
        win.transient(self.root); win.grab_set()
        win.resizable(False, False)

        win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 420) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 420) // 2
        win.geometry(f"+{x}+{y}")

        head = tk.Frame(win, bg=c["bg"])
        head.pack(fill="x", padx=24, pady=(20, 8))

        months = MONTHS[self.lang]
        wd_name = WEEKDAYS_FULL[self.lang][day_date.weekday()]
        date_str = f"{wd_name}, {day_date.day} {months[day_date.month - 1]}"
        tk.Label(head, text=L("quick_create", self.lang),
                 bg=c["bg"], fg=c["muted"],
                 font=self.font(-1, "bold")).pack(anchor="w")
        tk.Label(head, text=date_str, bg=c["bg"], fg=c["text"],
                 font=self.font(4, "bold")).pack(anchor="w", pady=(2, 0))

        name_card = RoundedFrame(win, bg=c["card"], radius=14,
                                  border=c["grid"], border_width=1, height=80)
        name_card.pack(fill="x", padx=24, pady=(8, 6))
        name_card.pack_propagate(False)
        nc = name_card.inner
        nc.configure(bg=c["card"])

        name_entry = tk.Entry(nc, bg=c["card2"], fg=c["text"],
                               insertbackground=c["text"], bd=0,
                               font=self.font(1), highlightthickness=1,
                               highlightbackground=c["grid"],
                               highlightcolor=c["accent"])
        name_entry.pack(fill="x", ipady=8, pady=18, padx=18)
        name_entry.focus_set()

        time_card = RoundedFrame(win, bg=c["card"], radius=14,
                                  border=c["grid"], border_width=1, height=120)
        time_card.pack(fill="x", padx=24, pady=6)
        time_card.pack_propagate(False)
        tc = time_card.inner
        tc.configure(bg=c["card"])

        tk.Label(tc, text=L("field_time", self.lang), bg=c["card"],
                 fg=c["muted"], font=self.font(-1, "bold")).pack(anchor="w",
                                                                   padx=18,
                                                                   pady=(14, 0))
        time_picker = TimePicker(tc, c, self.font, self.lang, initial=pre_time)
        time_picker.pack(anchor="w", padx=18, pady=(6, 0))

        btns = tk.Frame(win, bg=c["bg"])
        btns.pack(fill="x", padx=24, pady=(16, 20))

        def save_once():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning(L("notify_error", self.lang),
                                         L("warn_name", self.lang))
                return
            try:
                hh, mm = map(int, time_picker.get().split(":"))
            except ValueError:
                return
            dt = day_date.replace(hour=hh, minute=mm, second=0, microsecond=0)
            task = {
                "id": int(time.time() * 1000),
                "name": name,
                "type": "once",
                "done": False,
                "skipped": False,
                "notified": False,
                "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "datetime": dt.strftime("%Y-%m-%d %H:%M"),
            }
            self.tasks.append(task)
            self.save_tasks()
            self.refresh_week_view()
            self.refresh_tasks_list()
            win.destroy()

        def save_weekly():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning(L("notify_error", self.lang),
                                         L("warn_name", self.lang))
                return
            time_str = time_picker.get()
            task = {
                "id": int(time.time() * 1000),
                "name": name,
                "type": "weekly",
                "done": False,
                "skipped": False,
                "notified": False,
                "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "weekday": WEEKDAYS_FULL["ru"][day_date.weekday()],
                "time": time_str,
            }
            self.tasks.append(task)
            self.save_tasks()
            self.refresh_week_view()
            self.refresh_tasks_list()
            win.destroy()

        RoundedButton(btns, text=L("quick_once", self.lang),
                      command=save_once,
                      bg=c["accent_dk"], fg="#ffffff", hover_bg=c["accent"],
                      font=self.font(0, "bold"),
                      width=180, height=44, radius=12).pack(side="left")

        RoundedButton(btns, text=L("quick_weekly", self.lang),
                      command=save_weekly,
                      bg=c["card"], fg=c["accent"], hover_bg=c["card2"],
                      font=self.font(0, "bold"),
                      width=180, height=44, radius=12).pack(side="right")

        win.bind("<Escape>", lambda e: win.destroy())

    # ─── Диалог деталей задачи ───────────────────────────────
    def open_task_menu(self, task):
        c = self.c
        win = tk.Toplevel(self.root)
        win.title(L("task_details", self.lang))
        win.geometry("420x400")
        win.configure(bg=c["bg"])
        win.transient(self.root); win.grab_set()

        win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 420) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 400) // 2
        win.geometry(f"+{x}+{y}")

        header = tk.Frame(win, bg=c["bg"])
        header.pack(fill="x", padx=24, pady=(20, 12))
        tk.Label(header, text=L("task_details", self.lang),
                 bg=c["bg"], fg=c["muted"],
                 font=self.font(-1, "bold")).pack(anchor="w")
        tk.Label(header, text=task["name"], bg=c["bg"], fg=c["text"],
                 font=self.font(4, "bold"),
                 wraplength=360, justify="left").pack(anchor="w", pady=(4, 0))

        info = RoundedFrame(win, bg=c["card"], radius=14, border=c["grid"],
                             border_width=1, height=110)
        info.pack(fill="x", padx=24, pady=(4, 16))
        info.pack_propagate(False)
        inner = info.inner
        inner.configure(bg=c["card"])

        typ = L("type_once", self.lang) if task["type"] == "once" else L("type_weekly", self.lang)
        if task["type"] == "once":
            when = task["datetime"]
        else:
            try:
                idx = WEEKDAYS_FULL["ru"].index(task["weekday"])
                wd_local = WEEKDAYS_FULL[self.lang][idx]
            except (ValueError, KeyError):
                wd_local = task["weekday"]
            when = f"{wd_local}, {task['time']}"

        for label, value, row in [(L("task_type", self.lang), typ, 0),
                                   (L("task_when", self.lang), when, 1)]:
            tk.Label(inner, text=label, bg=c["card"], fg=c["muted"],
                     font=self.font(-1)).grid(row=row, column=0, sticky="w",
                                              padx=18,
                                              pady=(12 if row == 0 else 4, 0))
            tk.Label(inner, text=value, bg=c["card"], fg=c["text"],
                     font=self.font(0, "bold")).grid(row=row, column=1,
                                                     sticky="w", padx=(12, 0),
                                                     pady=(12 if row == 0 else 4, 0))

        btns = tk.Frame(win, bg=c["bg"])
        btns.pack(fill="x", padx=24, pady=(4, 8))
        btns2 = tk.Frame(win, bg=c["bg"])
        btns2.pack(fill="x", padx=24, pady=(0, 20))

        RoundedButton(btns, text=L("btn_done", self.lang), icon="✓",
                      command=lambda: (self.toggle_done(task), win.destroy()),
                      bg=c["accent_dk"], fg="#ffffff", hover_bg=c["accent"],
                      font=self.font(0, "bold"),
                      width=180, height=42, radius=10).pack(side="left")

        RoundedButton(btns, text=L("btn_skip", self.lang), icon="⊘",
                      command=lambda: (self.toggle_skipped(task), win.destroy()),
                      bg=c["card"], fg=c["muted"], hover_bg=c["card2"],
                      font=self.font(0, "bold"),
                      width=180, height=42, radius=10).pack(side="right")

        RoundedButton(btns2, text=L("delete", self.lang), icon="✕",
                      command=lambda: (self.delete_task(task), win.destroy()),
                      bg=c["card"], fg=c["danger"], hover_bg=c["card2"],
                      font=self.font(0, "bold"),
                      width=180, height=42, radius=10).pack(side="left")

        RoundedButton(btns2, text=L("btn_close", self.lang), command=win.destroy,
                      bg=c["card"], fg=c["text"], hover_bg=c["card2"],
                      font=self.font(0), width=180, height=42,
                      radius=10).pack(side="right")

    def toggle_done(self, task):
        task["done"] = not task.get("done", False)
        if task["done"]:
            task["skipped"] = False
        self.save_tasks()
        self.refresh_week_view()
        self.refresh_tasks_list()

    def toggle_skipped(self, task):
        task["skipped"] = not task.get("skipped", False)
        if task["skipped"]:
            task["done"] = False
        self.save_tasks()
        self.refresh_week_view()
        self.refresh_tasks_list()

    def delete_task(self, task):
        if not messagebox.askyesno(L("delete", self.lang),
                                     f"{L('delete', self.lang)} «{task['name']}»?"):
            return
        self.tasks = [t for t in self.tasks if t["id"] != task["id"]]
        self.save_tasks()
        self.refresh_week_view()
        self.refresh_tasks_list()

    def shift_week(self, days):
        self.week_start += timedelta(days=days)
        self.refresh_week_view()

    def go_today(self):
        today = datetime.now()
        self.week_start = today - timedelta(days=today.weekday())
        self.refresh_week_view()

    # ─── Вкладка "Все задачи" ────────────────────────────────
    def build_tasks_tab(self):
        c = self.c

        top = tk.Frame(self.tab_tasks, bg=c["bg"])
        top.pack(fill="x", pady=(0, 14))
        tk.Label(top, text=L("all_tasks", self.lang), bg=c["bg"], fg=c["text"],
                 font=self.font(4, "bold")).pack(side="left")

        RoundedButton(top, text=L("new_goal", self.lang), icon="+",
                      command=self.open_add_dialog,
                      bg=c["accent_dk"], fg="#ffffff", hover_bg=c["accent"],
                      font=self.font(0, "bold"),
                      width=160, height=40, radius=12).pack(side="right")

        table_card = RoundedFrame(self.tab_tasks, bg=c["card"], radius=14,
                                   border=c["grid"], border_width=1)
        table_card.pack(fill="both", expand=True)
        inner = table_card.inner
        inner.configure(bg=c["card"])

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Sched.Treeview", background=c["card"],
                        fieldbackground=c["card"], foreground=c["text"],
                        rowheight=38, borderwidth=0, font=self.font(0))
        style.configure("Sched.Treeview.Heading", background=c["card"],
                        foreground=c["muted"], font=self.font(-1, "bold"),
                        borderwidth=0, relief="flat")
        style.map("Sched.Treeview",
                  background=[("selected", c["accent_dk"])],
                  foreground=[("selected", "#ffffff")])
        style.layout("Sched.Treeview",
                      [("Sched.Treeview.treearea", {"sticky": "nswe"})])

        cols = ("name", "type", "when", "status")
        self.tree = ttk.Treeview(inner, columns=cols, show="headings",
                                  style="Sched.Treeview", selectmode="browse")
        self.tree.heading("name", text=L("name_col", self.lang))
        self.tree.heading("type", text=L("type_col", self.lang))
        self.tree.heading("when", text=L("when_col", self.lang))
        self.tree.heading("status", text=L("done_col", self.lang))
        self.tree.column("name", width=380, anchor="w")
        self.tree.column("type", width=150, anchor="center")
        self.tree.column("when", width=250, anchor="center")
        self.tree.column("status", width=150, anchor="center")

        sb = ttk.Scrollbar(inner, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True,
                        padx=(14, 0), pady=14)
        sb.pack(side="right", fill="y", pady=14, padx=(0, 10))

        btns = tk.Frame(self.tab_tasks, bg=c["bg"])
        btns.pack(fill="x", pady=(12, 0))

        RoundedButton(btns, text=L("mark_done", self.lang), icon="✓",
                      command=self.mark_done_from_list,
                      bg=c["card"], fg=c["text"], hover_bg=c["card2"],
                      font=self.font(0, "bold"),
                      width=200, height=40, radius=12).pack(side="left")

        RoundedButton(btns, text=L("skip", self.lang), icon="⊘",
                      command=self.skip_from_list,
                      bg=c["card"], fg=c["muted"], hover_bg=c["card2"],
                      font=self.font(0, "bold"),
                      width=160, height=40, radius=12).pack(side="left", padx=8)

        RoundedButton(btns, text=L("delete", self.lang), icon="✕",
                      command=self.delete_from_list,
                      bg=c["card"], fg=c["danger"], hover_bg=c["card2"],
                      font=self.font(0, "bold"),
                      width=140, height=40, radius=12).pack(side="left", padx=8)

    def refresh_tasks_list(self):
        if not hasattr(self, "tree"):
            return
        try:
            for i in self.tree.get_children():
                self.tree.delete(i)
        except Exception:
            return
        sorted_tasks = sorted(self.tasks, key=lambda t: (
            t.get("done", False), t.get("skipped", False)))
        for t in sorted_tasks:
            typ = L("type_once", self.lang) if t["type"] == "once" else L("type_weekly", self.lang)
            if t["type"] == "once":
                when = t["datetime"]
            else:
                try:
                    idx = WEEKDAYS_FULL["ru"].index(t["weekday"])
                    wd_local = WEEKDAYS_FULL[self.lang][idx]
                except (ValueError, KeyError):
                    wd_local = t["weekday"]
                when = f"{wd_local}, {t['time']}"

            if t.get("done"):
                status = L("status_done", self.lang)
            elif t.get("skipped"):
                status = L("status_skipped", self.lang)
            else:
                status = L("status_pending", self.lang)

            self.tree.insert("", "end", iid=str(t["id"]),
                              values=(t["name"], typ, when, status))

    def mark_done_from_list(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(L("pick", self.lang), L("pick_task", self.lang))
            return
        for t in self.tasks:
            if t["id"] == int(sel[0]):
                self.toggle_done(t); break

    def skip_from_list(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(L("pick", self.lang), L("pick_task", self.lang))
            return
        for t in self.tasks:
            if t["id"] == int(sel[0]):
                self.toggle_skipped(t); break

    def delete_from_list(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo(L("pick", self.lang), L("pick_task", self.lang))
            return
        for t in self.tasks:
            if t["id"] == int(sel[0]):
                self.delete_task(t); break

    # ─── Вкладка "Кастомизация" ──────────────────────────────
    def build_settings_tab(self):
        c = self.c

        canvas = tk.Canvas(self.tab_settings, bg=c["bg"], highlightthickness=0)
        sb = tk.Scrollbar(self.tab_settings, orient="vertical",
                          command=canvas.yview, bd=0, width=8)
        outer = tk.Frame(canvas, bg=c["bg"])
        outer.bind("<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        wid = canvas.create_window((0, 0), window=outer, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        canvas.bind("<Configure>",
                     lambda e: canvas.itemconfig(wid, width=e.width))

        def _wheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind("<MouseWheel>", _wheel)

        # Язык
        self._section(outer, L("sec_lang", self.lang), L("sec_lang_sub", self.lang))
        lang_card = RoundedFrame(outer, bg=c["card"], radius=16,
                                  border=c["grid"], border_width=1, height=90)
        lang_card.pack(fill="x", pady=(10, 8))
        lang_card.pack_propagate(False)
        li = lang_card.inner
        li.configure(bg=c["card"])

        self.lang_var = tk.StringVar(value=self.lang)
        lang_row = tk.Frame(li, bg=c["card"])
        lang_row.pack(anchor="w", padx=20, pady=22)

        for code, name in LANGUAGES.items():
            tk.Radiobutton(lang_row, text=name, variable=self.lang_var,
                            value=code, bg=c["card"], fg=c["text"],
                            activebackground=c["card"],
                            activeforeground=c["accent"],
                            selectcolor=c["accent_dk"],
                            font=self.font(0),
                            cursor="hand2", highlightthickness=0, bd=0,
                            command=self.change_language).pack(side="left", padx=(0, 24))

        # Темы
        self._section(outer, L("sec_theme", self.lang), L("sec_theme_sub", self.lang))

        theme_names = list(THEMES.keys())
        rows = (len(theme_names) + 2) // 3
        themes_card = RoundedFrame(outer, bg=c["card"], radius=16,
                                    border=c["grid"], border_width=1,
                                    height=80 + rows * 105)
        themes_card.pack(fill="x", pady=(10, 8))
        themes_card.pack_propagate(False)
        ti = themes_card.inner
        ti.configure(bg=c["card"])

        grid = tk.Frame(ti, bg=c["card"])
        grid.pack(fill="both", expand=True, padx=20, pady=18)

        self.theme_var = tk.StringVar(value=self.settings["theme"])

        for i, theme_name in enumerate(theme_names):
            t = THEMES[theme_name]
            col = i % 3
            row = i // 3

            card = tk.Frame(grid, bg=t["card"], cursor="hand2",
                             highlightthickness=2,
                             highlightbackground=c["accent"]
                             if theme_name == self.settings["theme"] else c["grid"])
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            preview = tk.Frame(card, bg=t["bg"], height=44)
            preview.pack(fill="x", padx=6, pady=(6, 0))
            preview.pack_propagate(False)

            tk.Label(preview, text="Aa", bg=t["bg"], fg=t["accent"],
                     font=(self.settings["font_family"], 15, "bold")).pack(side="left",
                                                                          padx=10)

            dots = tk.Frame(preview, bg=t["bg"])
            dots.pack(side="right", padx=10)
            for dot_color in [t["accent"], t["danger"], t["success"]]:
                d = tk.Frame(dots, bg=dot_color, width=10, height=10)
                d.pack(side="left", padx=2)
                d.pack_propagate(False)

            lf = tk.Frame(card, bg=t["card"])
            lf.pack(fill="x", padx=10, pady=8)

            tk.Radiobutton(lf, text=theme_name, variable=self.theme_var,
                            value=theme_name, bg=t["card"], fg=t["text"],
                            activebackground=t["card"],
                            activeforeground=t["text"],
                            selectcolor=t["accent"],
                            font=self.font(-2, "bold"), cursor="hand2",
                            command=self.change_theme,
                            highlightthickness=0, bd=0).pack(anchor="w")

            for w in (card, preview):
                w.bind("<Button-1>",
                        lambda e, n=theme_name: self._select_theme(n))

        for i in range(3):
            grid.columnconfigure(i, weight=1)

        # Шрифт
        self._section(outer, L("sec_font", self.lang), L("sec_font_sub", self.lang))
        font_card = RoundedFrame(outer, bg=c["card"], radius=16,
                                  border=c["grid"], border_width=1, height=180)
        font_card.pack(fill="x", pady=(10, 8))
        font_card.pack_propagate(False)
        fi = font_card.inner
        fi.configure(bg=c["card"])

        row1 = tk.Frame(fi, bg=c["card"])
        row1.pack(fill="x", padx=20, pady=(18, 8))

        tk.Label(row1, text=L("font_family", self.lang), bg=c["card"], fg=c["muted"],
                 font=self.font(-1, "bold")).pack(anchor="w")

        self.font_family_var = tk.StringVar(value=self.settings["font_family"])
        fc = ttk.Combobox(row1, textvariable=self.font_family_var,
                           values=FONTS, state="readonly", width=25,
                           font=self.font(0))
        fc.pack(side="left", pady=(6, 0))
        fc.bind("<<ComboboxSelected>>", lambda e: self.change_font())

        tk.Label(row1, text=L("font_size", self.lang), bg=c["card"], fg=c["muted"],
                 font=self.font(-1, "bold")).pack(side="left",
                                                    padx=(30, 0), anchor="s")
        self.font_size_var = tk.IntVar(value=self.settings["font_size"])
        tk.Spinbox(row1, from_=8, to=18, width=5,
                    textvariable=self.font_size_var, bg=c["card2"], fg=c["text"],
                    bd=0, font=self.font(0), buttonbackground=c["card2"],
                    command=self.change_font,
                    highlightthickness=0).pack(side="left", padx=(10, 0), pady=(6, 0))

        self.font_preview = tk.Label(fi, text=L("font_preview", self.lang),
                                      bg=c["card"], fg=c["text"],
                                      font=(self.settings["font_family"],
                                            self.settings["font_size"] + 4, "bold"))
        self.font_preview.pack(anchor="w", padx=20, pady=(10, 0))
        tk.Label(fi, text=L("font_preview_sub", self.lang),
                 bg=c["card"], fg=c["muted"],
                 font=(self.settings["font_family"],
                       self.settings["font_size"])).pack(anchor="w", padx=20)

        # Дополнительно
        self._section(outer, L("sec_misc", self.lang), L("sec_misc_sub", self.lang))
        opt_card = RoundedFrame(outer, bg=c["card"], radius=16,
                                 border=c["grid"], border_width=1, height=90)
        opt_card.pack(fill="x", pady=(10, 8))
        opt_card.pack_propagate(False)
        oi = opt_card.inner
        oi.configure(bg=c["card"])

        self.weekend_var = tk.BooleanVar(value=self.settings.get("show_weekend", True))
        tk.Checkbutton(oi, text=L("show_weekend", self.lang),
                        variable=self.weekend_var, bg=c["card"], fg=c["text"],
                        activebackground=c["card"], activeforeground=c["text"],
                        selectcolor=c["accent_dk"], font=self.font(0),
                        cursor="hand2", highlightthickness=0, bd=0,
                        command=self.change_weekend).pack(anchor="w", padx=20, pady=20)

        # Данные
        self._section(outer, L("sec_data", self.lang), L("sec_data_sub", self.lang))
        data_card = RoundedFrame(outer, bg=c["card"], radius=16,
                                  border=c["grid"], border_width=1, height=130)
        data_card.pack(fill="x", pady=(10, 8))
        data_card.pack_propagate(False)
        di = data_card.inner
        di.configure(bg=c["card"])

        tk.Label(di, text=L("autosave_on", self.lang),
                 bg=c["card"], fg=c["text"],
                 font=self.font(0, "bold")).pack(anchor="w", padx=20,
                                                   pady=(16, 4))
        tk.Label(di, text=L("autosave_desc", self.lang),
                 bg=c["card"], fg=c["muted"],
                 font=self.font(-2)).pack(anchor="w", padx=20)

        RoundedButton(di, text=L("open_folder", self.lang), icon="📂",
                      command=self.open_data_folder,
                      bg=c["card2"], fg=c["text"], hover_bg=c["accent_dk"],
                      font=self.font(0, "bold"),
                      width=250, height=36, radius=10).pack(anchor="w",
                                                              padx=20,
                                                              pady=(10, 0))

        reset_row = tk.Frame(outer, bg=c["bg"])
        reset_row.pack(fill="x", pady=(12, 30))

        RoundedButton(reset_row, text=L("reset_settings", self.lang), icon="↻",
                      command=self.reset_settings,
                      bg=c["card"], fg=c["danger"], hover_bg=c["card2"],
                      font=self.font(0, "bold"),
                      width=210, height=42, radius=12).pack(side="left")

    def _section(self, parent, title, subtitle):
        c = self.c
        box = tk.Frame(parent, bg=c["bg"])
        box.pack(fill="x", pady=(18, 0))
        tk.Label(box, text=title, bg=c["bg"], fg=c["text"],
                 font=self.font(3, "bold")).pack(anchor="w")
        tk.Label(box, text=subtitle, bg=c["bg"], fg=c["muted"],
                 font=self.font(-1)).pack(anchor="w", pady=(2, 0))

    def _select_theme(self, name):
        self.theme_var.set(name)
        self.change_theme()

    def change_theme(self):
        self.settings["theme"] = self.theme_var.get()
        self.save_settings()
        self.rebuild_ui()

    def change_font(self):
        self.settings["font_family"] = self.font_family_var.get()
        self.settings["font_size"] = self.font_size_var.get()
        self.save_settings()
        try:
            self.font_preview.config(
                font=(self.settings["font_family"],
                      self.settings["font_size"] + 4, "bold"))
        except Exception:
            pass
        self.refresh_week_view()

    def change_weekend(self):
        self.settings["show_weekend"] = self.weekend_var.get()
        self.save_settings()
        self.refresh_week_view()

    def change_language(self):
        self.settings["language"] = self.lang_var.get()
        self.lang = self.settings["language"]
        self.save_settings()
        self.rebuild_ui()

    def reset_settings(self):
        if not messagebox.askyesno(L("reset_settings", self.lang),
                                     L("reset_confirm", self.lang)):
            return
        current_lang = self.settings.get("language", "ru")
        self.settings = DEFAULT_SETTINGS.copy()
        self.settings["language"] = current_lang
        self.lang = current_lang
        self.save_settings()
        self.rebuild_ui()

    def rebuild_ui(self):
        try:
            self.c = THEMES.get(self.settings["theme"], THEMES["Apple Planner (Violet)"])
            self.lang = self.settings.get("language", "ru")
            self.root.title(f"🍎 {L('app_title', self.lang)}")
            self._apply_window_bg()

            for w in self.root.winfo_children():
                w.destroy()

            self.root.update_idletasks()

            self.build_ui()
            self.refresh_week_view()
            self.refresh_tasks_list()
        except Exception:
            print("[!] Ошибка перерисовки UI:")
            traceback.print_exc()

    # ─── Полный диалог добавления ────────────────────────────
    def open_add_dialog(self):
        c = self.c
        win = tk.Toplevel(self.root)
        win.title(L("new_dialog_title", self.lang))
        win.geometry("560x640")
        win.configure(bg=c["bg"])
        win.transient(self.root); win.grab_set()
        win.resizable(False, False)

        win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 560) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 640) // 2
        win.geometry(f"+{x}+{y}")

        head = tk.Frame(win, bg=c["bg"])
        head.pack(fill="x", padx=28, pady=(24, 8))
        tk.Label(head, text=L("new_dialog_title", self.lang), bg=c["bg"], fg=c["text"],
                 font=self.font(5, "bold")).pack(anchor="w")

        card1 = RoundedFrame(win, bg=c["card"], radius=14, border=c["grid"],
                              border_width=1, height=92)
        card1.pack(fill="x", padx=28, pady=6)
        card1.pack_propagate(False)
        c1 = card1.inner
        c1.configure(bg=c["card"])

        tk.Label(c1, text=L("field_what", self.lang), bg=c["card"], fg=c["muted"],
                 font=self.font(-1, "bold")).pack(anchor="w", padx=18, pady=(14, 0))

        name_entry = tk.Entry(c1, bg=c["card2"], fg=c["text"],
                               insertbackground=c["text"], bd=0,
                               font=self.font(1), highlightthickness=1,
                               highlightbackground=c["grid"],
                               highlightcolor=c["accent"])
        name_entry.pack(fill="x", ipady=8, pady=(6, 14), padx=18)
        name_entry.focus_set()

        card2 = RoundedFrame(win, bg=c["card"], radius=14, border=c["grid"],
                              border_width=1, height=72)
        card2.pack(fill="x", padx=28, pady=6)
        card2.pack_propagate(False)
        c2 = card2.inner
        c2.configure(bg=c["card"])

        tk.Label(c2, text=L("field_repeat", self.lang), bg=c["card"], fg=c["muted"],
                 font=self.font(-1, "bold")).pack(anchor="w", padx=18, pady=(14, 0))

        type_var = tk.StringVar(value="weekly")
        trow = tk.Frame(c2, bg=c["card"])
        trow.pack(anchor="w", padx=18, pady=(8, 0))

        tk.Radiobutton(trow, text=L("field_every_week", self.lang),
                        variable=type_var, value="weekly",
                        bg=c["card"], fg=c["text"],
                        activebackground=c["card"], activeforeground=c["accent"],
                        selectcolor=c["accent_dk"], font=self.font(0),
                        cursor="hand2", highlightthickness=0, bd=0).pack(side="left")
        tk.Radiobutton(trow, text=L("field_once", self.lang),
                        variable=type_var, value="once",
                        bg=c["card"], fg=c["text"],
                        activebackground=c["card"], activeforeground=c["accent"],
                        selectcolor=c["accent_dk"], font=self.font(0),
                        cursor="hand2", highlightthickness=0, bd=0).pack(side="left", padx=(24, 0))

        card3 = RoundedFrame(win, bg=c["card"], radius=14, border=c["grid"],
                              border_width=1, height=230)
        card3.pack(fill="x", padx=28, pady=6)
        card3.pack_propagate(False)
        c3 = card3.inner
        c3.configure(bg=c["card"])

        day_title = tk.Label(c3, text=L("field_weekday", self.lang),
                              bg=c["card"], fg=c["muted"],
                              font=self.font(-1, "bold"))
        day_title.pack(anchor="w", padx=18, pady=(14, 6))

        switcher = tk.Frame(c3, bg=c["card"])
        switcher.pack(anchor="w", fill="x", padx=15)

        weekday_picker = WeekdayPicker(switcher, c, self.font, self.lang,
                                         initial=datetime.now().weekday())

        date_frame = tk.Frame(switcher, bg=c["card"])
        tk.Label(date_frame, text=L("field_date", self.lang), bg=c["card"],
                 fg=c["muted"], font=self.font(-1, "bold")).pack(anchor="w")
        date_entry = tk.Entry(date_frame, bg=c["card2"], fg=c["text"],
                               insertbackground=c["text"], bd=0,
                               font=self.font(1), highlightthickness=1,
                               highlightbackground=c["grid"],
                               highlightcolor=c["accent"])
        date_entry.pack(fill="x", ipady=8, pady=(6, 0))
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        tk.Label(c3, text=L("field_time", self.lang), bg=c["card"], fg=c["muted"],
                 font=self.font(-1, "bold")).pack(anchor="w", padx=18, pady=(14, 6))

        time_picker = TimePicker(c3, c, self.font, self.lang, initial="09:00")
        time_picker.pack(anchor="w", padx=18)

        def update_fields():
            try:
                if type_var.get() == "weekly":
                    day_title.config(text=L("field_weekday", self.lang))
                    date_frame.pack_forget()
                    weekday_picker.pack(anchor="w")
                else:
                    day_title.config(text=L("field_date", self.lang))
                    weekday_picker.pack_forget()
                    date_frame.pack(anchor="w", fill="x")
            except Exception:
                pass

        type_var.trace_add("write", lambda *_: update_fields())
        update_fields()

        btns = tk.Frame(win, bg=c["bg"])
        btns.pack(fill="x", padx=28, pady=(14, 22))

        def save():
            try:
                name = name_entry.get().strip()
                if not name:
                    messagebox.showwarning(L("notify_error", self.lang),
                                             L("warn_name", self.lang))
                    return

                time_str = time_picker.get()
                task = {
                    "id": int(time.time() * 1000),
                    "name": name,
                    "type": type_var.get(),
                    "done": False,
                    "skipped": False,
                    "notified": False,
                    "created": datetime.now().strftime("%Y-%m-%d %H:%M"),
                }

                if type_var.get() == "weekly":
                    idx = WEEKDAYS_FULL[self.lang].index(weekday_picker.get())
                    task["weekday"] = WEEKDAYS_FULL["ru"][idx]
                    task["time"] = time_str
                else:
                    try:
                        date_obj = datetime.strptime(date_entry.get().strip(), "%Y-%m-%d")
                    except ValueError:
                        messagebox.showwarning(L("notify_error", self.lang),
                                                 L("warn_date", self.lang))
                        return
                    try:
                        hh, mm = map(int, time_str.split(":"))
                    except ValueError:
                        messagebox.showwarning(L("notify_error", self.lang),
                                                 L("warn_time", self.lang))
                        return
                    dt = date_obj.replace(hour=hh, minute=mm)
                    task["datetime"] = dt.strftime("%Y-%m-%d %H:%M")

                self.tasks.append(task)
                self.save_tasks()
                self.refresh_week_view()
                self.refresh_tasks_list()
                win.destroy()
            except Exception:
                traceback.print_exc()

        RoundedButton(btns, text=L("btn_save", self.lang), icon="✓",
                      command=save, bg=c["accent_dk"], fg="#ffffff",
                      hover_bg=c["accent"], font=self.font(0, "bold"),
                      width=150, height=44, radius=12).pack(side="right")

        RoundedButton(btns, text=L("btn_cancel", self.lang), command=win.destroy,
                      bg=c["card"], fg=c["text"], hover_bg=c["card2"],
                      font=self.font(0), width=120, height=44,
                      radius=12).pack(side="right", padx=(0, 10))

        win.bind("<Return>", lambda e: save())
        win.bind("<Escape>", lambda e: win.destroy())

    # ─── Уведомления ─────────────────────────────────────────
    def show_notification(self, task):
        title = L("notify_title", self.lang)
        if task["type"] == "once":
            when = task["datetime"]
        else:
            try:
                idx = WEEKDAYS_FULL["ru"].index(task["weekday"])
                wd_local = WEEKDAYS_FULL[self.lang][idx]
            except (ValueError, KeyError):
                wd_local = task["weekday"]
            when = f"{wd_local}, {task['time']}"
        message = f"{task['name']}\n{when}"
        if HAS_PLYER:
            try:
                notification.notify(title=title, message=message,
                                     timeout=10, app_name="Apple Planner")
            except Exception:
                pass
        try:
            self.root.after(0, lambda: messagebox.showinfo(title, message))
        except Exception:
            pass

    def check_loop(self):
        while self.running:
            try:
                now = datetime.now()
                for task in list(self.tasks):
                    if task.get("done") or task.get("skipped") or task.get("notified"):
                        continue
                    trigger = False
                    if task["type"] == "once":
                        try:
                            dt = datetime.strptime(task["datetime"], "%Y-%m-%d %H:%M")
                        except ValueError:
                            continue
                        if 0 <= (now - dt).total_seconds() < 60:
                            trigger = True
                    elif task["type"] == "weekly":
                        if WEEKDAYS_FULL["ru"][now.weekday()] == task["weekday"]:
                            try:
                                h, m = map(int, task["time"].split(":"))
                            except ValueError:
                                continue
                            target = now.replace(hour=h, minute=m,
                                                  second=0, microsecond=0)
                            if 0 <= (now - target).total_seconds() < 60:
                                trigger = True
                    if trigger:
                        task["notified"] = True
                        self.save_tasks()
                        self.show_notification(task)
                        if task["type"] == "weekly":
                            self.root.after(120000,
                                            lambda tid=task["id"]: self.reset_notify(tid))
            except Exception as e:
                print("Ошибка проверки:", e)
            time.sleep(20)

    def reset_notify(self, task_id):
        for t in self.tasks:
            if t["id"] == task_id:
                t["notified"] = False
                self.save_tasks()
                break

    def auto_refresh(self):
        try:
            self.refresh_week_view()
        except Exception:
            pass
        self.root.after(60000, self.auto_refresh)


# ─── Запуск ──────────────────────────────────────────────────
def main():
    root = tk.Tk()
    app = TaskScheduler(root)

    def autosave():
        try:
            app.save_tasks()
        except Exception as e:
            print(f"[!] Автосейв: {e}")
        root.after(60000, autosave)

    root.after(60000, autosave)
    root.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception:
        print("=" * 60)
        print("ПРОИЗОШЛА ОШИБКА:")
        traceback.print_exc()
        print("=" * 60)
        try:
            input("Нажми Enter, чтобы закрыть...")
        except Exception:
            pass
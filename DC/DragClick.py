import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import ctypes
import json
import os

# Windows API
user32 = ctypes.windll.user32

# Константы для кликов мыши
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040

# Специальные флаги для клавиш-модификаторов
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

# Виртуальные коды клавиш
VK_CODES = {
    'A': 0x41, 'B': 0x42, 'C': 0x43, 'D': 0x44, 'E': 0x45, 'F': 0x46,
    'G': 0x47, 'H': 0x48, 'I': 0x49, 'J': 0x4A, 'K': 0x4B, 'L': 0x4C,
    'M': 0x4D, 'N': 0x4E, 'O': 0x4F, 'P': 0x50, 'Q': 0x51, 'R': 0x52,
    'S': 0x53, 'T': 0x54, 'U': 0x55, 'V': 0x56, 'W': 0x57, 'X': 0x58,
    'Y': 0x59, 'Z': 0x5A,
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
    '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
    'F1': 0x70, 'F2': 0x71, 'F3': 0x72, 'F4': 0x73, 'F5': 0x74,
    'F6': 0x75, 'F7': 0x76, 'F8': 0x77, 'F9': 0x78, 'F10': 0x79,
    'F11': 0x7A, 'F12': 0x7B,
    'SPACE': 0x20, 'ENTER': 0x0D, 'TAB': 0x09, 'ESC': 0x1B,
    'BACKSPACE': 0x08, 'DELETE': 0x2E, 'INSERT': 0x2D,
    'HOME': 0x24, 'END': 0x23, 'PGUP': 0x21, 'PGDN': 0x22,
    'UP': 0x26, 'DOWN': 0x28, 'LEFT': 0x25, 'RIGHT': 0x27,
    'WIN': 0x5B, 'MENU': 0x5D,
    # Модификаторы (с правильными кодами)
    'SHIFT': 0x10, 'CTRL': 0x11, 'ALT': 0x12,
}

# Скан-коды для модификаторов (нужны для корректной работы)
SCAN_CODES = {
    'SHIFT': 0x2A,   # Левый SHIFT
    'CTRL': 0x1D,    # Левый CTRL
    'ALT': 0x38,     # Левый ALT
}

# Для отображения
DISPLAY_NAMES = {
    'SPACE': 'ПРОБЕЛ', 'ENTER': 'ENTER', 'BACKSPACE': 'BACKSPACE',
    'DELETE': 'DELETE', 'TAB': 'TAB', 'ESC': 'ESC',
    'SHIFT': 'SHIFT', 'CTRL': 'CTRL', 'ALT': 'ALT',
    'UP': '↑ ВВЕРХ', 'DOWN': '↓ ВНИЗ', 'LEFT': '← ВЛЕВО', 'RIGHT': '→ ВПРАВО',
    'WIN': 'WIN', 'MENU': 'MENU',
}

class AutoKeyPresser:
    def __init__(self, root):
        self.root = root
        self.root.title("AUTO KEY PRESSER - 350 CPS MAX")
        self.root.geometry("700x850")
        self.root.resizable(False, False)
        
        self.config_file = "auto_key_presser_config.json"
        self.triggers = {}
        self.active_triggers = {}
        self.running = True
        self.last_press_time = {}
        
        self.locked = False
        self.floating_window = None
        
        # Статистика для CPS
        self.press_count = 0
        self.last_cps_time = 0
        
        self.load_config()
        self.create_widgets()
        self.start_keyboard_hook()
        self.start_cps_counter()
        
    def create_widgets(self):
        main = ttk.Frame(self.root, padding="10")
        main.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        title = ttk.Label(main, text="⚡ AUTO KEY PRESSER ⚡", 
                         font=("Arial", 18, "bold"))
        title.pack(pady=5)
        
        # CPS индикатор
        cps_frame = ttk.LabelFrame(main, text="ТЕКУЩАЯ СКОРОСТЬ НАЖАТИЙ", padding="10")
        cps_frame.pack(fill=tk.X, pady=5)
        
        self.cps_label = ttk.Label(cps_frame, text="0 CPS", 
                                   font=("Arial", 28, "bold"), foreground="red")
        self.cps_label.pack()
        
        # Глобальное управление
        control_frame = ttk.LabelFrame(main, text="🕹️ ГЛОБАЛЬНОЕ УПРАВЛЕНИЕ", padding="10")
        control_frame.pack(fill=tk.X, pady=5)
        
        btn_frame = ttk.Frame(control_frame)
        btn_frame.pack()
        
        self.enable_all_btn = ttk.Button(btn_frame, text="✅ ВКЛЮЧИТЬ ВСЁ", 
                                        command=self.enable_all, width=14)
        self.enable_all_btn.pack(side=tk.LEFT, padx=3)
        
        self.disable_all_btn = ttk.Button(btn_frame, text="❌ ВЫКЛЮЧИТЬ ВСЁ", 
                                         command=self.disable_all, width=14)
        self.disable_all_btn.pack(side=tk.LEFT, padx=3)
        
        self.lock_btn = ttk.Button(btn_frame, text="🔒 ЗАБЛОКИРОВАТЬ", 
                                  command=self.toggle_lock, width=14)
        self.lock_btn.pack(side=tk.LEFT, padx=3)
        
        self.float_btn = ttk.Button(btn_frame, text="📌 ПОКАЗАТЬ ОКНО", 
                                   command=self.toggle_floating_window, width=14)
        self.float_btn.pack(side=tk.LEFT, padx=3)
        
        self.lock_status = ttk.Label(control_frame, text="🔓 РАЗБЛОКИРОВАНО", 
                                     foreground="green", font=("Arial", 9))
        self.lock_status.pack(pady=5)
        
        # Настройка скорости
        speed_frame = ttk.LabelFrame(main, text="⚙️ НАСТРОЙКА СКОРОСТИ (нажатий в секунду)", padding="10")
        speed_frame.pack(fill=tk.X, pady=5)
        
        speed_row = ttk.Frame(speed_frame)
        speed_row.pack()
        
        ttk.Label(speed_row, text="Скорость:").pack(side=tk.LEFT, padx=5)
        self.speed_var = tk.StringVar(value="130")
        speed_spin = ttk.Spinbox(speed_row, from_=1, to=350, textvariable=self.speed_var, width=8)
        speed_spin.pack(side=tk.LEFT, padx=5)
        ttk.Label(speed_row, text="нажатий/сек (1-350)").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(speed_row, text="ПРИМЕНИТЬ ДЛЯ ВСЕХ", 
                  command=self.apply_speed_to_all).pack(side=tk.LEFT, padx=10)
        
        # Пресеты
        preset_frame = ttk.Frame(speed_frame)
        preset_frame.pack(pady=5)
        
        presets = [("100", 100), ("130", 130), ("150", 150), ("200", 200), ("250", 250), ("300", 300), ("350⚡", 350)]
        for text, val in presets:
            btn = ttk.Button(preset_frame, text=f"{text} CPS", width=8,
                           command=lambda v=val: self.set_global_speed(v))
            btn.pack(side=tk.LEFT, padx=2)
        
        # Добавление триггера
        add_frame = ttk.LabelFrame(main, text="➕ ДОБАВИТЬ НОВЫЙ ТРИГГЕР", padding="10")
        add_frame.pack(fill=tk.X, pady=5)
        
        # Триггер
        trigger_row = ttk.Frame(add_frame)
        trigger_row.pack(pady=5)
        
        ttk.Label(trigger_row, text="Нажимать клавишу:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.trigger_key_var = tk.StringVar()
        trigger_keys = [k for k in VK_CODES.keys()]
        trigger_display = [DISPLAY_NAMES.get(k, k) for k in trigger_keys]
        self.trigger_combo = ttk.Combobox(trigger_row, textvariable=self.trigger_key_var, 
                                          values=trigger_display, width=18)
        self.trigger_combo.pack(side=tk.LEFT, padx=5)
        self.trigger_combo.set('R')
        
        # Действие
        action_row = ttk.Frame(add_frame)
        action_row.pack(pady=5)
        
        ttk.Label(action_row, text="Будет нажимать:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.action_key_var = tk.StringVar()
        action_list = ['🖱️ ЛКМ (левая кнопка)', '🖱️ ПКМ (правая кнопка)', '🖱️ СКМ (средняя кнопка)']
        action_list += [DISPLAY_NAMES.get(k, k) for k in trigger_keys]
        self.action_combo = ttk.Combobox(action_row, textvariable=self.action_key_var, 
                                         values=action_list, width=22)
        self.action_combo.pack(side=tk.LEFT, padx=5)
        self.action_combo.set('🖱️ ЛКМ (левая кнопка)')
        
        # Режим
        mode_row = ttk.Frame(add_frame)
        mode_row.pack(pady=5)
        
        ttk.Label(mode_row, text="Режим:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.mode_var = tk.StringVar(value="toggle")
        ttk.Radiobutton(mode_row, text="Переключатель (вкл/выкл)", 
                       variable=self.mode_var, value="toggle").pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(mode_row, text="Удержание (пока зажата)", 
                       variable=self.mode_var, value="hold").pack(side=tk.LEFT, padx=5)
        
        # Скорость
        speed_row2 = ttk.Frame(add_frame)
        speed_row2.pack(pady=5)
        
        ttk.Label(speed_row2, text="Скорость (CPS):").pack(side=tk.LEFT)
        self.trigger_speed_var = tk.StringVar(value="")
        speed_spin2 = ttk.Spinbox(speed_row2, from_=1, to=350, textvariable=self.trigger_speed_var, width=6)
        speed_spin2.pack(side=tk.LEFT, padx=5)
        ttk.Label(speed_row2, text="(пусто = глобальная)").pack(side=tk.LEFT, padx=5)
        
        ttk.Button(add_frame, text="➕ ДОБАВИТЬ ТРИГГЕР", 
                  command=self.add_trigger, width=30).pack(pady=10)
        
        # Список триггеров
        list_frame = ttk.LabelFrame(main, text="📋 АКТИВНЫЕ ТРИГГЕРЫ", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.triggers_listbox = tk.Listbox(list_frame, height=8, font=("Courier", 9))
        self.triggers_listbox.pack(fill=tk.BOTH, expand=True, pady=5)
        
        scroll = ttk.Scrollbar(self.triggers_listbox, orient=tk.VERTICAL, 
                               command=self.triggers_listbox.yview)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.triggers_listbox.config(yscrollcommand=scroll.set)
        
        btn_list_frame = ttk.Frame(list_frame)
        btn_list_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_list_frame, text="🗑️ УДАЛИТЬ", 
                  command=self.remove_trigger).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_list_frame, text="✏️ РЕДАКТИРОВАТЬ", 
                  command=self.edit_trigger).pack(side=tk.LEFT, padx=5)
        
        # Статус
        self.status_label = ttk.Label(main, text="💤 ОЖИДАНИЕ", 
                                      font=("Arial", 11, "bold"),
                                      foreground="blue")
        self.status_label.pack(pady=10)
        
        info_text = """
        ⚡ МАКСИМАЛЬНАЯ СКОРОСТЬ: 350 НАЖАТИЙ В СЕКУНДУ! ⚡
        
        📖 ЧТО ЭТО:
        • Нажимаешь R → программа автоматически нажимает ЛКМ (до 350 раз в секунду!)
        • Нажимаешь F → автоматически нажимается SHIFT с бешеной скоростью
        • SHIFT, CTRL, ALT - ТЕПЕРЬ РАБОТАЮТ!
        • И так для ЛЮБЫХ клавиш!
        """
        
        info = ttk.Label(main, text=info_text, foreground="gray", 
                        justify=tk.LEFT, font=("Arial", 8))
        info.pack(pady=5)
        
        self.update_list_display()
        
    def set_global_speed(self, speed):
        self.speed_var.set(str(speed))
        self.apply_speed_to_all()
        
    def add_trigger(self):
        trigger_display = self.trigger_key_var.get()
        action_display = self.action_key_var.get()
        mode = self.mode_var.get()
        custom_speed = self.trigger_speed_var.get()
        
        trigger = self.display_to_code(trigger_display)
        action = self.display_to_action(action_display)
        
        if not trigger or not action:
            messagebox.showwarning("Ошибка", "Выберите корректные значения!")
            return
        
        if trigger in self.triggers:
            messagebox.showwarning("Ошибка", f"Триггер для {trigger_display} уже существует!")
            return
        
        if custom_speed and custom_speed.strip():
            try:
                speed = int(custom_speed)
                if not (1 <= speed <= 350):
                    raise ValueError
            except:
                messagebox.showwarning("Ошибка", "Скорость должна быть от 1 до 350")
                return
        else:
            speed = int(self.speed_var.get())
        
        self.triggers[trigger] = {
            'action': action,
            'mode': mode,
            'speed': speed,
            'display_trigger': trigger_display,
            'display_action': action_display
        }
        
        self.update_list_display()
        self.save_config()
        messagebox.showinfo("Успех", f"Добавлен: {trigger_display} → {action_display} ({speed} CPS)")
        
    def display_to_code(self, display_name):
        for code, name in DISPLAY_NAMES.items():
            if name == display_name:
                return code
        for code in VK_CODES.keys():
            if code == display_name or code == display_name.upper():
                return code.upper()
        return None
        
    def display_to_action(self, display_name):
        if 'ЛКМ' in display_name or 'левая' in display_name:
            return 'lmb'
        elif 'ПКМ' in display_name or 'правая' in display_name:
            return 'rmb'
        elif 'СКМ' in display_name or 'средняя' in display_name:
            return 'mmb'
        for code, name in DISPLAY_NAMES.items():
            if name == display_name:
                return code
        for code in VK_CODES.keys():
            if code == display_name or code == display_name.upper():
                return code.upper()
        return None
        
    def remove_trigger(self):
        selection = self.triggers_listbox.curselection()
        if selection:
            trigger = list(self.triggers.keys())[selection[0]]
            if trigger in self.active_triggers:
                self.active_triggers[trigger] = False
            del self.triggers[trigger]
            self.update_list_display()
            self.save_config()
            
    def edit_trigger(self):
        selection = self.triggers_listbox.curselection()
        if not selection:
            messagebox.showinfo("Инфо", "Сначала выберите триггер")
            return
            
        trigger = list(self.triggers.keys())[selection[0]]
        data = self.triggers[trigger]
        
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Редактирование")
        edit_window.geometry("400x280")
        edit_window.resizable(False, False)
        edit_window.attributes("-topmost", True)
        
        frame = ttk.Frame(edit_window, padding="15")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text=f"{data['display_trigger']} → {data['display_action']}",
                 font=("Arial", 10, "bold")).pack(pady=10)
        
        ttk.Label(frame, text="Режим:").pack(anchor=tk.W)
        mode_var = tk.StringVar(value=data['mode'])
        ttk.Radiobutton(frame, text="Переключатель (вкл/выкл)", 
                       variable=mode_var, value="toggle").pack(anchor=tk.W)
        ttk.Radiobutton(frame, text="Удержание (пока зажата)", 
                       variable=mode_var, value="hold").pack(anchor=tk.W)
        
        speed_frame = ttk.Frame(frame)
        speed_frame.pack(fill=tk.X, pady=10)
        ttk.Label(speed_frame, text="Скорость (CPS 1-350):").pack(side=tk.LEFT)
        speed_var = tk.StringVar(value=str(data['speed']))
        speed_spin = ttk.Spinbox(speed_frame, from_=1, to=350, textvariable=speed_var, width=8)
        speed_spin.pack(side=tk.LEFT, padx=5)
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=15)
        
        def save_changes():
            try:
                new_speed = int(speed_var.get())
                if not (1 <= new_speed <= 350):
                    raise ValueError
            except:
                messagebox.showwarning("Ошибка", "Скорость от 1 до 350")
                return
                
            self.triggers[trigger]['mode'] = mode_var.get()
            self.triggers[trigger]['speed'] = new_speed
            self.save_config()
            self.update_list_display()
            edit_window.destroy()
            messagebox.showinfo("Успех", "Изменения сохранены")
            
        ttk.Button(btn_frame, text="💾 СОХРАНИТЬ", command=save_changes).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="❌ ОТМЕНА", command=edit_window.destroy).pack(side=tk.LEFT, padx=5)
        
    def apply_speed_to_all(self):
        try:
            new_speed = int(self.speed_var.get())
            if not (1 <= new_speed <= 350):
                raise ValueError
        except:
            messagebox.showwarning("Ошибка", "Скорость от 1 до 350")
            return
            
        for trigger in self.triggers:
            self.triggers[trigger]['speed'] = new_speed
        self.save_config()
        self.update_list_display()
        messagebox.showinfo("Успех", f"Скорость всех триггеров: {new_speed} CPS")
        
    def update_list_display(self):
        self.triggers_listbox.delete(0, tk.END)
        for trigger, data in self.triggers.items():
            trigger_disp = data.get('display_trigger', trigger)
            action_disp = data.get('display_action', data['action'])
            mode = "🔄 Перекл" if data['mode'] == 'toggle' else "🔽 Удерж"
            speed = f"{data['speed']} CPS"
            
            if self.locked:
                status = "🔒 БЛОК"
            elif self.active_triggers.get(trigger, False):
                status = "✅ АКТИВЕН"
            else:
                status = "⭕ ОТКЛ"
                
            line = f"{trigger_disp:<16} → {action_disp:<18} | {mode:<8} | {speed:>8} | {status}"
            self.triggers_listbox.insert(tk.END, line)
            
    # ===== ЭМУЛЯЦИЯ НАЖАТИЙ (С ПОДДЕРЖКОЙ SHIFT/CTRL/ALT) =====
    def press_key_fast(self, key_code):
        """Максимально быстрое нажатие с поддержкой модификаторов"""
        try:
            if key_code == 'lmb':
                user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            elif key_code == 'rmb':
                user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
                user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            elif key_code == 'mmb':
                user32.mouse_event(MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
                user32.mouse_event(MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)
            else:
                vk_code = VK_CODES.get(key_code.upper())
                if vk_code:
                    # Для модификаторов используем специальный метод
                    if key_code.upper() in ['SHIFT', 'CTRL', 'ALT']:
                        self.press_modifier_key(vk_code, key_code.upper())
                    else:
                        # Обычная клавиша
                        user32.keybd_event(vk_code, 0, 0, 0)
                        user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)
        except Exception as e:
            pass
            
    def press_modifier_key(self, vk_code, key_name):
        """Специальный метод для клавиш-модификаторов"""
        try:
            # Получаем скан-код
            scan_code = SCAN_CODES.get(key_name, 0)
            
            # Нажатие
            user32.keybd_event(vk_code, scan_code, 0, 0)
            # Небольшая задержка для регистрации
            time.sleep(0.001)
            # Отпускание
            user32.keybd_event(vk_code, scan_code, KEYEVENTF_KEYUP, 0)
        except Exception as e:
            pass
            
    def press_key_down(self, key_code):
        """Нажать и удерживать клавишу"""
        try:
            if key_code == 'lmb':
                user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            elif key_code == 'rmb':
                user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            elif key_code == 'mmb':
                user32.mouse_event(MOUSEEVENTF_MIDDLEDOWN, 0, 0, 0, 0)
            else:
                vk_code = VK_CODES.get(key_code.upper())
                if vk_code:
                    if key_code.upper() in ['SHIFT', 'CTRL', 'ALT']:
                        scan_code = SCAN_CODES.get(key_code.upper(), 0)
                        user32.keybd_event(vk_code, scan_code, 0, 0)
                    else:
                        user32.keybd_event(vk_code, 0, 0, 0)
        except:
            pass
            
    def press_key_up(self, key_code):
        """Отпустить клавишу"""
        try:
            if key_code == 'lmb':
                user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            elif key_code == 'rmb':
                user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
            elif key_code == 'mmb':
                user32.mouse_event(MOUSEEVENTF_MIDDLEUP, 0, 0, 0, 0)
            else:
                vk_code = VK_CODES.get(key_code.upper())
                if vk_code:
                    if key_code.upper() in ['SHIFT', 'CTRL', 'ALT']:
                        scan_code = SCAN_CODES.get(key_code.upper(), 0)
                        user32.keybd_event(vk_code, scan_code, KEYEVENTF_KEYUP, 0)
                    else:
                        user32.keybd_event(vk_code, 0, KEYEVENTF_KEYUP, 0)
        except:
            pass
            
    # ===== ПЛАВАЮЩЕЕ ОКНО =====
    def toggle_floating_window(self):
        if self.floating_window and self.floating_window.winfo_exists():
            self.floating_window.destroy()
            self.floating_window = None
            self.float_btn.config(text="📌 ПОКАЗАТЬ ОКНО")
        else:
            self.create_floating_window()
            
    def create_floating_window(self):
        self.floating_window = tk.Toplevel(self.root)
        self.floating_window.title("Auto Key Presser")
        self.floating_window.geometry("280x380")
        self.floating_window.resizable(False, False)
        self.floating_window.attributes("-topmost", True)
        self.floating_window.attributes("-alpha", 0.92)
        self.floating_window.overrideredirect(True)
        
        title_bar = tk.Frame(self.floating_window, bg="#1a1a2e", height=35)
        title_bar.pack(fill=tk.X)
        title_bar.bind("<Button-1>", self.start_move)
        title_bar.bind("<B1-Motion>", self.on_move)
        
        title_label = tk.Label(title_bar, text="⚡ AUTO KEY PRESSER", bg="#1a1a2e", 
                              fg="white", font=("Arial", 10, "bold"))
        title_label.pack(side=tk.LEFT, padx=10)
        
        close_btn = tk.Button(title_bar, text="✖", command=self.close_floating_window,
                             bg="#1a1a2e", fg="white", bd=0, font=("Arial", 10, "bold"))
        close_btn.pack(side=tk.RIGHT, padx=10)
        
        content = tk.Frame(self.floating_window, bg="#16213e", padx=10, pady=10)
        content.pack(fill=tk.BOTH, expand=True)
        
        self.float_cps = tk.Label(content, text="0 CPS", bg="#16213e", fg="#00ff00", 
                                  font=("Arial", 16, "bold"))
        self.float_cps.pack(pady=5)
        
        tk.Frame(content, height=10, bg="#16213e").pack()
        
        enable_btn = tk.Button(content, text="▶ ВКЛЮЧИТЬ ВСЁ", 
                              bg="#0066cc", fg="white", font=("Arial", 10),
                              command=self.enable_all, relief=tk.FLAT)
        enable_btn.pack(fill=tk.X, pady=3, ipady=5)
        
        disable_btn = tk.Button(content, text="⏹ ВЫКЛЮЧИТЬ ВСЁ", 
                               bg="#cc3300", fg="white", font=("Arial", 10),
                               command=self.disable_all, relief=tk.FLAT)
        disable_btn.pack(fill=tk.X, pady=3, ipady=5)
        
        self.float_lock_btn = tk.Button(content, text="🔒 ЗАБЛОКИРОВАТЬ", 
                                       bg="#ffaa00", fg="black", font=("Arial", 10),
                                       command=self.toggle_lock, relief=tk.FLAT)
        self.float_lock_btn.pack(fill=tk.X, pady=3, ipady=5)
        
        tk.Frame(content, height=10, bg="#16213e").pack()
        
        panic_btn = tk.Button(content, text="🛑 СТОП ВСЁ 🛑", 
                             bg="#ff0000", fg="white", font=("Arial", 14, "bold"),
                             command=self.panic_stop_all, relief=tk.RAISED)
        panic_btn.pack(fill=tk.X, pady=10, ipady=10)
        
        screen_width = self.floating_window.winfo_screenwidth()
        self.floating_window.geometry(f"280x380+{screen_width-290}+50")
        
        self.float_btn.config(text="📌 СКРЫТЬ ОКНО")
        self.update_floating_status()
        
    def update_floating_status(self):
        def update():
            while self.running and self.floating_window and self.floating_window.winfo_exists():
                if self.floating_window and self.floating_window.winfo_exists():
                    self.float_lock_btn.config(text="🔓 РАЗБЛОКИРОВАТЬ" if self.locked else "🔒 ЗАБЛОКИРОВАТЬ")
                time.sleep(0.3)
        threading.Thread(target=update, daemon=True).start()
        
    def start_move(self, event):
        self.start_x = event.x
        self.start_y = event.y
        
    def on_move(self, event):
        x = self.floating_window.winfo_x() + event.x - self.start_x
        y = self.floating_window.winfo_y() + event.y - self.start_y
        self.floating_window.geometry(f"+{x}+{y}")
        
    def close_floating_window(self):
        if self.floating_window:
            self.floating_window.destroy()
            self.floating_window = None
            self.float_btn.config(text="📌 ПОКАЗАТЬ ОКНО")
            
    # ===== БЛОКИРОВКА =====
    def toggle_lock(self):
        self.locked = not self.locked
        if self.locked:
            self.lock_btn.config(text="🔓 РАЗБЛОКИРОВАТЬ")
            self.lock_status.config(text="🔒 ЗАБЛОКИРОВАНО", foreground="red")
            self.status_label.config(text="🔒 РЕЖИМ БЛОКИРОВКИ", foreground="orange")
            for key in self.active_triggers:
                self.active_triggers[key] = False
        else:
            self.lock_btn.config(text="🔒 ЗАБЛОКИРОВАТЬ")
            self.lock_status.config(text="🔓 РАЗБЛОКИРОВАНО", foreground="green")
            self.status_label.config(text="💤 ОЖИДАНИЕ", foreground="blue")
        self.update_list_display()
            
    # ===== ГЛОБАЛЬНОЕ УПРАВЛЕНИЕ =====
    def enable_all(self):
        if self.locked:
            messagebox.showwarning("Заблокировано", "Сначала разблокируйте!")
            return
        if not self.triggers:
            messagebox.showinfo("Инфо", "Нет добавленных триггеров")
            return
        for trigger in self.triggers:
            if not self.active_triggers.get(trigger, False):
                self.start_trigger(trigger)
        self.status_label.config(text="✅ ВСЕ ТРИГГЕРЫ ВКЛЮЧЕНЫ", foreground="green")
        self.update_list_display()
        
    def disable_all(self):
        for trigger in list(self.active_triggers.keys()):
            self.stop_trigger(trigger)
        self.status_label.config(text="❌ ВСЕ ТРИГГЕРЫ ВЫКЛЮЧЕНЫ", foreground="red")
        self.update_list_display()
        
    def panic_stop_all(self):
        for trigger in list(self.active_triggers.keys()):
            self.stop_trigger(trigger)
        self.status_label.config(text="🛑 АВАРИЙНАЯ ОСТАНОВКА", foreground="red")
        self.update_list_display()
        
    # ===== ОСНОВНАЯ ЛОГИКА =====
    def start_keyboard_hook(self):
        def hook():
            while self.running:
                if not self.locked:
                    for trigger, data in self.triggers.items():
                        if self.is_key_pressed(trigger):
                            self.handle_trigger(trigger, data)
                time.sleep(0.0005)
        threading.Thread(target=hook, daemon=True).start()
        
    def is_key_pressed(self, key):
        key_upper = key.upper()
        if key_upper in VK_CODES:
            code = VK_CODES[key_upper]
            return user32.GetAsyncKeyState(code) & 0x8000 != 0
        return False
        
    def handle_trigger(self, trigger, data):
        now = time.time()
        if trigger in self.last_press_time:
            if now - self.last_press_time[trigger] < 0.05:
                return
        self.last_press_time[trigger] = now
        
        if data['mode'] == 'toggle':
            if self.active_triggers.get(trigger, False):
                self.stop_trigger(trigger)
            else:
                self.start_trigger(trigger)
        else:
            self.start_hold_trigger(trigger, data)
            
    def start_trigger(self, trigger):
        if self.active_triggers.get(trigger, False):
            return
            
        data = self.triggers[trigger]
        self.active_triggers[trigger] = True
        display = data.get('display_trigger', trigger)
        self.status_label.config(text=f"🔥 {display} → {data['speed']} CPS", foreground="green")
        self.update_list_display()
        
        thread = threading.Thread(target=self.auto_press_loop, args=(trigger,), daemon=True)
        thread.start()
        
    def start_hold_trigger(self, trigger, data):
        if self.active_triggers.get(trigger, False):
            return
            
        self.active_triggers[trigger] = True
        display = data.get('display_trigger', trigger)
        self.status_label.config(text=f"🔽 {display} → УДЕРЖАНИЕ {data['speed']} CPS", foreground="orange")
        self.update_list_display()
        
        thread = threading.Thread(target=self.hold_press_loop, args=(trigger,), daemon=True)
        thread.start()
        
    def stop_trigger(self, trigger):
        if not self.active_triggers.get(trigger, False):
            return
            
        # Если это был режим удержания, отпускаем клавишу
        data = self.triggers.get(trigger)
        if data and data['mode'] == 'hold':
            self.press_key_up(data['action'])
            
        self.active_triggers[trigger] = False
        display = self.triggers[trigger].get('display_trigger', trigger)
        self.status_label.config(text=f"💤 {display} → ОСТАНОВЛЕН", foreground="blue")
        self.update_list_display()
        
    def auto_press_loop(self, trigger):
        data = self.triggers[trigger]
        action = data['action']
        speed = data['speed']
        delay = 1.0 / speed
        
        while self.running and self.active_triggers.get(trigger, False) and not self.locked:
            start = time.time()
            self.press_key_fast(action)
            self.press_count += 1
            elapsed = time.time() - start
            if delay > elapsed:
                time.sleep(delay - elapsed)
                
    def hold_press_loop(self, trigger):
        data = self.triggers[trigger]
        action = data['action']
        speed = data['speed']
        delay = 1.0 / speed
        
        # Сразу нажимаем и удерживаем клавишу
        self.press_key_down(action)
        
        while self.running and self.active_triggers.get(trigger, False) and not self.locked:
            if not self.is_key_pressed(trigger):
                break
            start = time.time()
            # Для модификаторов не нужно повторять нажатия, они уже зажаты
            if action not in ['lmb', 'rmb', 'mmb'] and action.upper() in ['SHIFT', 'CTRL', 'ALT']:
                # Модификаторы просто держим, не спамим
                time.sleep(delay)
            else:
                # Обычные клавиши повторяем
                self.press_key_fast(action)
                self.press_count += 1
            elapsed = time.time() - start
            if delay > elapsed:
                time.sleep(delay - elapsed)
                
        # Отпускаем клавишу
        self.press_key_up(action)
        self.active_triggers[trigger] = False
        self.update_list_display()
        
    def start_cps_counter(self):
        def update():
            last_time = time.time()
            last_count = 0
            while self.running:
                time.sleep(0.2)
                now = time.time()
                if now - last_time >= 1:
                    cps = int((self.press_count - last_count) / (now - last_time))
                    self.cps_label.config(text=f"{cps} CPS")
                    if self.floating_window and self.floating_window.winfo_exists():
                        self.float_cps.config(text=f"{cps} CPS")
                    
                    if cps >= 250:
                        self.cps_label.config(foreground="#ff00ff")
                    elif cps >= 200:
                        self.cps_label.config(foreground="#ff0000")
                    elif cps >= 130:
                        self.cps_label.config(foreground="#ffaa00")
                    else:
                        self.cps_label.config(foreground="#00ff00")
                    
                    last_count = self.press_count
                    last_time = now
        threading.Thread(target=update, daemon=True).start()
        
    def save_config(self):
        config = {
            'triggers': self.triggers,
            'global_speed': self.speed_var.get()
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, ensure_ascii=False)
        except:
            pass
            
    def load_config(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.triggers = config.get('triggers', {})
                    self.speed_var = tk.StringVar(value=config.get('global_speed', '130'))
            except:
                pass
                
    def on_closing(self):
        # Отпускаем все зажатые клавиши
        for trigger, data in self.triggers.items():
            if data['mode'] == 'hold' and self.active_triggers.get(trigger, False):
                self.press_key_up(data['action'])
                
        self.running = False
        for key in self.active_triggers:
            self.active_triggers[key] = False
        if self.floating_window:
            self.floating_window.destroy()
        self.save_config()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoKeyPresser(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
import tkinter as tk
from tkinter import ttk, colorchooser
import json

class SettingsDialog:
    def __init__(self, parent, current_settings, on_save_callback):
        self.parent = parent
        self.on_save = on_save_callback
        self.settings = current_settings.copy()
        
        self.window = tk.Toplevel(parent)
        self.window.title("Yazıcı - Gelişmiş Ayarlar")
        self.window.geometry("600x750")
        self.window.resizable(False, False)
        self.window.attributes("-topmost", True)
        
        # Colors
        self.bg_color = "#121212"
        self.card_color = "#1e1e1e"
        self.text_color = "#ffffff"
        self.accent_color = self.settings.get("color_theme", "#bb86fc")
        self.secondary_text = "#b0b0b0"
        
        self.window.configure(bg=self.bg_color)
        
        # Header
        header = tk.Frame(self.window, bg=self.accent_color, height=80)
        header.pack(fill='x', side='top')
        header.pack_propagate(False)
        
        tk.Label(header, text="⚙️ Uygulama Yapılandırması", fg='white', bg=self.accent_color, 
                 font=('Segoe UI', 16, 'bold')).pack(pady=(15, 0))
        tk.Label(header, text="Kullanıcı deneyiminizi buradan kişiselleştirin", fg='white', bg=self.accent_color, 
                 font=('Segoe UI', 9)).pack()

        # Footer
        footer = tk.Frame(self.window, bg=self.card_color, height=75)
        footer.pack(fill='x', side='bottom')
        footer.pack_propagate(False)
        
        tk.Button(footer, text="Vazgeç", command=self.window.destroy, bg='#424242', fg='white', 
                  relief='flat', padx=25, font=('Segoe UI', 10), cursor="hand2").pack(side='right', padx=20, pady=20)
        
        save_btn = tk.Button(footer, text="Ayarları Uygula", command=self.save, bg=self.accent_color, fg='white', 
                             relief='flat', padx=35, font=('Segoe UI', 10, 'bold'), cursor="hand2")
        save_btn.pack(side='right', pady=20)

        # MAIN CONTENT AREA
        self.main_scroll_container = tk.Frame(self.window, bg=self.bg_color)
        self.main_scroll_container.pack(fill='both', expand=True, padx=2, pady=2)

        # Better Canvas Setup for Scrolling - Explicitly sizing
        self.canvas = tk.Canvas(self.main_scroll_container, bg=self.bg_color, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.main_scroll_container, orient="vertical", command=self.canvas.yview)
        
        # This frame will hold all settings
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.bg_color)
        
        # Ensure the frame starts with some width to avoid initialization issues
        self.scrollable_frame.pack_propagate(True)
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        def _configure_window(event):
            # Ensure the frame stays as wide as the canvas minus padding
            width = event.width
            self.canvas.itemconfig(self.canvas_window, width=width)
            
        def _configure_scrollregion(event=None):
            # Force update of scrollregion based on actual frame size
            self.window.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

        self.canvas.bind('<Configure>', _configure_window)
        # Bind to both frame reconfiguration and window visibility
        self.scrollable_frame.bind('<Configure>', lambda e: _configure_scrollregion())

        # Support MouseWheel
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        self.canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self.vars = {}
        
        # Populate fields
        settings_to_add = [
            ("📱 Genel Görünüm", [
                ("program_name", "Uygulama Görünen Adı", "str", "Görev çubuğunda ve bildirimlerde görünecek isim."),
                ("color_theme", "Tema Rengi (Vurgu)", "color", "Uygulama pencereleri ve butonlar için ana renk."),
            ]),
            ("⌨️ Kontroller ve Kısayollar", [
                ("hotkey", "Metin İşlem Kısayolu", "str", "Karakter/AI tetikleyicisi (örn: ctrl+c)."),
                ("stt_hotkey", "Sesle Yazma Kısayolu", "str", "Sesle yazmayı başlatan kombinasyon."),
                ("cooldown", "Tıklama Hassasiyeti (sn)", "float", "Tıklama algılama gecikmesi."),
            ]),
            ("🗣️ Ses ve Menü", [
                ("stt_duration", "Ses Kayıt Süresi (sn)", "int", "Maksimum kayıt uzunluğu."),
                ("floating_menu_duration", "Menü Kapanma Süresi (sn)", "int", "Menünün ekranda kalma süresi."),
            ]),
            ("⚙️ Özellikler", [
                ("notify_on_no_change", "Değişiklik Olmazsa Bildir", "bool", "Düzeltme gerekmediğinde uyarı gösterir."),
                ("enable_character_fix", "Karakter Düzeltme Aktif", "bool", "Otomatik Karakter Onarma."),
                ("enable_ai_improve", "AI İyileştirme Aktif", "bool", "Yapay Zeka Metin Düzenleme."),
                ("enable_speech_to_text", "Sesle Yazma Aktif", "bool", "Ses girişini metne çevirme."),
            ])
        ]

        # Add items and force updates
        for section_title, fields in settings_to_add:
            self._add_section(section_title)
            for f_key, f_label, f_type, f_desc in fields:
                self._add_field(f_key, f_label, f_type, f_desc)

        # FINAL INITIALIZATION PUSH
        self.window.after(100, _configure_scrollregion)
        self.window.after(500, _configure_scrollregion) # Second pass to be sure

        # Center the window
        self._center_window()

    def _center_window(self):
        self.window.update() # Full update to get accurate winfo
        w = self.window.winfo_width()
        h = self.window.winfo_height()
        ws = self.window.winfo_screenwidth()
        hs = self.window.winfo_screenheight()
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        self.window.geometry('%dx%d+%d+%d' % (w, h, x, y))

    def _add_section(self, title):
        sf = tk.Frame(self.scrollable_frame, bg=self.bg_color)
        sf.pack(fill='x', padx=30, pady=(25, 10))
        
        label = tk.Label(sf, text=title, fg=self.accent_color, bg=self.bg_color, font=('Segoe UI', 13, 'bold'))
        label.pack(side='left')
        
        separator = tk.Frame(sf, height=2, bg="#333")
        separator.pack(side='left', fill='x', expand=True, padx=(20, 0))

    def _add_field(self, key, label, ftype, description=""):
        val = self.settings.get(key, "")
        
        container = tk.Frame(self.scrollable_frame, bg=self.card_color, pady=15, padx=20)
        container.pack(fill='x', padx=30, pady=8)
        
        # Subtle border to verify rendering
        container.configure(highlightbackground="#2c2c2c", highlightthickness=1)
        
        text_frame = tk.Frame(container, bg=self.card_color)
        text_frame.pack(side='left', fill='both', expand=True)
        
        tk.Label(text_frame, text=label, fg=self.text_color, bg=self.card_color, 
                 font=('Segoe UI', 11, 'bold')).pack(anchor='w')
        
        if description:
            tk.Label(text_frame, text=description, fg=self.secondary_text, bg=self.card_color, 
                     font=('Segoe UI', 9), wraplength=350, justify='left').pack(anchor='w', pady=(4, 0))
            
        control_frame = tk.Frame(container, bg=self.card_color)
        control_frame.pack(side='right', padx=(10, 0))

        if ftype == "bool":
            var = tk.BooleanVar(master=self.window, value=bool(val))
            self.vars[key] = var
            cb = tk.Checkbutton(control_frame, variable=var, bg=self.card_color, activebackground=self.card_color,
                               fg=self.text_color, activeforeground=self.text_color, selectcolor=self.accent_color, 
                               highlightthickness=0, bd=0)
            cb.pack()
        elif ftype == "color":
            color = str(val) if val else self.accent_color
            color_btn_frame = tk.Frame(control_frame, bg=self.card_color)
            color_btn_frame.pack()
            
            cp = tk.Frame(color_btn_frame, width=50, height=30, bg=color, cursor="hand2",
                          highlightbackground='white', highlightthickness=1)
            cp.pack(side='top')
            cp.pack_propagate(False)
            
            def _choose_color(e, k=key, p=cp):
                c = colorchooser.askcolor(initialcolor=self.settings.get(k), title="Tema Rengi Seç")[1]
                if c: 
                    self.settings[k] = c
                    p.configure(bg=c)
            cp.bind("<Button-1>", _choose_color)
            tk.Label(color_btn_frame, text="Değiştir", fg=self.secondary_text, bg=self.card_color, font=('Segoe UI', 8)).pack(pady=2)
        else:
            var = tk.StringVar(master=self.window, value=str(val))
            self.vars[key] = var
            
            entry_container = tk.Frame(control_frame, bg="#000", padx=1, pady=1)
            entry_container.pack()
            
            e = tk.Entry(entry_container, textvariable=var, font=('Consolas', 11) if key == "hotkey" else ('Segoe UI', 11), 
                         width=15, bg="#111", fg=self.text_color, insertbackground='white', 
                         relief='flat', bd=0)
            e.pack(padx=8, pady=5)

    def save(self):
        new_settings = self.settings.copy()
        for key, var in self.vars.items():
            try:
                val = var.get()
                if key in ["stt_duration", "floating_menu_duration"]: 
                    val = int(val)
                elif key == "cooldown": 
                    val = float(str(val).replace(',', '.'))
                new_settings[key] = val
            except: 
                pass
        self.on_save(new_settings)
        self.window.destroy()

def show_settings_window(parent, current_settings, on_save_callback):
    SettingsDialog(parent, current_settings, on_save_callback)

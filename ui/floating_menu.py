import tkinter as tk
from threading import Timer
import time

active_menu = None

class FloatingMenu:
    def __init__(self, x, y, callback, theme_color='#1a237e'):
        global active_menu
        if active_menu:
            active_menu.destroy()
            
        self.root = tk.Tk()
        self.root.withdraw()
        self.on_action = callback
        self.theme_color = theme_color
        self.clicked = False
        active_menu = self

        # Create menu window
        self.menu = tk.Toplevel(self.root)
        self.menu.overrideredirect(True)
        self.menu.attributes("-topmost", True)
        self.menu.attributes("-alpha", 0.0)
        self.menu.configure(bg='#2c3e50', highlightbackground=theme_color, highlightthickness=2)
        
        # Positioning
        self.menu.geometry(f"+{x}+{y + 20}")
        
        # Frame
        self.frame = tk.Frame(self.menu, bg='#2c3e50', padx=5, pady=5)
        self.frame.pack()
        
        # Geometry tracking (thread-safe for is_click_on_menu)
        self.geometry = {'x': x, 'y': y + 20, 'w': 100, 'h': 40} 
        self.menu.update_idletasks() # Force geometry calculation
        self._update_geometry_cache()
        self._create_button("🔠", "Karakter Düzelt", "fix", 0)
        self._create_button("🇹🇷", "Türkçe İyileştir", "improve_tr", 1)
        self._create_button("🪄", "Orijinal Dilde İyileştir", "improve_auto", 2)
        
        # Timers
        self.auto_close_timer = Timer(10.0, self.destroy)
        self.auto_close_timer.start()
        
        # Fade in
        self._fade_in()
        
        # Start loop
        self.root.mainloop()

    def _create_button(self, icon, tooltip, action_type, column):
        btn = tk.Button(
            self.frame, 
            text=icon, 
            bg='#2c3e50', 
            fg='white', 
            activebackground=self.theme_color,
            activeforeground='white',
            font=('Segoe UI Emoji', 14),
            relief='flat',
            padx=10,
            pady=5,
            command=lambda: self._handle_click(action_type)
        )
        btn.grid(row=0, column=column, padx=2)
        
        # Explicit click binding as fallback
        btn.bind("<Button-1>", lambda e: self._handle_click(action_type))
        
        # Explicit click binding to ensure it works even if 'command' is picky
        # Note: _handle_click handles the 'double call' protection
        
        # Hover effect with dynamic tooltip
        def on_enter(e):
            btn.configure(bg=self.theme_color)
            self._show_tooltip(tooltip, btn)
            
        def on_leave(e):
            btn.configure(bg='#2c3e50')
            self._hide_tooltip()

        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    def _show_tooltip(self, text, widget):
        self._hide_tooltip()
        self.tooltip_window = tw = tk.Toplevel(self.menu)
        tw.overrideredirect(True)
        tw.attributes("-topmost", True)
        
        # Position tooltip above button
        x = widget.winfo_rootx()
        y = widget.winfo_rooty() - 30
        tw.geometry(f"+{x}+{y}")
        
        label = tk.Label(tw, text=text, bg='#34495e', fg='white', 
                         font=('Segoe UI', 8), padx=5, pady=2,
                         highlightbackground='#7f8c8d', highlightthickness=1)
        label.pack()

    def _hide_tooltip(self):
        if hasattr(self, 'tooltip_window') and self.tooltip_window:
            try:
                self.tooltip_window.destroy()
            except:
                pass
            self.tooltip_window = None
        
    def _handle_click(self, action_type):
        if self.clicked: return
        self.clicked = True
        
        # Hide immediately for responsiveness
        try:
            self.menu.withdraw()
            self._hide_tooltip()
        except:
            pass
            
        # Run action in a small delay to let UI events settle
        def run_action():
            try:
                self.on_action(action_type)
            finally:
                self.destroy()
        
        # Start action in a separate thread so we can close this one fast
        import threading
        threading.Thread(target=run_action, daemon=True).start()

    def _fade_in(self):
        try:
            self._update_geometry_cache()
            alpha = self.menu.attributes("-alpha")
            if alpha < 0.95:
                self.menu.attributes("-alpha", alpha + 0.15)
                self.menu.after(20, self._fade_in)
        except:
            pass

    def _update_geometry_cache(self):
        try:
            self.geometry = {
                'x': self.menu.winfo_rootx(),
                'y': self.menu.winfo_rooty(),
                'w': self.menu.winfo_width(),
                'h': self.menu.winfo_height()
            }
        except:
            pass

    def destroy(self):
        global active_menu
        if active_menu == self:
            active_menu = None
            
        if hasattr(self, 'auto_close_timer') and self.auto_close_timer:
            self.auto_close_timer.cancel()
        try:
            self.root.after(1, self.root.destroy)
        except:
            pass

def close_active_menu():
    global active_menu
    if active_menu:
        active_menu.destroy()

def is_click_on_menu(x, y):
    global active_menu
    if not active_menu: return False
    try:
        # Use cached geometry to avoid cross-thread Tkinter calls
        geo = active_menu.geometry
        padding = 15
        return (geo['x'] - padding) <= x <= (geo['x'] + geo['w'] + padding) and \
               (geo['y'] - padding) <= y <= (geo['y'] + geo['h'] + padding)
    except:
        return False

def show_floating_menu(x, y, callback, theme_color='#1a237e'):
    import threading
    threading.Thread(target=lambda: FloatingMenu(x, y, callback, theme_color), daemon=True).start()

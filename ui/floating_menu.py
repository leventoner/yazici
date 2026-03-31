import tkinter as tk
import threading
from threading import Timer, Thread, Lock
import time
import queue

active_menu = None
main_root = None
ui_thread = None
ui_queue = queue.Queue()

ui_thread_lock = Lock()
ui_ready_event = threading.Event()

def _ensure_ui_running():
    global ui_thread, main_root
    if ui_thread is None or not ui_thread.is_alive():
        with ui_thread_lock:
            if ui_thread is None or not ui_thread.is_alive():
                ui_ready_event.clear()
                ui_thread = Thread(target=_run_tk_loop, daemon=True)
                ui_thread.start()
                ui_ready_event.wait()

def _run_tk_loop():
    global main_root
    main_root = tk.Tk()
    main_root.withdraw()
    
    # Process the queue using root.after
    def process_queue():
        try:
            while True:
                task = ui_queue.get_nowait()
                task()
        except queue.Empty:
            pass
        main_root.after(100, process_queue)
    
    main_root.after(100, process_queue)
    ui_ready_event.set()
    main_root.mainloop()

class FloatingMenu:
    def __init__(self, x, y, callback, theme_color='#1a237e', duration=10.0):
        global active_menu, main_root
        
        # Always run on main thread
        self.on_action = callback
        self.theme_color = theme_color
        self.clicked = False
        
        # Create menu window
        self.menu = tk.Toplevel(main_root)
        self.menu.overrideredirect(True)
        self.menu.attributes("-topmost", True)
        self.menu.attributes("-alpha", 0.0)
        self.menu.configure(bg='#2c3e50', highlightbackground=theme_color, highlightthickness=2)
        
        # Positioning
        self.menu.geometry(f"+{x}+{y + 20}")
        
        # Frame
        self.frame = tk.Frame(self.menu, bg='#2c3e50', padx=5, pady=5)
        self.frame.pack()
        
        # Geometry tracking
        self.geometry = {'x': x, 'y': y + 20, 'w': 100, 'h': 40} 
        self.menu.update_idletasks() # Force geometry calculation
        self._update_geometry_cache()
        
        self._create_button("🔠", "Karakter Düzelt", "fix", 0)
        self._create_button("🇹🇷", "Türkçe İyileştir", "improve_tr", 1)
        self._create_button("🪄", "Orijinal Dilde İyileştir", "improve_auto", 2)
        
        # Timers
        self.auto_close_timer = Timer(float(duration), self._check_auto_close)
        self.auto_close_timer.start()
        
        # Fade in
        self._fade_in()

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
        
        # Hover effect
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
        
        try:
            self._hide_tooltip()
            self.menu.withdraw()
        except:
            pass
            
        def run_action():
            try:
                self.on_action(action_type)
            finally:
                close_active_menu()
        
        Thread(target=run_action, daemon=True).start()

    def _fade_in(self):
        try:
            self._update_geometry_cache()
            alpha = float(self.menu.attributes("-alpha"))
            if alpha < 0.95:
                self.menu.attributes("-alpha", alpha + 0.15)
                self.menu.after(20, self._fade_in)
        except:
            pass

    def _check_auto_close(self):
        """Checks if the mouse is over the menu before closing. If over, delays closing."""
        if not main_root or not self.menu:
            return

        def _perform_check():
            try:
                # Refresh geometry to get latest positions
                self._update_geometry_cache()
                
                # Get current mouse position
                x = self.menu.winfo_pointerx()
                y = self.menu.winfo_pointery()
                
                if is_click_on_menu(x, y):
                    # Mouse is over, wait another 2 seconds and check again
                    self.auto_close_timer = Timer(2.0, self._check_auto_close)
                    self.auto_close_timer.start()
                else:
                    # Mouse is not over, close the menu
                    close_active_menu()
            except Exception:
                # Fallback to closing if anything goes wrong
                close_active_menu()

        # Execute check on the main UI thread
        main_root.after(10, _perform_check)

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
        if hasattr(self, 'auto_close_timer') and self.auto_close_timer:
            self.auto_close_timer.cancel()
        try:
            self.menu.destroy()
        except:
            pass

class NotificationOverlay:
    def __init__(self, title, message, color='#3498db'):
        global main_root
        self.title = title
        self.message = message
        self.color = color
        
        self.overlay = tk.Toplevel(main_root)
        self.overlay.overrideredirect(True)
        self.overlay.attributes("-topmost", True)
        self.overlay.attributes("-alpha", 0.0)
        self.overlay.configure(bg='#2c3e50', highlightbackground=self.color, highlightthickness=2)
        
        frame = tk.Frame(self.overlay, bg='#2c3e50', padx=15, pady=10)
        frame.pack()

        tk.Label(frame, text=self.title, fg=self.color, bg='#2c3e50', font=('Segoe UI', 10, 'bold')).pack(anchor='w')

        display_msg = self.message
        if len(display_msg) > 120:
            display_msg = display_msg[:117] + "..."
            
        tk.Label(frame, text=display_msg, fg='white', bg='#2c3e50', font=('Segoe UI', 9), wraplength=400, justify='left').pack(anchor='w', pady=(2, 0))

        self.overlay.update_idletasks()
        width = self.overlay.winfo_width()
        height = self.overlay.winfo_height()
        screen_width = self.overlay.winfo_screenwidth()
        screen_height = self.overlay.winfo_screenheight()
        
        x = screen_width - width - 20
        y = screen_height - height - 60
        self.overlay.geometry(f"+{x}+{y}")

        self._fade_in()
        self.overlay.after(4000, self.overlay.destroy)

    def _fade_in(self):
        try:
            alpha = float(self.overlay.attributes("-alpha"))
            if alpha < 0.95:
                self.overlay.attributes("-alpha", alpha + 0.1)
                self.overlay.after(30, self._fade_in)
        except:
            pass

def close_active_menu():
    global active_menu
    if active_menu:
        menu = active_menu
        active_menu = None
        main_root.after(1, menu.destroy)

def is_click_on_menu(x, y):
    global active_menu
    if not active_menu: return False
    try:
        geo = active_menu.geometry
        padding = 15
        return (geo['x'] - padding) <= x <= (geo['x'] + geo['w'] + padding) and \
               (geo['y'] - padding) <= y <= (geo['y'] + geo['h'] + padding)
    except:
        return False

def is_menu_active():
    global active_menu
    return active_menu is not None

def show_floating_menu(x, y, callback, theme_color='#1a237e', duration=10.0):
    global active_menu
    _ensure_ui_running()
    
    def _create_menu():
        global active_menu
        if active_menu:
            active_menu.destroy()
        active_menu = FloatingMenu(x, y, callback, theme_color, duration)
        
    main_root.after(1, _create_menu)

def show_notification(title, message, color='#3498db'):
    close_active_menu()
    _ensure_ui_running()
    main_root.after(1, lambda: NotificationOverlay(title, message, color))

def get_main_root():
    _ensure_ui_running()
    return main_root

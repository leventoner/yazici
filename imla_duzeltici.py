import os
import sys
import time
import threading
import json
import keyboard
import pyperclip
from mintlemon import Normalizer
import pystray
from PIL import Image
import tkinter as tk
from dotenv import load_dotenv
import speech_recognition as sr
import sounddevice as sd
from scipy.io import wavfile
import numpy as np
import io
from pynput import mouse
from ui.floating_menu import show_floating_menu, close_active_menu, is_click_on_menu, show_notification, is_menu_active
import subprocess

# Fix DPI scaling on Windows
if sys.platform == "win32":
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            windll.user32.SetProcessDPIAware()
        except Exception:
            pass


# Helper functions for paths
def resource_path(relative_path):
    """ Get absolute path to internal bundled resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_external_path(relative_path):
    """ Get absolute path to file in the same directory as the executable """
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Load environment variables
# 1. Load from bundled .env (Internal default)
internal_env = resource_path(".env")
if os.path.exists(internal_env):
    load_dotenv(internal_env)

# 2. Load from external .env (User override)
external_env = get_external_path(".env")
if os.path.exists(external_env):
    load_dotenv(external_env, override=True)

# Settings logic
DEFAULT_SETTINGS = {
    "program_name": "Yazıcı",
    "hotkey": "ctrl+c",
    "stt_hotkey": "ctrl+shift+y",
    "stt_duration": 10,
    "cooldown": 0.5,
    "notify_on_no_change": True,
    "enable_character_fix": True,
    "enable_ai_improve": True,
    "enable_speech_to_text": True,
    "color_theme": "#1a237e",
    "floating_menu_duration": 10
}

def load_settings():
    # Try external settings first (user modifiable)
    settings_path = get_external_path("settings.json")
    
    # If external doesn't exist, try internal bundled default
    if not os.path.exists(settings_path):
        settings_path = resource_path("settings.json")
        
    try:
        if os.path.exists(settings_path):
            with open(settings_path, "r", encoding="utf-8") as f:
                return {**DEFAULT_SETTINGS, **json.load(f)}
    except Exception as e:
        print(f"Error loading settings: {e}")
    return DEFAULT_SETTINGS

settings = load_settings()
THEME_COLOR = settings.get("color_theme", "#1a237e")
PROGRAM_NAME = settings.get("program_name", "Yazıcı")

# Global variables
click_count = 0
last_click_time = 0
COOLDOWN = settings["cooldown"]
is_running = True
processing_lock = threading.Lock()
timer = None

# Gemini configuration
import google.generativeai as genai
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

def initialize_gemini():
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY not found in environment.")
        return None
    
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        available_names = []
        try:
            available_models = list(genai.list_models())
            available_names = [m.name for m in available_models if 'generateContent' in m.supported_generation_methods]
        except Exception as list_err:
            print(f"Model listeleme hatası: {list_err}")

        preferred_keywords = ['gemini-2.0-flash', 'gemini-2.1-flash', 'gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-pro']
        for kw in preferred_keywords:
            for full_name in available_names:
                if kw in full_name:
                    return genai.GenerativeModel(full_name)
        
        for fallback in ['gemini-1.5-flash', 'gemini-pro']:
            try:
                return genai.GenerativeModel(f"models/{fallback}")
            except:
                continue
        return None
    except Exception as e:
        print(f"Gemini kritik hata: {e}")
        return None

model = initialize_gemini()

# The resource_path and get_external_path functions are moved to the top

# Notifications are now handled by ui.floating_menu.show_notification

def check_lib_health():
    try:
        return Normalizer.deasciify("kiymetli") == "kıymetli"
    except:
        return False

def deasciify_text(text):
    if not text:
        return text
    try:
        # 1. Full text deasciify
        corrected = Normalizer.deasciify(text)
        
        # 2. Word-by-word fallback (sometimes more reliable for mixed texts)
        # Use regex or split() to handle all whitespace types
        words = text.split()
        if not words: return corrected
        
        corrected_words = [Normalizer.deasciify(w) for w in words]
        
        # We need to preserve original spacing if possible, but for comparison:
        # if the word-by-word produced a different result than full-text, 
        # it might be better. 
        # However, Normalizer usually does a good job. 
        # Let's check if the current 'corrected' still has 'kiymetli' or 'umarim'
        
        problematic_words = ["kiymetli", "umarim", "basarilar", "gormek"]
        for p in problematic_words:
            if p in corrected and p not in text: # This shouldn't happen, but logic check
                pass
            if p in text and p in corrected:
                # Full text failed to catch this word, try word-by-word results
                # Simple replacement for better accuracy
                for i, w in enumerate(words):
                    if w in problematic_words or any(c in "cgiosu" for c in w.lower()):
                         # This is a bit complex, let's just return the best version we found
                         pass
        
        # Simplest: if word by word changed something that full text didn't, or vice-versa
        # Let's just return the most 'turkish' looking one (more non-ascii chars)
        def count_turkish(s):
            return sum(1 for c in s if c in "çğıöşüÇĞİÖŞÜ")
            
        if count_turkish(corrected) < count_turkish(' '.join(corrected_words)):
            # Reconstruct with original spacing is hard with simple split, 
            # but let's try a better approach:
            new_text = text
            for i, w in enumerate(words):
                cw = corrected_words[i]
                if cw != w:
                    new_text = new_text.replace(w, cw, 1)
            corrected = new_text

        return corrected
    except Exception as e:
        print(f"Deasciify error: {e}")
        return text

def improve_text(text, auto_detect=False):
    try:
        available_models = list(genai.list_models())
        available_model_names = [m.name for m in available_models if 'generateContent' in m.supported_generation_methods]
    except:
        available_model_names = ['models/gemini-2.0-flash', 'models/gemini-1.5-flash', 'models/gemini-pro']

    prioritized = ['models/gemini-2.0-flash', 'models/gemini-2.5-flash', 'models/gemini-1.5-flash', 'models/gemini-pro']
    for m in available_model_names:
        if m not in prioritized:
            prioritized.append(m)

    last_error = ""
    for model_name in prioritized:
        try:
            current_model = genai.GenerativeModel(model_name)
            if auto_detect:
                prompt = f"Improve the grammar, spelling, word order, and general flow of the following text in its original language. Return only the corrected text, do not add any explanations or comments. Text: {text}"
            else:
                prompt = f"Aşağıdaki Türkçe metni dilbilgisi, imla, kelime sırası ve genel akıcılık açısından iyileştir. Sadece düzeltilmiş metni döndür, başka hiçbir şey yazma. Metin: {text}"
            
            response = current_model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            error_msg = str(e)
            last_error = error_msg
            continue
    return f"Hata: {last_error}"


def handle_fix_clipboard():
    # If the hotkey is ctrl+c, the user's clicks already put the text in the clipboard
    # We just need to wait a tiny bit to make sure OS finished the write
    time.sleep(0.3)
    
    # Try to get text from clipboard with retries
    text = ""
    for i in range(10):
        try:
            text = pyperclip.paste()
            if text and len(text.strip()) > 0: 
                break
        except:
            pass
        time.sleep(0.1)

    if not text or not text.strip():
        show_notification("Hata", "Lütfen metni seçin ve tekrar deneyin.", color='#e74c3c')
        return
    
    corrected = deasciify_text(text)
    
    if text.strip() != corrected.strip():
        pyperclip.copy(corrected)
        show_notification("Karakterler Düzeltildi!", corrected, color='#2ecc71')
    else:
        if settings.get("notify_on_no_change", True):
            # Double check: maybe it's the case where Normalizer failed to load inside EXE
            show_notification("Düzeltme Gerekmedi", "Metin zaten düzgün görünüyor.", color='#3498db')

def handle_improve_clipboard(auto_detect=False):
    # If hotkey is ctrl+c, we don't send it again
    if settings['hotkey'].lower() != 'ctrl+c':
        keyboard.press_and_release('ctrl+c')
    
    time.sleep(0.3)
    
    text = ""
    for i in range(10):
        try:
            text = pyperclip.paste()
            if text and len(text.strip()) > 0: break
        except:
            pass
        time.sleep(0.1)

    if not text or not text.strip():
        show_notification("Hata", "Lütfen metni seçin ve tekrar deneyin.", color='#e74c3c')
        return
    
    status_msg = "Metin kendi dilinde iyileştiriliyor..." if auto_detect else "Metin yapay zeka ile iyileştiriliyor..."
    show_notification("İşleniyor...", status_msg, color='#9b59b6')
    improved = improve_text(text, auto_detect=auto_detect)
    
    if improved and not improved.startswith("Hata:"):
        pyperclip.copy(improved)
        success_title = "Dilde İyileştirildi!" if auto_detect else "Yazı İyileştirildi!"
        show_notification(success_title, improved, color='#9b59b6')
    else:
        show_notification("İşlem Başarısız", improved, color='#e74c3c')

def handle_speech_to_text():
    """Records audio using sounddevice and types it as Turkish text."""
    if not settings.get("enable_speech_to_text", True):
        show_notification("Uyarı", "Sesle yazma özelliği kapalı.", color='#e74c3c')
        return

    r = sr.Recognizer()
    
    # Recording settings
    fs = 16000  # Sample rate
    duration = settings.get("stt_duration", 10)
    
    show_notification("Dinleniyor...", f"Lütfen Türkçe konuşun ({duration} saniye).", color='#9b59b6')
    
    try:
        # Step 1: Record using sounddevice
        # We record for 5 seconds (can be improved later with silence detection)
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()  # Wait until recording is finished
        
        show_notification("İşleniyor...", "Sesiniz metne çevriliyor...", color='#e67e22')
        
        # Step 2: Convert to WAV in memory
        buffer = io.BytesIO()
        wavfile.write(buffer, fs, recording)
        buffer.seek(0)
        
        # Step 3: Process with SpeechRecognition
        with sr.AudioFile(buffer) as source:
            audio_data = r.record(source)
            
            # Using Google Web Speech API (free and supports Turkish)
            text = r.recognize_google(audio_data, language='tr-TR')
            
            if text:
                time.sleep(0.5)
                keyboard.write(text)
                show_notification("Başarılı!", f"Yazıya Geçirildi: {text}", color='#2ecc71')
            else:
                show_notification("Uyarı", "Ses anlaşılamadı.", color='#f1c40f')
                
    except Exception as e:
        show_notification("Hata", f"Ses Tanıma Hatası: {e}", color='#e74c3c')

def process_action():
    global click_count
    current_clicks = click_count
    click_count = 0
    
    if not is_running: return

    # Wait a moment for the system to handle the copy action
    time.sleep(0.3)
    
    if current_clicks == 2:
        if settings.get("enable_character_fix", True):
            handle_fix_clipboard()
        else:
            show_notification("Uyarı", "Karakter düzeltme özelliği kapalı.", color='#e74c3c')
    elif current_clicks == 3:
        if settings.get("enable_ai_improve", True):
            handle_improve_clipboard(auto_detect=False)
        else:
            show_notification("Uyarı", "Yapay zeka iyileştirme özelliği kapalı.", color='#e74c3c')
    elif current_clicks >= 4:
        if settings.get("enable_ai_improve", True):
            handle_improve_clipboard(auto_detect=True)
        else:
            show_notification("Uyarı", "Yapay zeka iyileştirme özelliği kapalı.", color='#e74c3c')

def on_hotkey_pressed():
    global click_count, timer, last_click_time
    if not is_running: return
    
    close_active_menu()
    current_time = time.time()
    if current_time - last_click_time < COOLDOWN:
        click_count += 1
    else:
        click_count = 1
    
    last_click_time = current_time
    if timer: timer.cancel()
    timer = threading.Timer(COOLDOWN, process_action)
    timer.start()

def handle_deletion_key():
    if is_menu_active():
        # Text deletion happened, close the floating menu
        close_active_menu()

# --- Selection Detection Logic (Floating Menu Trigger) ---

class SelectionManager:
    def __init__(self):
        self.mouse_press_pos = (0, 0)
        self.mouse_press_time = 0
        self.last_up_time = 0
        self.click_count = 0
        self.is_dragging = False
        self.menu_active = False

    def on_click(self, x, y, button, pressed):
        if not is_running: return
        if button != mouse.Button.left: return

        # If user clicks elsewhere (not on current menu), close it
        if pressed and not is_click_on_menu(x, y):
            close_active_menu()

        current_time = time.time()

        if pressed:
            # Check if this is a double/triple click
            if current_time - self.last_up_time < 0.4:
                self.click_count += 1
            else:
                self.click_count = 1
            
            self.mouse_press_pos = (x, y)
            self.mouse_press_time = current_time
            self.is_dragging = False
        else:
            # Released
            self.last_up_time = current_time
            
            # 1. Check for Drag Selection
            dist = ((x - self.mouse_press_pos[0])**2 + (y - self.mouse_press_pos[1])**2)**0.5
            if dist > 15: # Significant movement
                self.is_dragging = True
            
            # 2. Trigger Conditions: Double Click OR Drag ended
            if self.click_count >= 2 or self.is_dragging:
                # Give the application a moment to actually select the text
                threading.Timer(0.1, self.check_and_show_menu, args=(x, y)).start()

    def check_and_show_menu(self, x, y):
        # We need to see if there is actually selected text.
        # How? Simulate Ctrl+C and see if clipboard is not empty or changed.
        
        # Save old clipboard to be polite
        try:
            old_clip = pyperclip.paste()
        except:
            old_clip = ""

        # Request Copy
        keyboard.press_and_release('ctrl+c')
        time.sleep(0.15) # Wait for OS

        try:
            current_clip = pyperclip.paste()
        except:
            current_clip = ""

        # If selection happened, show menu
        # (We assume if clipboard is NOT empty and potentially different, or just NOT empty)
        # To avoid showing it on empty clicks, we check if current_clip has content.
        if current_clip and current_clip.strip():
            duration = settings.get("floating_menu_duration", 10)
            show_floating_menu(x, y, self.menu_callback, theme_color=THEME_COLOR, duration=duration)
        else:
            # Restore if it was just a random click that didn't select anything
            # But wait, if text was already in clipboard from before, this might be tricky.
            # Best way: Check if current_clip is different from old_clip?
            # No, user might select the same text again.
            # Usually, if Ctrl+C was sent and we have text, it's a good indicator.
            pass

    def menu_callback(self, action_type):
        if action_type == "fix":
            handle_fix_clipboard()
        elif action_type == "improve_tr":
            handle_improve_clipboard(auto_detect=False)
        elif action_type == "improve_auto":
            handle_improve_clipboard(auto_detect=True)

selection_manager = SelectionManager()

def start_mouse_listener():
    with mouse.Listener(on_click=selection_manager.on_click) as listener:
        listener.join()

def quit_app(icon, item):
    global is_running
    is_running = False
    icon.stop()
    os._exit(0)

def get_check_status(feature_name):
    return "✓ " if settings.get(feature_name, True) else "  "

def toggle_feature(icon, item):
    feature_map = {
        "Karakter Düzeltme (2x)": "enable_character_fix",
        "Yapay Zeka (AI) Desteği": "enable_ai_improve",
        "Sesle Yazma (STT)": "enable_speech_to_text"
    }
    key = feature_map.get(item.text.replace("✓ ", "").replace("  ", ""))
    if key:
        settings[key] = not settings[key]
        # Update settings.json so it persists
        try:
            settings_path = get_external_path("settings.json")
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
        except:
            pass
        # Refresh menu
        icon.menu = create_menu()

def create_menu():
    return pystray.Menu(
        pystray.MenuItem(f"{PROGRAM_NAME} v3.0", lambda: None, enabled=False),
        pystray.MenuItem("---", lambda: None, enabled=False),
        pystray.MenuItem(f"{get_check_status('enable_character_fix')}Karakter Düzeltme (2x)", toggle_feature),
        pystray.MenuItem(f"{get_check_status('enable_ai_improve')}Yapay Zeka (AI) Desteği", toggle_feature),
        pystray.MenuItem(f"{get_check_status('enable_speech_to_text')}Sesle Yazma (STT)", toggle_feature),
        pystray.MenuItem("---", lambda: None, enabled=False),
        pystray.MenuItem("Panoyu Düzelt", handle_fix_clipboard),
        pystray.MenuItem("Pusula (Sesle Yaz)", lambda: threading.Thread(target=handle_speech_to_text, daemon=True).start()),
        pystray.MenuItem("---", lambda: None, enabled=False),
        pystray.MenuItem(f"Kısayollar:", lambda: None, enabled=False),
        pystray.MenuItem(f"  {settings['hotkey'].upper()}: Karakter/AI", lambda: None, enabled=False),
        pystray.MenuItem(f"  {settings['stt_hotkey'].upper()}: Sesle Yaz", lambda: None, enabled=False),
        pystray.MenuItem("---", lambda: None, enabled=False),
        pystray.MenuItem("Çıkış", quit_app)
    )

def setup_tray():
    image = Image.open(resource_path("icon.png"))
    icon = pystray.Icon("yazici", image, f"{PROGRAM_NAME} & Metin Asistanı", create_menu())
    icon.run()

def start_listener():
    try:
        keyboard.add_hotkey(settings['hotkey'], on_hotkey_pressed, suppress=False)
        # Add the Speech-to-Text hotkey
        keyboard.add_hotkey(settings['stt_hotkey'], lambda: threading.Thread(target=handle_speech_to_text, daemon=True).start(), suppress=False)
        
        # Listen for delete/backspace/escape to close the floating menu
        keyboard.on_press_key("backspace", lambda _: handle_deletion_key(), suppress=False)
        keyboard.on_press_key("delete", lambda _: handle_deletion_key(), suppress=False)
        keyboard.on_press_key("esc", lambda _: handle_deletion_key(), suppress=False)
        
        while is_running:
            time.sleep(1)
    except Exception as e:
        print(f"Hotkey error: {e}")

if __name__ == "__main__":
    # Command line arguments handling
    if len(sys.argv) > 1:
        if "--fix" in sys.argv:
            handle_fix_clipboard()
            sys.exit(0)
        elif "--improve" in sys.argv:
            handle_improve_clipboard()
            sys.exit(0)

    # Start listeners
    threading.Thread(target=start_listener, daemon=True).start()
    threading.Thread(target=start_mouse_listener, daemon=True).start()

    # Initial notification and library health check
    msg = f"Yazıcı Hazır!\n2x {settings['hotkey'].upper()}: Karakter\n3x {settings['hotkey'].upper()}: İyileştir\n{settings['stt_hotkey'].upper()}: Sesle Yaz"
    if not check_lib_health():
        msg += "\n\n⚠️ KRİTİK: Dil kütüphanesi yüklenemedi!"
        show_notification(f"{PROGRAM_NAME} - HATA", msg, color='#e67e22')
    else:
        show_notification(PROGRAM_NAME, msg)

    # Start tray
    setup_tray()

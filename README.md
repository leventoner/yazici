# 🖊️ Yazıcı (V3.0) - Akıllı Metin Asistanı

**Yazıcı**, hem Türkçe karakter sorunlarını (ASCII) çözer hem de yapay zeka desteğiyle yazılarınızı (gramer, imla, kelime sırası) iyileştirir. Ayrıca gelişmiş ses tanımasıyla söylediklerinizi anında yazıya döker. 

---

## ✨ Öne Çıkan Özellikler

- **🎨 Premium Lacivert Tema:** Modern ve sade bir arayüzle şık bildirim panelleri.
- **🛠️ İsteğe Bağlı Özellikler:** Her bir özelliği (Karakter Düzeltme, AI İyileştirme, Sesle Yazma) sağ tık menüsünden tek tıkla açıp kapatabilirsiniz.
- **🖊️ Akıllı Düzeltme:** `mintlemon-turkish-nlp` ile kelime bağlamına göre en uygun Türkçe karakterleri seçer.
- **🤖 Yapay Zeka Desteği:** Google Gemini Pro API kullanarak metinlerinizin akıcılığını ve dilbilgisini mükemmelleştirir.
- **🎙️ Sesle Yaz (STT):** `sounddevice` ve `SpeechRecognition` altyapısıyla söylediklerinizi doğrudan imlecin olduğu yere yazar.
- **✨ Metin Seçimi Menüsü:** 3 kez tıklayarak veya fare ile metin seçtiğinizde beliren akıllı menü.
  - 🔠: Karakter Düzeltme
  - 🇹🇷: Türkçe İyileştirme
  - 🪄: Orijinal Dilde İyileştirme
- **⌨️ Akıllı Kısayollar:**
  - **2x Ctrl+C:** Karakter düzeltme.
  - **3x Ctrl+C:** Yapay zeka ile Türkçe iyileştirme.
  - **4x Ctrl+C:** Yapay zeka ile metnin özgün dilinde iyileştirme.
  - **Ctrl + Shift + Y:** Sesle yazmayı başlatır.

---

## 🚀 Başlangıç

### 1. Yapılandırma (`settings.json`)
Uygulama davranışını `settings.json` üzerinden özelleştirebilirsiniz:
- `stt_duration`: Ses kayıt süresi (Varsayılan: 10 saniye).
- `enable_...`: Özelliklerin başlangıç durumlarını (True/False) kontrol eder.
- `color_theme`: Bildirimlerin renk kodunu değiştirir.

### 2. Konfigürasyon
`.env` dosyasında `GEMINI_API_KEY` değerinin tanımlı olduğundan emin olun.

### 3. Çalıştırma
```powershell
python yazici.py
```

### 4. EXE Olarak Paketleme (Build)
Sanal ortam (venv) kullanıyorsanız şu komutla en sağlıklı EXE dosyasını oluşturabilirsiniz:
```powershell
python -m PyInstaller --noconsole --onefile --add-data "icon.png;." --add-data ".env;." --add-data "settings.json;." --icon="icon.ico" --collect-all zeyrek --collect-all mintlemon --collect-all google.generativeai --collect-all sounddevice --collect-all speech_recognition --collect-all pynput --name "Yazici" yazici.py
```

---
**Yazım, İyileştirme ve Ses Tanıma. Her şey tek bir tuşla.**
**Geliştirici:** Levent Öner
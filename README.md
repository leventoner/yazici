# 🇹🇷 İmla Düzeltici & Yazı İyileştirici (V2.0)

Bu yazılım, hem Türkçe karakter sorunlarını (ASCII) çözer hem de yapay zeka desteğiyle yazılarınızı (gramer, imla, kelime sırası) iyileştirir. Windows üzerinde arka planda çalışarak her türlü uygulamada (Chrome, Word, PDF, Notepad vb.) hızlıca kullanılabilir.

## ✨ Öne Çıkan Özellikler

- **Gelişmiş Düzeltme:** `mintlemon-turkish-nlp` ile kelime bağlamına göre en uygun Türkçe karakterleri seçer.
- **Yapay Zeka ile İyileştirme:** Google Gemini Pro API kullanarak metnin;
  - Dilbilgisi ve imla hatalarını giderir.
  - Kelime sırasını daha akıcı hale getirir.
  - Noktalama işaretlerini düzeltir.
  - Genel anlatım bozukluklarını giderir.
- **Akıllı Kısayollar:**
  - **2x Ctrl+C:** Sadece Türkçe karakterleri düzeltir (ASCII -> Türkçe).
  - **3x Ctrl+C:** Metni tamamen analiz eder ve yapay zeka ile iyileştirir (Improve).
  - **Ctrl + Shift + Y:** Söylediklerinizi metne çevirir (Speech-to-Text).
- **Modern Görsel Geri Bildirim:** İşlem yapıldığında sağ alt köşede renkli ve transparan bir bildirim paneli görünür.
- **Sistem Tepsisi (Taskbar):** Uygulama sağ alt köşede ikon olarak çalışır, sağ tıklayarak özellikleri görebilir veya çıkış yapabilirsiniz.

## 🚀 Başlangıç

### 1. Gemini API Anahtarı Ayarı
Yazı iyileştirme özelliğini kullanabilmek için bir API anahtarına ihtiyacınız vardır:
1. [Google AI Studio](https://aistudio.google.com/) üzerinden ücretsiz bir API anahtarı alın.
2. Proje dizinindeki `.env` dosyasını açın (eğer yoksa `.env.example` dosyasını kopyalayıp `.env` yapın).
3. `GEMINI_API_KEY=YOUR_API_KEY_HERE` kısmına aldığınız anahtarı yapıştırın.

### 2. Konfigürasyon ve Kısayollar
`settings.json` dosyasını kullanarak uygulamanın davranışını değiştirebilirsiniz:
- `hotkey`: Varsayılan `ctrl+c`. Değiştirmek isterseniz `ctrl+q`, `alt+c` gibi değerler yazabilirsiniz.
- `stt_hotkey`: Sesle yazma kısayolu. Varsayılan `ctrl+shift+y`.
- `stt_duration`: Ses kayıt süresi (saniye). Varsayılan `10`.
- `cooldown`: Çift/Üçlü tıklama hızı (saniye cinsinden).
- `notify_on_no_change`: Değişiklik olmadığında bildirim gösterilsin mi?

### 3. Sağ Tık Menüsü (Opsiyonel)
Dosyalara sağ tıkladığınızda "İmla Düzelt" seçeneklerini görmek isterseniz, terminali **Yönetici** olarak açıp şu komutu çalıştırın:
```bash
python add_context_menu.py
```

### 4. EXE Olarak Çalıştırma
En kolay kullanım yöntemi, `dist/` klasörü içindeki `imla_duzeltici.exe` dosyasını çalıştırmaktır.

### 5. Python ile Çalıştırma
Eğer kodu doğrudan Python ile çalıştırmak isterseniz:
1. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```
2. Uygulamayı başlatın:
   ```bash
   python imla_duzeltici.py
   ```

## 🛠️ Yeni EXE Üretme (Build)

Bu yazılımı güncellediğinizde veya tekrar EXE haline getirmek istediğinizde şu adımları izleyin:

1. **Çalışan Uygulamayı Kapatın**:
   Eğer uygulama şu an çalışıyorsa, EXE'nin üzerine yazabilmek için kapatmalısınız:
   ```powershell
   taskkill /F /IM imla_duzeltici.exe /T 2>$null
   ```

2. **Sanal Ortamı Aktif Edin**:
   ```powershell
   .\venv\Scripts\activate
   ```

3. **EXE Oluşturma Komutunu Çalıştırın**:
   Aşağıdaki komut, tüm bağımlılıkları ve veri dosyalarını tek bir EXE dosyasına paketler ve ikon ekler:
   ```powershell
   pyinstaller --noconsole --onefile --add-data "icon.png;." --add-data ".env;." --add-data "settings.json;." --icon="icon.ico" --collect-all zeyrek --collect-all mintlemon --collect-all google.generativeai --collect-all scipy --collect-all sounddevice --collect-all speech_recognition --name "imla_duzeltici" imla_duzeltici.py
   ```

4. **Sonuç**:
   İşlem bittiğinde yeni EXE dosyanız `dist/imla_duzeltici.exe` konumunda hazır olacaktır.

> [!NOTE]
> `build` klasörü ve `.spec` dosyası işlem sırasında geçici olarak oluşur, işlem bittikten sonra güvenle silebilirsiniz.

## 📦 Bağımlılıklar
- `mintlemon-turkish-nlp` / `zeyrek` (Dil işleme)
- `google-generativeai` (Yapay Zeka - Gemini)
- `pyperclip` (Pano yönetimi)
- `keyboard` (Tuş dinleme)
- `python-dotenv` (Çevre değişkenleri)
- `pystray` / `Pillow` (Sistem tepsisi)
- `SpeechRecognition` / `PyAudio` (Ses tanıma)

---
**Geliştirici:** Levent Öner
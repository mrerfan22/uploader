# Telegram Video Downloader & Uploader Bot 🚀

ربات دانلودر و آپلودر تلگرام (تا سقف ۲ گیگابایت) با قابلیت استخراج کیفیت‌های مختلف.

## ⚡ نصب و دیپلوی خودکار (One-Line Deploy)

برای نصب خودکار روی سرور لینوکس (Ubuntu / Debian)، دستور زیر را در ترمینال VPS وارد کنید:

```bash
bash <(curl -sL https://raw.githubusercontent.com/mrerfan22/uploader/main/deploy.sh)
```

هنگام اجرا، اسکریپت به صورت خودکار موارد زیر را در ترمینال از شما می‌پرسد:
- `API_ID`
- `API_HASH`
- `BOT_TOKEN`

## 🛠 دستورات مدیریت سرویس در سرور

* **مشاهده لاگ‌های زنده ربات:**
  ```bash
  journalctl -u uploader.service -f
  ```
* **ری‌استارت کردن ربات:**
  ```bash
  sudo systemctl restart uploader.service
  ```
* **متوقف کردن ربات:**
  ```bash
  sudo systemctl stop uploader.service
  ```
* **آپدیت کردن هسته دانلودر (`yt-dlp`):**
  ```bash
  sudo /opt/uploader/venv/bin/pip install -U yt-dlp && sudo systemctl restart uploader.service
  ```

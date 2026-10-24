import os
import re
import asyncio
from dotenv import load_dotenv
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp

# بارگذاری متغیرها از فایل .env
load_dotenv()

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("ph_downloader_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_links = {}

PH_REGEX = r"(https?://(?:www\.|cn\.|de\.|fr\.|es\.|it\.|pt\.|pl\.|rt\.|m\.)?pornhub\.(?:com|org)/view_video\.php\?viewkey=[a-zA-Z0-9]+)"

BASE_YDL_OPTS = {
    'quiet': True,
    'no_warnings': True,
    'geo_bypass': True,
    'age_limit': 99,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cookie': 'age_verified=1; platform=pc'
    }
}

def get_ph_info(url):
    with yt_dlp.YoutubeDL(BASE_YDL_OPTS) as ydl:
        info = ydl.extract_info(url, download=False)
        formats = []
        seen_heights = set()
        
        for f in info.get('formats', []):
            height = f.get('height')
            vcodec = f.get('vcodec', 'none')
            
            if height and vcodec != 'none' and height not in seen_heights:
                seen_heights.add(height)
                filesize = f.get('filesize') or f.get('filesize_approx')
                formats.append({
                    'height': height,
                    'filesize': filesize
                })
        
        formats.sort(key=lambda x: x['height'], reverse=True)
        return info.get('title', 'Video'), info.get('duration', 0), formats

def download_ph_video(url, height, output_path):
    ydl_opts = BASE_YDL_OPTS.copy()
    ydl_opts.update({
        'format': f'bestvideo[height<={height}]+bestaudio/best[height<={height}]/best',
        'outtmpl': output_path,
        'merge_output_format': 'mp4',
        'concurrent_fragment_downloads': 5,
    })
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

@app.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text(
        "🔥 **ربات دانلودر و آپلودر آماده است!**\n\n"
        "لینک ویدیو رو بفرست تا کیفیت‌های موجود رو استخراج کنم."
    )

@app.on_message(filters.text & filters.private)
async def handle_message(client, message):
    match = re.search(PH_REGEX, message.text.strip())
    if not match:
        await message.reply_text("❌ لطفاً یک لینک معتبر بفرست.")
        return

    url = match.group(1)
    status_msg = await message.reply_text("🔍 در حال بررسی لینک و استخراج کیفیت‌ها...")

    try:
        loop = asyncio.get_event_loop()
        title, duration, formats = await loop.run_in_executor(None, get_ph_info, url)

        if not formats:
            await status_msg.edit_text("❌ کیفیتی برای این ویدیو پیدا نشد.")
            return

        msg_id = str(message.id)
        user_links[msg_id] = {'url': url, 'title': title, 'duration': duration}

        buttons = []
        for f in formats:
            size_str = f" (~{int(f['filesize'] / (1024 * 1024))} MB)" if f['filesize'] else ""
            btn_text = f"🎬 کیفیت {f['height']}p{size_str}"
            buttons.append([InlineKeyboardButton(btn_text, callback_data=f"phdl|{msg_id}|{f['height']}")])

        mins, secs = divmod(duration, 60)
        await status_msg.edit_text(
            f"📹 **{title}**\n⏱ زمان: `{int(mins):02d}:{int(secs):02d}`\n\n👇 کیفیت را انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    except Exception as e:
        await status_msg.edit_text(f"❌ خطا:\n`{str(e)}`")

@app.on_callback_query(filters.regex(r"^phdl\|"))
async def process_download(client, callback_query):
    _, msg_id, height = callback_query.data.split("|")
    video_data = user_links.get(msg_id)

    if not video_data:
        await callback_query.answer("❌ لینک منقضی شده! دوباره بفرست.", show_alert=True)
        return

    await callback_query.message.edit_text(f"⏳ در حال دانلود کیفیت **{height}p** روی سرور...")
    file_name = f"ph_{msg_id}_{height}p.mp4"

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, download_ph_video, video_data['url'], height, file_name)

        await callback_query.message.edit_text("📤 دانلود تمام شد! در حال آپلود به تلگرام...")

        await client.send_video(
            chat_id=callback_query.message.chat.id,
            video=file_name,
            caption=f"📹 **{video_data['title']}**\n✅ کیفیت: `{height}p`",
            duration=int(video_data['duration']) if video_data['duration'] else 0,
            supports_streaming=True
        )
        await callback_query.message.delete()

    except Exception as e:
        await callback_query.message.edit_text(f"❌ خطا:\n`{str(e)}`")

    finally:
        if os.path.exists(file_name):
            os.remove(file_name)
        user_links.pop(msg_id, None)

if __name__ == "__main__":
    print("Bot is running...")
    app.run()

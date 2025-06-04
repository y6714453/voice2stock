import edge_tts
import asyncio
import subprocess
import requests
import os
import json
from requests_toolbelt.multipart.encoder import MultipartEncoder

# 📞 פרטי התחברות (דוגמה – לא אמיתיים)
USERNAME = "0733181201"
PASSWORD = "6714453"
TARGET_PATH = "ivr2:/8/"
ITEMS_FILE = "stock_items.json"

# 🧠 התחברות וקבלת טוקן מ־ימות המשיח
def get_token():
    response = requests.get(f"https://www.call2all.co.il/ym/api/Login?username={USERNAME}&password={PASSWORD}")
    data = response.json()
    token = data.get("token")
    if not token:
        raise Exception("❌ שגיאה בקבלת טוקן")
    print("✅ טוקן נשלף:", token)
    return token

# 💬 שליפת טקסט בסיסי למניה
def get_text(symbol, name):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=1d&interval=1d"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        data = response.json()['chart']['result'][0]
        price = data['meta']['regularMarketPrice']
        return f"מניית {name} נסחרת בשווי של {price:.2f} דולר"
    except Exception as e:
        print("❌ שגיאה בשליפת נתונים:", e)
        return f"מניית {name} - נתון לא זמין כרגע"

# 🎙 יצירת MP3
async def create_mp3(text, filename):
    print(f"🎤 מייצר קובץ קול עבור הטקסט: {text}")
    tts = edge_tts.Communicate(text, "he-IL-AvriNeural")
    await tts.save(filename)
    print(f"✅ קובץ MP3 נוצר: {filename}")

# 🎛 המרה ל-WAV
def convert_to_wav(mp3_file, wav_file):
    print(f"🎛 ממיר את {mp3_file} ל־{wav_file}")
    subprocess.run([
        "ffmpeg", "-y",
        "-i", mp3_file,
        "-ac", "1",
        "-ar", "8000",
        "-sample_fmt", "s16",
        wav_file
    ])

# ☁️ העלאה לימות
def upload_to_yemot(wav_file, path, token):
    if not os.path.exists(wav_file):
        print(f"❌ הקובץ {wav_file} לא נמצא")
        return

    with open(wav_file, 'rb') as f:
        m = MultipartEncoder(
            fields={
                'token': token,
                'path': path + "000.wav",
                'upload': (wav_file, f, 'audio/wav')
            }
        )
        response = requests.post(
            'https://www.call2all.co.il/ym/api/UploadFile',
            data=m,
            headers={'Content-Type': m.content_type}
        )

    print(f"🔍 קוד תגובה: {response.status_code}")
    print(f"🧾 טקסט תגובה: {response.text}")
    if response.status_code == 200 and 'OK' in response.text:
        print(f"✅ הועלה בהצלחה ל־{path}")
    else:
        print("❌ שגיאה בהעלאה לימות")

# 🚀 פונקציית הרצה ראשית
async def main():
    token = get_token()

    with open(ITEMS_FILE, encoding="utf-8") as f:
        items = json.load(f)

    for item in items:
        print(f"🔄 מטפל ב־{item['name']} ({item['symbol']})")
        text = get_text(item["symbol"], item["name"])
        mp3_file = "temp.mp3"
        wav_file = "temp.wav"

        await create_mp3(text, mp3_file)
        convert_to_wav(mp3_file, wav_file)
        upload_to_yemot(wav_file, item["target_path"], token)

# 📥 הרצה
asyncio.run(main())

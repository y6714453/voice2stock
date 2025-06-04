import speech_recognition as sr
import yfinance as yf
from difflib import get_close_matches
import edge_tts
import subprocess
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder
import os
import asyncio

# 🟡 הגדרות התחלתיות
USERNAME = "0733181201"
PASSWORD = "6714453"
VOICE = "he-IL-AvriNeural"
WAV_PATH = "temp.wav"
MP3_PATH = "temp.mp3"
UPLOAD_PATH = "ivr2:/8/000.wav"

# 🎯 מילון שמות מניות
stock_dict = {
    "טבע": "TEVA.TA",
    "לאומי": "LUMI.TA",
    "שופרסל": "SAE.TA"
}

# 🧠 מציאת ההתאמה הקרובה ביותר
def get_best_match(query):
    matches = get_close_matches(query, stock_dict.keys(), n=1, cutoff=0.6)
    return matches[0] if matches else None

# 🧾 תמלול מהקלטה
def transcribe_from_yemot():
    print("🎙️ מוריד קובץ הקלטה משלוחה 9...")
    r = requests.get("https://www.call2all.co.il/ym/api/DownloadFile", params={
        "token": f"{USERNAME}:{PASSWORD}",
        "path": "ivr2:/9/001.wav"
    })
    with open("input.wav", "wb") as f:
        f.write(r.content)

    print("🔠 ממיר לקובץ טקסט...")
    recognizer = sr.Recognizer()
    with sr.AudioFile("input.wav") as source:
        audio = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio, language="he-IL")
        except:
            return ""

# 📈 שליפת מחיר מניה
def get_stock_text(ticker, name):
    try:
        data = yf.Ticker(ticker).history(period="7d")
        current = data["Close"].iloc[-1]
        open_today = data["Open"].iloc[-1]
        change = ((current - open_today) / open_today) * 100
        sign = "עלייה" if change > 0 else "ירידה"
        percent = f"{abs(change):.1f}".replace(".", " נקודה ")
        return f"מניית {name} נסחרת כעת בשווי של {round(current, 2)} שקלים חדשים. מתחילת היום נרשמה {sign} של {percent} אחוז."
    except:
        return f"לא ניתן לשלוף נתונים עבור מניית {name}."

# 🎵 יצירת MP3 והמרה ל-WAV
async def create_voice_file(text):
    tts = edge_tts.Communicate(text, VOICE)
    await tts.save(MP3_PATH)
    subprocess.run(["ffmpeg", "-y", "-i", MP3_PATH, "-ar", "8000", "-ac", "1", WAV_PATH])

# ⬆️ העלאה לשלוחה 8
def upload_to_yemot():
    with open(WAV_PATH, 'rb') as f:
        m = MultipartEncoder(fields={
            'username': USERNAME,
            'password': PASSWORD,
            'path': UPLOAD_PATH,
            'upload': ('000.wav', f, 'audio/wav')
        })
        r = requests.post("https://www.call2all.co.il/ym/api/UploadFile", data=m, headers={'Content-Type': m.content_type})
        print("🧾 תגובת ימות:", r.text)

# ▶️ הרצה ראשית
async def main():
    text = transcribe_from_yemot()
    print("📃 תמלול:", text)

    match = get_best_match(text)
    if not match:
        print("❌ לא נמצאה מניה מתאימה.")
        return

    ticker = stock_dict[match]
    summary = get_stock_text(ticker, match)
    print("📜 נוסח קולי:", summary)

    await create_voice_file(summary)
    upload_to_yemot()

asyncio.run(main())

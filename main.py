import requests
import asyncio
import edge_tts
import os
import subprocess
import speech_recognition as sr
from requests_toolbelt.multipart.encoder import MultipartEncoder
import yfinance as yf
from datetime import datetime, timedelta

USERNAME = "0733181201"
PASSWORD = "6714453"
TOKEN = f"{USERNAME}:{PASSWORD}"

# 📥 הורדת קובץ מימות
def download_yemot_file():
    url = "https://www.call2all.co.il/ym/api/DownloadFile"
    params = {"token": TOKEN, "path": "ivr2:/9/000.wav"}
    response = requests.get(url, params=params)
    if response.status_code == 200 and response.content:
        with open("input.wav", "wb") as f:
            f.write(response.content)
        print("✅ ירד קובץ מימות המשיח")
        return "input.wav"
    else:
        print("📭 אין קובץ חדש")
        return None

# 🗑️ מחיקת הקובץ משלוחה 9
def delete_yemot_file():
    url = "https://www.call2all.co.il/ym/api/DeleteFile"
    params = {"token": TOKEN, "path": "ivr2:/9/000.wav"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        print("🗑️ הקובץ נמחק מהשלוחה")
    else:
        print("❌ שגיאה במחיקה:", response.text)

# 🎙️ תמלול
def transcribe_audio_google(file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio, language='he-IL')
        print("📃 תמלול:", text)
        return text
    except Exception as e:
        print("❌ שגיאה בתמלול:", e)
        return ""

# 🔍 תרגום שם למניה
def get_stock_symbol(text):
    if "טבע" in text:
        return "TEVA.TA", "טבע"
    elif "לאומי" in text:
        return "LUMI.TA", "לאומי"
    elif "שופרסל" in text:
        return "SAE.TA", "שופרסל"
    return None, None

# 📊 שליפת נתונים ויצירת נוסח
def get_stock_data(symbol, hebrew_name):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="6mo")
        today = hist.iloc[-1]
        price = round(today["Close"], 2)
        today_change = round(((today["Close"] - today["Open"]) / today["Open"]) * 100, 1)

        # השוואות
        start_year = hist.loc[hist.index >= datetime(datetime.now().year, 1, 1)]
        yearly_change = round(((today["Close"] - start_year["Open"][0]) / start_year["Open"][0]) * 100, 1) if not start_year.empty else 0

        max_price = hist["Close"].max()
        distance_from_high = round(((today["Close"] - max_price) / max_price) * 100, 1)

        # טקסט מנוסח
        result = (
            f"מניית {hebrew_name} נסחרת עכשיו בשווי של {price} שקלים חדשים. "
            f"מתחילת היום, {'עלייה' if today_change >= 0 else 'ירידה'} של {abs(today_change)} אחוז. "
            f"מתחילת השנה, {'עלייה' if yearly_change >= 0 else 'ירידה'} של {abs(yearly_change)} אחוז. "
            f"המחיר הנוכחי רחוק מהשיא ב־{abs(distance_from_high)} אחוז."
        )
        print("📝 נוסח קולי:", result)
        return result
    except Exception as e:
        print("❌ שגיאה בשליפת הנתונים:", e)
        return "אירעה שגיאה בשליפת נתוני המניה"

# 🗣️ יצירת קול
async def generate_edge_tts(text, mp3_path="temp.mp3", wav_path="output.wav"):
    voice = "he-IL-AsafNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(mp3_path)
    subprocess.run(["ffmpeg", "-y", "-i", mp3_path, wav_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# ⬆️ העלאה לשלוחה 8
def upload_to_yemot(wav_path):
    url = "https://www.call2all.co.il/ym/api/UploadFile"
    m = MultipartEncoder(
        fields={
            "token": TOKEN,
            "path": "ivr2:/8/000.wav",
            "convertAudio": "0",
            "upload": ("000.wav", open(wav_path, "rb"), "audio/wav")
        }
    )
    r = requests.post(url, data=m, headers={"Content-Type": m.content_type})
    if r.status_code == 200:
        print("✅ קובץ הועלה לשלוחה 8")
    else:
        print("❌ שגיאה בהעלאה:", r.text)

# 🔁 ריצה מתמשכת
async def main_loop():
    while True:
        file_path = download_yemot_file()
        if file_path:
            text = transcribe_audio_google(file_path)
            if text:
                symbol, hebrew_name = get_stock_symbol(text)
                if symbol:
                    stock_text = get_stock_data(symbol, hebrew_name)
                    await generate_edge_tts(stock_text)
                    upload_to_yemot("output.wav")
                else:
                    print("❌ לא זוהתה מניה מתאימה")
            delete_yemot_file()
        await asyncio.sleep(2)

# 🚀 הפעלה
asyncio.run(main_loop())

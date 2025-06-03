import requests
import asyncio
import edge_tts
import os
import tempfile
import subprocess
from requests_toolbelt.multipart.encoder import MultipartEncoder

# 🟡 פרטי המערכת שלך (אל תשכח לעדכן אם תחליף סיסמה)
USERNAME = "0733181201"
PASSWORD = "6714453"
TOKEN = f"{USERNAME}:{PASSWORD}"

# 📥 שליפת קובץ מהשלוחה (נניח שלוחה 9)
def download_yemot_file():
    url = "https://www.call2all.co.il/ym/api/DownloadFile"
    params = {
        "token": TOKEN,
        "path": "ivr2:/9/000.wav"
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        with open("input.wav", "wb") as f:
            f.write(response.content)
        print("✅ ירד קובץ מימות המשיח")
        return "input.wav"
    else:
        print("❌ לא הצליח להוריד קובץ")
        return None

# 🎙️ תמלול עם Whisper (ספריית openai-whisper)
def transcribe_audio_whisper(file_path):
    import whisper
    model = whisper.load_model("base")
    result = model.transcribe(file_path, language='he')
    print("📃 תמלול:", result['text'])
    return result['text']

# 🧠 ניתוח טקסט לשליפת מניה מתאימה
def get_stock_symbol(text):
    text = text.strip()
    if "טבע" in text:
        return "TEVA.TA"
    elif "לאומי" in text:
        return "LUMI.TA"
    elif "שופרסל" in text:
        return "SAE.TA"
    return None

# 📊 שליפת נתוני מניה מ־Yahoo Finance
def get_stock_data(symbol):
    import yfinance as yf
    stock = yf.Ticker(symbol)
    data = stock.history(period="1d")
    current = stock.info.get("currentPrice", 0)
    name = stock.info.get("shortName", "")
    return f"נפילת {name}: {current} ש"

# 🗣️ יצירת קובץ קול עם Edge-TTS ואז המרה ל-WAV
async def generate_edge_tts(text, mp3_path="temp.mp3", wav_path="output.wav"):
    voice = "he-IL-AvriMale"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(mp3_path)
    subprocess.run(["ffmpeg", "-y", "-i", mp3_path, wav_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# ⬆️ העלאת קובץ לימות המשיח לשלוחה 8
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

# 🚀 הרצת כל השלבים
async def main():
    audio_file = download_yemot_file()
    if not audio_file:
        return
    text = transcribe_audio_whisper(audio_file)
    symbol = get_stock_symbol(text)
    if not symbol:
        print("❌ לא זוהתה מניה מוכרת בתמלול")
        return
    stock_text = get_stock_data(symbol)
    await generate_edge_tts(stock_text)
    upload_to_yemot("output.wav")

# 🔁 הפעלה
asyncio.run(main())

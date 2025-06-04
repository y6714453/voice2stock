import requests
import asyncio
import edge_tts
import os
import subprocess
import speech_recognition as sr
from requests_toolbelt.multipart.encoder import MultipartEncoder

# 🟡 פרטי המערכת שלך
USERNAME = "0733181201"
PASSWORD = "6714453"
TOKEN = f"{USERNAME}:{PASSWORD}"

# 📥 שליפת קובץ מהשלוחה 9
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
        print("📭 אין קובץ חדש לשליפה")
        return None

# 🗑️ מחיקת קובץ מהשלוחה
def delete_yemot_file():
    url = "https://www.call2all.co.il/ym/api/DeleteFile"
    params = {"token": TOKEN, "path": "ivr2:/9/000.wav"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        print("🗑️ הקובץ נמחק מהשלוחה")
    else:
        print("❌ שגיאה במחיקה:", response.text)

# 🎙️ תמלול עם Google Speech Recognition
def transcribe_audio_google(file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio, language='he-IL')
        print("📃 תמלול:", text)
        return text
    except sr.UnknownValueError:
        print("❌ לא הבנתי את מה שנאמר")
        return ""
    except sr.RequestError as e:
        print("❌ שגיאה בבקשה ל־Google:", e)
        return ""

# 🧠 זיהוי שם מניה
def get_stock_symbol(text):
    text = text.strip()
    if "טבע" in text:
        return "TEVA.TA"
    elif "לאומי" in text:
        return "LUMI.TA"
    elif "שופרסל" in text:
        return "SAE.TA"
    return None

# 📊 שליפת נתוני מניה
def get_stock_data(symbol):
    import yfinance as yf
    stock = yf.Ticker(symbol)
    name = stock.info.get("shortName", "")
    price = stock.info.get("currentPrice", 0)
    return f"המחיר של {name} הוא {price} שקלים"

# 🎧 יצירת קובץ קול עם Edge-TTS והמרה ל-WAV
async def generate_edge_tts(text, mp3_path="temp.mp3", wav_path="output.wav"):
    voice = "he-IL-AsafNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(mp3_path)
    subprocess.run(["ffmpeg", "-y", "-i", mp3_path, wav_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

# ⬆️ העלאת קובץ לימות לשלוחה 8
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

# 🔁 לולאה מתמשכת כל 2 שניות
async def main_loop():
    while True:
        file_path = download_yemot_file()
        if file_path:
            text = transcribe_audio_google(file_path)
            if text:
                symbol = get_stock_symbol(text)
                if symbol:
                    stock_text = get_stock_data(symbol)
                    await generate_edge_tts(stock_text)
                    upload_to_yemot("output.wav")
                else:
                    print("❌ לא זוהתה מניה מתאימה")
            delete_yemot_file()
        await asyncio.sleep(2)

# 🚀 התחלה
asyncio.run(main_loop())

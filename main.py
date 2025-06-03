# 📁 קובץ: main.py

# 📦 ספריות נדרשות
import os
import requests
import speech_recognition as sr
from pydub import AudioSegment
import yfinance as yf

# 🔐 פרטי התחברות לימות המשיח
USERNAME = "0733181201"
PASSWORD = "6714453"
API_BASE = "https://www.call2all.co.il/ym/api/DownloadFile"
FILE_PATH = "ivr2:/9/001.wav"  # שנה את הנתיב לפי השלוחה שלך

# 🎯 מניות לחיפוש + טיקר
STOCKS = {
    "טבע": "TEVA.TA",
    "לאומי": "LUMI.TA",
    "שופרסל": "SAE.TA"
}

def download_file():
    print("⬇️ מוריד קובץ מימות...")
    response = requests.get(API_BASE, params={
        "token": f"{USERNAME}:{PASSWORD}",
        "path": FILE_PATH
    })
    if response.status_code == 200:
        with open("recorded.wav", "wb") as f:
            f.write(response.content)
        print("✅ קובץ נשמר בהצלחה.")
        return "recorded.wav"
    else:
        print("❌ שגיאה בהורדה:", response.text)
        return None

def transcribe_audio(file_path):
    print("🧠 ממיר ל־WAV ותמלול עם Google...")
    sound = AudioSegment.from_file(file_path)
    sound.export("converted.wav", format="wav")

    recognizer = sr.Recognizer()
    with sr.AudioFile("converted.wav") as source:
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio, language="he-IL")
        print("📄 טקסט מזוהה:", text)
        return text
    except sr.UnknownValueError:
        print("😶 לא זוהה טקסט מהקובץ.")
        return ""
    except sr.RequestError as e:
        print("🔌 שגיאת רשת:", e)
        return ""

def get_stock_info(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d")
    if not data.empty:
        price = data['Close'].iloc[-1]
        print(f"💹 מחיר נוכחי של {ticker}: {price} ₪")
        return price
    else:
        print("⚠️ לא נמצאו נתונים למניה זו.")
        return None

def main():
    file_path = download_file()
    if not file_path:
        return

    text = transcribe_audio(file_path)
    for hebrew_name, ticker in STOCKS.items():
        if hebrew_name in text:
            print(f"🔍 זוהתה מניה: {hebrew_name}")
            get_stock_info(ticker)
            break
    else:
        print("🔎 לא זוהתה אף מניה מהידועות.")

if __name__ == "__main__":
    main()

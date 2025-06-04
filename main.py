import requests
import asyncio
import edge_tts
import os
import subprocess
import speech_recognition as sr
from requests_toolbelt.multipart.encoder import MultipartEncoder
import yfinance as yf

USERNAME = "0733181201"
PASSWORD = "6714453"
TOKEN = f"{USERNAME}:{PASSWORD}"

# שליפת קובץ שמע מימות המשיח
def download_yemot_file():
    url = "https://www.call2all.co.il/ym/api/DownloadFile"
    params = {"token": TOKEN, "path": "ivr2:/9/000.wav"}
    response = requests.get(url, params=params)
    if response.status_code == 200 and response.content:
        with open("input.wav", "wb") as f:
            f.write(response.content)
        print("✅ ירד קובץ מימות המשיח")
        return "input.wav"
    print("📭 אין קובץ לשליפה")
    return None

# מחיקת קובץ מהשלוחה 9
def delete_yemot_file():
    url = "https://www.call2all.co.il/ym/api/DeleteFile"
    params = {"token": TOKEN, "path": "ivr2:/9/000.wav"}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        print("🗑️ הקובץ נמחק מהשלוחה 9")
    else:
        print("❌ שגיאה במחיקה:", response.text)

# תמלול עם Google
def transcribe_audio_google(file_path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(file_path) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio, language='he-IL')
        print("📃 תמלול:", text)
        return text
    except:
        print("❌ שגיאה בתמלול")
        return ""

# תרגום מילולי לשם סימבול
def get_stock_symbol(text):
    if "טבע" in text:
        return "TEVA.TA", "טבע"
    elif "לאומי" in text:
        return "LUMI.TA", "לאומי"
    elif "שופרסל" in text:
        return "SAE.TA", "שופרסל"
    return None, None

# שליפת נתונים מ-Yahoo ויצירת טקסט קולי
def get_stock_text(symbol, hebrew_name):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="6mo")
        info = stock.info
        price = info.get("currentPrice", 0)
        change_day = round(info.get("regularMarketChangePercent", 0), 1)
        change_year = round(info.get("52WeekChange", 0) * 100, 1)
        prev_close = info.get("regularMarketPreviousClose", 0)
        high_52 = info.get("fiftyTwoWeekHigh", price)
        from_high = round((price - high_52) / high_52 * 100, 1)

        return f"""מניית {hebrew_name} נסחרת כעת בשווי של {price} שקלים חדשים. 
מתחילת היום, {'עלייה' if change_day > 0 else 'ירידה'} של {abs(change_day)} אחוז.
מתחילת השנה, {'עלייה' if change_year > 0 else 'ירידה'} של {abs(change_year)} אחוז.
המחיר הנוכחי רחוק מהשיא ב־{abs(from_high)} אחוז."""
    except Exception as e:
        print("❌ שגיאה בשליפת נתונים:", e)
        return "אירעה שגיאה בשליפת נתוני המניה"

# יצירת MP3 + המרה ל-WAV
async def generate_edge_tts(text, mp3_path="temp.mp3", wav_path="output.wav"):
    try:
        communicate = edge_tts.Communicate(text, "he-IL-AsafNeural")
        await communicate.save(mp3_path)
        subprocess.run(["ffmpeg", "-y", "-i", mp3_path, wav_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print("❌ שגיאה ביצירת קול:", e)

# העלאה לשלוחה 8
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

# לולאה כל 2 שניות
async def main_loop():
    while True:
        file_path = download_yemot_file()
        if file_path:
            text = transcribe_audio_google(file_path)
            if text:
                symbol, heb_name = get_stock_symbol(text)
                if symbol:
                    stock_text = get_stock_text(symbol, heb_name)
                    print("📝 נוסח קולי:", stock_text)
                    await generate_edge_tts(stock_text)
                    upload_to_yemot("output.wav")
                else:
                    print("❌ מניה לא מזוהה")
            delete_yemot_file()
        await asyncio.sleep(2)

# הפעלה
asyncio.run(main_loop())

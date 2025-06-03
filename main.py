import requests
import os
import whisper
import yfinance as yf
from difflib import get_close_matches
import edge_tts
import asyncio
import subprocess
import time

# 🟡 טוקן ימות המשיח שלך
TOKEN = "pyVGAX3ov7hprizQ"

# 📁 שלוחה שמכילה את ההקלטות
RECORD_BRANCH = "9"
# 📤 אותה שלוחה גם לקבלת הפלט
OUTPUT_BRANCH = "9"

# 🧠 מודל זיהוי קולי
model = whisper.load_model("base")

# 📘 רשימת מניות בעברית (3 בלבד)
STOCK_DICT = {
    "טבע": "TEVA.TA",
    "לאומי": "LUMI.TA",
    "שופרסל": "SAE.TA"
}

# 🟠 קבלת קבצים מהשלוחה
def get_recordings():
    response = requests.get("https://www.call2all.co.il/ym/api/GetRecordings", params={
        "token": TOKEN,
        "path": f"ivr2:/{RECORD_BRANCH}"
    })
    return response.json().get("recordings", [])

# 🎧 תמלול
def transcribe_wav(filepath):
    result = model.transcribe(filepath, language="he")
    return result["text"].strip()

# 🔍 התאמת שם מניה
def get_best_match(query):
    return get_close_matches(query, STOCK_DICT.keys(), n=1, cutoff=0.6)[0] if get_close_matches(query, STOCK_DICT.keys(), n=1, cutoff=0.6) else None

# 📈 נתוני מניה
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1y")
        if hist.empty or len(hist) < 2:
            return None
        current = hist['Close'].iloc[-1]
        prev = hist['Close'].iloc[-2]
        week = hist['Close'].iloc[-6] if len(hist) > 6 else prev
        mo3 = hist['Close'].iloc[-66] if len(hist) > 66 else prev
        year = hist['Close'].iloc[0]
        high = hist['Close'].max()
        return {
            'current': round(current, 2),
            'day': round((current - prev) / prev * 100, 2),
            'week': round((current - week) / week * 100, 2),
            '3mo': round((current - mo3) / mo3 * 100, 2),
            'year': round((current - year) / year * 100, 2),
            'from_high': round((current - high) / high * 100, 2)
        }
    except:
        return None

def format_text(name, ticker, data):
    return (
        f"נמצאה מניה בשם {name}, סימול {ticker}. "
        f"המחיר הנוכחי הוא {data['current']} שקלים. "
        f"שינוי יומי: {data['day']} אחוז. "
        f"שינוי שבועי: {data['week']} אחוז. "
        f"שינוי בשלושה חודשים: {data['3mo']} אחוז. "
        f"שינוי מתחילת השנה: {data['year']} אחוז. "
        f"המניה רחוקה מהשיא ב־{abs(data['from_high'])} אחוז."
    )

# 🗣️ יצירת MP3
async def create_mp3(text, filename="output.mp3"):
    communicate = edge_tts.Communicate(text, voice="he-IL-AvriNeural")
    await communicate.save(filename)

# 🎛️ המרה ל-WAV
def convert_to_wav(mp3_file, wav_file):
    subprocess.run(["ffmpeg", "-y", "-i", mp3_file, wav_file])

# ⬆️ העלאה לימות
def upload_wav_to_yemot(wav_path, filename="output.wav"):
    with open(wav_path, 'rb') as f:
        files = {'upload': (filename, f, 'audio/wav')}
        data = {
            'token': TOKEN,
            'path': f'ivr2:/{OUTPUT_BRANCH}'
        }
        r = requests.post("https://www.call2all.co.il/ym/api/UploadFile", data=data, files=files)
        return r.text

def main_loop():
    seen = set()
    while True:
        recordings = get_recordings()
        for rec in recordings:
            filename = rec["name"]
            if filename in seen:
                continue

            print(f"📥 מעבד את: {filename}")
            wav_url = rec["url"]
            local_wav = "input.wav"
            r = requests.get(wav_url)
            with open(local_wav, "wb") as f:
                f.write(r.content)

            query = transcribe_wav(local_wav)
            print(f"🎧 זוהה טקסט: {query}")
            match = get_best_match(query)
            if not match:
                print("❌ לא נמצאה מניה תואמת")
                continue

            ticker = STOCK_DICT[match]
            data = get_stock_data(ticker)
            if not data:
                print("⚠️ בעיה בשליפת נתונים")
                continue

            text = format_text(match, ticker, data)
            asyncio.run(create_mp3(text))
            convert_to_wav("output.mp3", "output.wav")
            upload_wav_to_yemot("output.wav")
            print("✅ קובץ הועלה")

            seen.add(filename)

        time.sleep(1)

if __name__ == "__main__":
    main_loop()

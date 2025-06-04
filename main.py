# main.py

import asyncio
import time
from stock_utils import load_stock_list, get_best_match, get_stock_data, format_text
from yemot_api import download_yemot_file, delete_yemot_file, upload_yemot_file
from audio_tools import text_to_speech, convert_mp3_to_wav
from speech_recognition import Recognizer, AudioFile

# 🟡 פרטי התחברות לימות המשיח (אפשר גם .env בעתיד)
TOKEN = "0733181201:6714453"
STOCKS_CSV_PATH = "hebrew_stocks.csv"

def transcribe_audio(filename):
    recognizer = Recognizer()
    with AudioFile(filename) as source:
        audio_data = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio_data, language="he-IL")
        print(f"🗣️ זוהה: {text}")
        return text.strip()
    except Exception as e:
        print(f"❌ שגיאה בזיהוי קולי: {e}")
        return ""

async def process_stock_request():
    stock_list = load_stock_list(STOCKS_CSV_PATH)

    print("🔁 בודק אם יש קובץ חדש בשלוחה 9...")
    input_path = download_yemot_file(TOKEN)
    if not input_path:
        return

    query = transcribe_audio(input_path)
    if not query:
        print("⚠️ לא זוהה טקסט מההקלטה")
        delete_yemot_file(TOKEN)
        return

    best_match = get_best_match(query, stock_list)
    if not best_match:
        print("❌ לא נמצאה מניה מתאימה")
        delete_yemot_file(TOKEN)
        return

    ticker = stock_list[best_match]
    data = get_stock_data(ticker)
    if not data:
        print("⚠️ לא נמצאו נתונים למניה")
        delete_yemot_file(TOKEN)
        return

    text = format_text(best_match, ticker, data)
    print("📄 טקסט מוכן:", text)

    mp3_file = "output.mp3"
    wav_file = "output.wav"
    await text_to_speech(text, mp3_file)
    convert_mp3_to_wav(mp3_file, wav_file)
    upload_yemot_file(wav_file, TOKEN)

    delete_yemot_file(TOKEN)
    print("✅ הסתיים תהליך עבור", best_match)

def main_loop():
    while True:
        try:
            asyncio.run(process_stock_request())
        except Exception as e:
            print("❌ שגיאה בלולאה הראשית:", e)
        time.sleep(2)

if __name__ == "__main__":
    main_loop()

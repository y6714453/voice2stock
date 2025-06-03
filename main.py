import requests
import time
import os
import io
import yfinance as yf
import speech_recognition as sr
from pydub import AudioSegment
from gtts import gTTS
from requests_toolbelt.multipart.encoder import MultipartEncoder

# פרטים הזה מועקן לשלוף
YEMOT_TOKEN = "0733181201:6714453"
SOURCE_PATH = "ivr2:/9/000.wav"
TARGET_PATH = "ivr2:/8/000.wav"

# מילון מניה לסימל
stocks_dict = {
    "טבע": "TEVA.TA",
    "לאומי": "LUMI.TA",
    "שופרסל": "SAE.TA"
}


def download_yemot_file():
    url = "https://www.call2all.co.il/ym/api/DownloadFile"
    params = {
        "token": YEMOT_TOKEN,
        "path": SOURCE_PATH
    }
    response = requests.get(url, params=params)
    if response.status_code == 200 and len(response.content) > 1000:
        print("📅 נמצא קובץ בשלוחה 9")
        return response.content
    return None


def transcribe_audio(wav_bytes):
    with open("temp.wav", "wb") as f:
        f.write(wav_bytes)
    recognizer = sr.Recognizer()
    with sr.AudioFile("temp.wav") as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio, language="he-IL")
        print(f"🔊 תמלול: {text}")
        return text.strip()
    except sr.UnknownValueError:
        print("❌ לא זהה מילה")
        return ""


def get_stock_info(name):
    ticker = stocks_dict.get(name)
    if not ticker:
        return None
    stock = yf.Ticker(ticker)
    try:
        info = stock.info
        price = info.get("regularMarketPrice", 0)
        change = info.get("regularMarketChangePercent", 0)
        return f"נפיל {name}: {price} ש"
    except:
        return None


def generate_speech(text):
    tts = gTTS(text=text, lang='he')
    tts.save("output.mp3")
    sound = AudioSegment.from_mp3("output.mp3")
    sound.export("output.wav", format="wav")


def upload_file():
    with open("output.wav", "rb") as f:
        m = MultipartEncoder(
            fields={
                'token': YEMOT_TOKEN,
                'path': TARGET_PATH,
                'upload': ('output.wav', f, 'audio/wav'),
                'convertAudio': '1'
            }
        )
        res = requests.post("https://www.call2all.co.il/ym/api/UploadFile", data=m, headers={'Content-Type': m.content_type})
        if res.status_code == 200:
            print("✅ קובץ עלה בהצלחה 8")
        else:
            print("❌ שגיאה בהעלאה")


# לולאה רצינות
while True:
    data = download_yemot_file()
    if data:
        query = transcribe_audio(data)
        for word in stocks_dict:
            if word in query:
                text = get_stock_info(word)
                if text:
                    print(f"📈 {text}")
                    generate_speech(text)
                    upload_file()
                break
    time.sleep(2)

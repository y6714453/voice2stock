from gtts import gTTS
import os
import subprocess
import requests
from requests_toolbelt.multipart.encoder import MultipartEncoder

# 🟡 פרטי המערכת (שנה לפי הצורך)
USERNAME = "0733181201"
PASSWORD = "6714453"
TOKEN = f"{USERNAME}:{PASSWORD}"

def generate_gtts(text, mp3_path="test.mp3", wav_path="test.wav"):
    try:
        print("🎤 מנסה ליצור קובץ MP3 עם gTTS...")
        tts = gTTS(text=text, lang='he')
        tts.save(mp3_path)

        if not os.path.exists(mp3_path):
            print("❌ קובץ MP3 לא נוצר.")
            return False

        subprocess.run([
            "ffmpeg", "-y", "-i", mp3_path,
            "-ar", "8000", "-ac", "1", wav_path
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if os.path.exists(wav_path):
            print("✅ קובץ WAV נוצר בהצלחה.")
            return True
        else:
            print("❌ ffmpeg לא יצר את WAV.")
            return False

    except Exception as e:
        print("❌ שגיאה ביצירת אודיו:", e)
        return False

def upload_to_yemot(wav_path):
    if not os.path.exists(wav_path):
        print("⚠️ קובץ WAV לא נמצא – לא ניתן להעלות.")
        return
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
        print("✅ קובץ הועלה לשלוחה 8 בהצלחה.")
    else:
        print("❌ שגיאה בהעלאה לימות:", r.text)

def main():
    text = "מניית שופרסל נסחרת בשווי של שלושת אלפים חמש מאות שמונים ותשעה דולר"
    success = generate_gtts(text)
    if success:
        upload_to_yemot("test.wav")

main()

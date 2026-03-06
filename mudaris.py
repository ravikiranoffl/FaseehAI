import os
import re
import glob
from datetime import datetime
import requests
import google.generativeai as genai
from gtts import gTTS

# --- 1. SETUP & CREDENTIALS ---
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def main():
    # --- 2. READ YESTERDAY'S LESSON ---
    list_of_files = glob.glob('lessons/*.txt')
    if not list_of_files:
        yesterdays_lesson = "This is day 1. Start from Phase 1, Day 1."
    else:
        latest_file = max(list_of_files, key=os.path.getctime)
        with open(latest_file, 'r', encoding='utf-8') as f:
            yesterdays_lesson = f.read()

    # --- 3. GENERATE TODAY'S LESSON ---
    with open('prompt.txt', 'r', encoding='utf-8') as f:
        master_prompt = f.read()

    model = genai.GenerativeModel('gemini-2.5-pro')
    full_prompt = f"{master_prompt}\n\n### YESTERDAY'S LESSON:\n{yesterdays_lesson}\n\nGenerate today's lesson now."
    
    response = model.generate_content(full_prompt)
    generated_text = response.text

    # --- 4. EXTRACT AUDIO & CLEAN TEXT ---
    audio_segments = re.findall(r'<AUDIO:\s*(.*?)>', generated_text)
    combined_audio_text = " ... ".join(audio_segments) 

    clean_telegram_text = re.sub(r'<AUDIO:\s*(.*?)>', r'\1', generated_text)

    # --- 5. GENERATE MP3 ---
    audio_path = "lesson_audio.mp3"
    if combined_audio_text.strip():
        tts = gTTS(text=combined_audio_text, lang='ar')
        tts.save(audio_path)

    # --- 6. SEND TO TELEGRAM ---
    send_text_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(send_text_url, data={'chat_id': TELEGRAM_CHAT_ID, 'text': clean_telegram_text})

    if os.path.exists(audio_path):
        send_audio_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendAudio"
        with open(audio_path, 'rb') as audio_file:
            requests.post(send_audio_url, data={'chat_id': TELEGRAM_CHAT_ID}, files={'audio': audio_file})

    # --- 7. SAVE TODAY'S LESSON ---
    today_str = datetime.now().strftime("%Y%m%d")
    new_filename = f"lessons/MSA-{today_str}.txt"
    
    with open(new_filename, 'w', encoding='utf-8') as f:
        f.write(generated_text) 
    
    print(f"Successfully saved {new_filename}")

if __name__ == "__main__":
    main()

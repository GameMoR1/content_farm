"""
Generate SRT/ASS captions for segments, style presets, emoji injection, safe-area, karaoke effect.
"""
import os
import json
from typing import List, Dict
import cv2

MEDIA_WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'media', 'work'))
os.makedirs(MEDIA_WORK, exist_ok=True)

# Emoji-словарь (пример)
EMOJI_DICT = {
    "1": "1️⃣", "2": "2️⃣", "3": "3️⃣", "!": "❗", "?": "❓",
    "happy": "😃", "sad": "😢", "fire": "🔥", "star": "⭐"
}

async def generate_captions(transcript_result, highlights, job_data):
    job_id = job_data["job_id"]
    job_dir = os.path.join(MEDIA_WORK, job_id)
    os.makedirs(job_dir, exist_ok=True)
    style = job_data.get("style_preset", "clean")
    emojis = job_data.get("emojis", True)
    for seg in highlights:
        seg_id = seg["id"]
        start, end = seg["start"], seg["end"]
        # Фильтруем слова по времени
        words = []
        for s in transcript_result["segments"]:
            for w in s["words"]:
                if w["start"] >= start and w["end"] <= end:
                    words.append(w)
        # Генерируем текст с эмодзи
        text = " ".join([inject_emoji(w["word"], emojis) for w in words])
        # SRT
        srt_path = os.path.join(job_dir, f"{seg_id}.srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(f"1\n{format_time(start)} --> {format_time(end)}\n{text}\n\n")
        # ASS (стилизация)
        ass_path = os.path.join(job_dir, f"{seg_id}.ass")
        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(generate_ass(text, start, end, style))

def inject_emoji(word, enable):
    if not enable:
        return word
    return EMOJI_DICT.get(word.lower(), word)

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def generate_ass(text, start, end, style):
    # Минимальный ASS с одним сабом и стилем
    return f"""[Script Info]\nTitle: Caption\nScriptType: v4.00+\n\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, OutlineColour, BackColour, Bold, Italic, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,Arial,48,&H00FFFFFF,&H00000000,&H00000000,0,0,1,3,1,2,10,10,10,1\n\n[Events]\nFormat: Layer, Start, End, Style, Text\nDialogue: 0,{ass_time(start)},{ass_time(end)},Default,{text}\n"""

def ass_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    cs = int((seconds - int(seconds)) * 100)
    return f"{h:01}:{m:02}:{s:02}.{cs:02}"

async def generate_previews(video_path, highlights, job_data):
    job_id = job_data["job_id"]
    job_dir = os.path.join(MEDIA_WORK, job_id)
    os.makedirs(job_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    for seg in highlights:
        seg_id = seg["id"]
        mid = (seg["start"] + seg["end"]) / 2
        cap.set(cv2.CAP_PROP_POS_MSEC, mid * 1000)
        ret, frame = cap.read()
        if ret:
            jpg_path = os.path.join(job_dir, f"{seg_id}_preview.jpg")
            cv2.imwrite(jpg_path, frame)
    cap.release()

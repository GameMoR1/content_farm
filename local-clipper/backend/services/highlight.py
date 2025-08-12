"""
Highlight detection: scenes (PySceneDetect), audio features (librosa), text signals (RAKE/KeyBERT), scoring, NMS, save highlights.json.
"""
import os
import json
import numpy as np
import librosa
from scenedetect import VideoManager, SceneManager
from scenedetect.detectors import ContentDetector
from keybert import KeyBERT
from rake_nltk import Rake
from typing import List, Dict

MEDIA_WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'media', 'work'))
os.makedirs(MEDIA_WORK, exist_ok=True)

async def detect_highlights(video_path, transcript_result, job_data):
    job_id = job_data["job_id"]
    job_dir = os.path.join(MEDIA_WORK, job_id)
    os.makedirs(job_dir, exist_ok=True)
    cache_json = os.path.join(job_dir, "highlights.json")
    if os.path.exists(cache_json):
        with open(cache_json, encoding='utf-8') as f:
            return json.load(f)
    # 1. Сцены (PySceneDetect)
    video_manager = VideoManager([video_path])
    scene_manager = SceneManager()
    scene_manager.add_detector(ContentDetector())
    video_manager.set_downscale_factor()
    video_manager.start()
    scene_manager.detect_scenes(frame_source=video_manager)
    scene_list = scene_manager.get_scene_list()
    scenes = [(start.get_seconds(), end.get_seconds()) for start, end in scene_list]
    video_manager.release()
    # 2. Аудио признаки (librosa)
    audio_path = os.path.splitext(video_path)[0] + ".wav"
    y, sr = librosa.load(audio_path, sr=None)
    rms = librosa.feature.rms(y=y)[0]
    flux = librosa.onset.onset_strength(y=y, sr=sr)
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    # 3. Текстовые признаки (RAKE/KeyBERT)
    text = " ".join([seg['text'] for seg in transcript_result['segments']])
    kw_model = KeyBERT()
    keywords = kw_model.extract_keywords(text, top_n=10)
    rake = Rake()
    rake.extract_keywords_from_text(text)
    rake_keywords = rake.get_ranked_phrases()[:10]
    # 4. Формирование кандидатов (20-60s)
    candidates = []
    for s, e in scenes:
        if e - s < 20 or e - s > 60:
            continue
        candidates.append({"start": s, "end": e})
    # 5. Считаем скор для каждого кандидата
    for c in candidates:
        # Аудио признаки (усреднение по сегменту)
        idx_start = int(c["start"] * sr)
        idx_end = int(c["end"] * sr)
        c["rms"] = float(np.mean(rms[idx_start:idx_end]))
        c["flux"] = float(np.mean(flux[int(c["start"]):int(c["end"])]))
        c["zcr"] = float(np.mean(zcr[idx_start:idx_end]))
        # Текстовые признаки (кол-во ключевых фраз)
        c["kw_count"] = sum(1 for kw, _ in keywords if kw in text[int(c["start"]):int(c["end"])] )
        c["rake_count"] = sum(1 for kw in rake_keywords if kw in text[int(c["start"]):int(c["end"])] )
        # Итоговый скор (простая сумма)
        c["score"] = c["rms"] + c["flux"] + c["zcr"] + c["kw_count"] + c["rake_count"]
    # 6. NMS по перекрытиям
    candidates = sorted(candidates, key=lambda x: -x["score"])
    selected = []
    for c in candidates:
        overlap = False
        for s in selected:
            if min(c["end"], s["end"]) - max(c["start"], s["start"]) > 2:
                overlap = True
                break
        if not overlap:
            selected.append(c)
        if len(selected) >= (job_data.get("max_clips") or 15):
            break
    # 7. Сохраняем highlights.json
    for i, seg in enumerate(selected):
        seg["id"] = f"seg_{i+1}"
    with open(cache_json, "w", encoding="utf-8") as f:
        json.dump(selected, f, ensure_ascii=False, indent=2)
    return selected

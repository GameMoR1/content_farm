"""
Local ASR with faster-whisper, VAD (silero-vad), audio extraction, language detection, caching.
"""
import os
import hashlib
import json
import torch
import numpy as np
from faster_whisper import WhisperModel
from typing import Optional

MEDIA_WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'media', 'work'))
os.makedirs(MEDIA_WORK, exist_ok=True)

# Silero VAD
try:
    import torch
    vad_model, utils = torch.hub.load(
        repo_or_dir='snakers4/silero-vad', model='silero_vad', force_reload=False, trust_repo=True)
    (get_speech_timestamps, save_audio, read_audio, VAD_SAMPLE_RATE) = utils
except Exception:
    vad_model = None
    get_speech_timestamps = None
    read_audio = None
    VAD_SAMPLE_RATE = 16000

# Модель whisper и параметры
WHISPER_MODEL = None
WHISPER_MODEL_SIZE = os.environ.get("MODEL_SIZE", "small")
WHISPER_DEVICE = os.environ.get("DEVICE", "auto")
WHISPER_COMPUTE = os.environ.get("WHISPER_COMPUTE", "auto")

def get_device_and_compute():
    if WHISPER_DEVICE == "auto":
        if torch.cuda.is_available():
            return "cuda", "float16"
        else:
            return "cpu", "int8_float16"
    return WHISPER_DEVICE, WHISPER_COMPUTE

def load_model():
    global WHISPER_MODEL
    if WHISPER_MODEL is None:
        device, compute_type = get_device_and_compute()
        WHISPER_MODEL = WhisperModel(WHISPER_MODEL_SIZE, device=device, compute_type=compute_type)
    return WHISPER_MODEL

def sha1_of_file(path):
    h = hashlib.sha1()
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def vad_split(audio, sample_rate):
    if get_speech_timestamps is None:
        return [(0, len(audio))]
    speech = get_speech_timestamps(audio, vad_model, sampling_rate=sample_rate)
    return [(s['start'], s['end']) for s in speech]

def save_srt(segments, path):
    with open(path, 'w', encoding='utf-8') as f:
        for i, seg in enumerate(segments, 1):
            start = seg['start']
            end = seg['end']
            text = seg['text']
            f.write(f"{i}\n{format_time(start)} --> {format_time(end)}\n{text}\n\n")

def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

async def transcribe(audio_path, job_data):
    """
    Транскрипция с VAD, word-level timestamps, автоязык, кэш по SHA1.
    """
    job_id = job_data["job_id"]
    job_dir = os.path.join(MEDIA_WORK, job_id)
    os.makedirs(job_dir, exist_ok=True)
    audio_sha1 = sha1_of_file(audio_path)
    cache_json = os.path.join(job_dir, f"transcript_{audio_sha1}.json")
    cache_srt = os.path.join(job_dir, f"transcript_{audio_sha1}.srt")
    if os.path.exists(cache_json) and os.path.exists(cache_srt):
        with open(cache_json, encoding='utf-8') as f:
            return json.load(f)
    # VAD
    audio = read_audio(audio_path, sampling_rate=VAD_SAMPLE_RATE)
    speech_segments = vad_split(audio, VAD_SAMPLE_RATE)
    # Whisper
    model = load_model()
    lang = job_data.get("lang")
    segments = []
    words = []
    confidences = []
    for start, end in speech_segments:
        segment_audio = audio[start:end]
        if len(segment_audio) < VAD_SAMPLE_RATE * 0.5:
            continue
        result, info = model.transcribe(segment_audio, language=lang, vad_filter=False, word_timestamps=True, beam_size=5)
        for seg in result:
            segments.append({
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
                "words": [{"word": w.word, "start": w.start, "end": w.end, "confidence": w.probability} for w in seg.words],
                "confidence": np.mean([w.probability for w in seg.words]) if seg.words else 1.0
            })
            words.extend(seg.words)
            confidences.extend([w.probability for w in seg.words])
    avg_conf = float(np.mean(confidences)) if confidences else 1.0
    language = info.get("language", "auto")
    duration = sum([seg[1] - seg[0] for seg in speech_segments]) / VAD_SAMPLE_RATE
    # Сохраняем SRT и JSON
    save_srt(segments, cache_srt)
    with open(cache_json, "w", encoding="utf-8") as f:
        json.dump({
            "segments": segments,
            "words": [w.word for w in words],
            "language": language,
            "avg_confidence": avg_conf,
            "duration": duration
        }, f, ensure_ascii=False, indent=2)
    return {
        "segments": segments,
        "words": [w.word for w in words],
        "language": language,
        "avg_confidence": avg_conf,
        "duration": duration
    }

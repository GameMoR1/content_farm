"""
Local title/hook/hashtags generation via Ollama, fallback to empty, cache meta/{seg_id}.json.
"""
import os
import json
import requests

MEDIA_WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'media', 'work'))
os.makedirs(MEDIA_WORK, exist_ok=True)
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_URL = "http://localhost:11434/api/generate"

async def generate_meta(job_id, seg_id, transcript_text):
    meta_dir = os.path.join(MEDIA_WORK, job_id, "meta")
    os.makedirs(meta_dir, exist_ok=True)
    meta_path = os.path.join(meta_dir, f"{seg_id}.json")
    if os.path.exists(meta_path):
        with open(meta_path, encoding='utf-8') as f:
            return json.load(f)
    prompt = f"""
На основе текста сегмента сгенерируй:
- 5 коротких title (<=70 символов)
- 3 hook (1 фраза)
- 10 hashtags (без #)
Текст:
{transcript_text}
"""
    try:
        resp = requests.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "prompt": prompt,
            "stream": False
        }, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            # Простейший парсер (ожидается json или текст с разделителями)
            out = parse_ollama_response(data.get("response", ""))
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
            return out
    except Exception:
        pass
    # Fallback
    out = {"titles": [], "hooks": [], "hashtags": []}
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    return out

def parse_ollama_response(text):
    # Ожидается json или текст с разделителями
    try:
        return json.loads(text)
    except Exception:
        # Попробуем парсить вручную
        lines = text.splitlines()
        titles, hooks, hashtags = [], [], []
        for l in lines:
            l = l.strip()
            if l.lower().startswith("title"):
                titles.append(l.split(":",1)[-1].strip())
            elif l.lower().startswith("hook"):
                hooks.append(l.split(":",1)[-1].strip())
            elif l.lower().startswith("hashtag"):
                hashtags.append(l.split(":",1)[-1].strip().replace("#", ""))
        return {"titles": titles, "hooks": hooks, "hashtags": hashtags}

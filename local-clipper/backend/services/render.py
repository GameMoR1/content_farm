"""
Clip rendering: ffmpeg crop/scale, панорамирование по треку, fps, loudnorm, burn-in сабы через ASS, ресэмпл, вывод mp4/webm, safe titles area.
"""
import os
import subprocess
import asyncio
import json
from typing import List, Dict

MEDIA_WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'media', 'work'))
MEDIA_OUTPUTS = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'media', 'outputs'))
os.makedirs(MEDIA_OUTPUTS, exist_ok=True)

async def render_segments(job_id: str, segments: List[Dict], resolution: int = 720, fmt: str = "mp4"):
    job_dir = os.path.join(MEDIA_WORK, job_id)
    outputs = []
    for seg in segments:
        seg_id = seg["id"]
        start, end = seg["start"], seg["end"]
        style = seg.get("style", "clean")
        captions = seg.get("captions", True)
        overlays = seg.get("overlays", [])
        track_path = os.path.join(job_dir, "tracks", f"{seg_id}.json")
        ass_path = os.path.join(job_dir, f"{seg_id}.ass")
        src_video = None
        # Поиск исходного видео
        for f in os.listdir(os.path.join(os.path.dirname(__file__), '..', '..', 'media', 'source')):
            if job_id in f:
                src_video = os.path.join(os.path.dirname(__file__), '..', '..', 'media', 'source', f)
                break
        if not src_video:
            continue
        out_path = os.path.join(MEDIA_OUTPUTS, f"{job_id}_{seg_id}.{fmt}")
        # ffmpeg: crop/scale, панорамирование, сабы, аудио
        filter_complex = []
        # Панорамирование по треку (если есть)
        if os.path.exists(track_path):
            with open(track_path, encoding='utf-8') as f:
                track = json.load(f)
            # Пример: crop=ih*9/16:ih:x:y
            # (реализация панорамирования по треку — placeholder, требует ffmpeg фильтра)
            filter_complex.append(f"crop=ih*9/16:ih")
        # Масштабирование
        if resolution == 1080:
            filter_complex.append("scale=1080:1920")
        else:
            filter_complex.append("scale=720:1280")
        # Сабтайтлы
        if captions and os.path.exists(ass_path):
            filter_complex.append(f"ass={ass_path}")
        # Аудио
        audio_filters = ["loudnorm", "aresample=48000"]
        # Итоговый фильтр
        vf = ",".join(filter_complex)
        af = ",".join(audio_filters)
        cmd = [
            "ffmpeg", "-y",
            "-i", src_video,
            "-ss", str(start), "-to", str(end),
            "-vf", vf,
            "-af", af,
            "-c:v", "libx264" if fmt=="mp4" else "libvpx-vp9",
            "-c:a", "aac" if fmt=="mp4" else "libopus",
            "-b:v", "4M",
            "-b:a", "192k",
            out_path
        ]
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        _, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg error: {stderr.decode(errors='ignore')}")
        outputs.append(out_path)
    return outputs

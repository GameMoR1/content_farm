"""
FastAPI backend: API routes, static files, CORS, error handling.
"""
from fastapi import FastAPI, BackgroundTasks, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
from typing import Optional, List
import os
import uuid
import shutil
import json

from .workers import job_queue
from .services import downloader, transcript, highlight, reframing, captions, styling, title_hook_tags, virality, render

app = FastAPI()

# --- Pydantic models ---
class JobRequestUrl(BaseModel):
    url: str
    lang: Optional[str] = None
    max_clips: Optional[int] = None
    clip_len: Optional[int] = None
    style_preset: Optional[str] = None
    aspect: Optional[str] = "9:16"
    emojis: Optional[bool] = True
    po_token: Optional[str] = None  # Добавлено поле для po_token

class RenderSegment(BaseModel):
    id: str
    start: float
    end: float
    style: Optional[str] = None
    captions: Optional[bool] = True
    overlays: Optional[List[str]] = None

class RenderRequest(BaseModel):
    segments: List[RenderSegment]
    resolution: int = 720
    format: str = "mp4"

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static frontend at /static
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'frontend'))
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path, html=True), name="frontend")

from fastapi.responses import FileResponse

@app.get("/")
def root():
    # Редирект на /static/index.html для корректной загрузки UI
    return FileResponse(os.path.join(frontend_path, "index.html"), media_type='text/html')

# --- API endpoints ---
@app.post("/api/job/from_url")
async def job_from_url(req: JobRequestUrl, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    # Сохранить job, добавить в очередь
    job_data = req.dict()
    job_data["job_id"] = job_id
    job_queue.progress[job_id] = {"status": "queued", "steps": []}
    await job_queue.queue.put((job_id, job_data))
    return {"job_id": job_id}

@app.post("/api/job/from_file")
async def job_from_file(file: UploadFile = File(...), lang: Optional[str] = Form(None), max_clips: Optional[int] = Form(None), clip_len: Optional[int] = Form(None), style_preset: Optional[str] = Form(None), aspect: Optional[str] = Form("9:16"), emojis: Optional[bool] = Form(True), po_token: Optional[str] = Form(None), background_tasks: BackgroundTasks = None):
    job_id = str(uuid.uuid4())
    # Сохранить файл
    source_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'media', 'source'))
    os.makedirs(source_dir, exist_ok=True)
    file_path = os.path.join(source_dir, f"{job_id}_{file.filename}")
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    job_data = {
        "job_id": job_id,
        "file_path": file_path,
        "lang": lang,
        "max_clips": max_clips,
        "clip_len": clip_len,
        "style_preset": style_preset,
        "aspect": aspect,
        "emojis": emojis,
        "po_token": po_token
    }
    job_queue.progress[job_id] = {"status": "queued", "steps": []}
    await job_queue.queue.put((job_id, job_data))
    return {"job_id": job_id}

@app.get("/api/job/{job_id}")
async def get_job_status(job_id: str):
    status = job_queue.progress.get(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status

@app.post("/api/job/{job_id}/meta/{seg_id}")
async def generate_meta(job_id: str, seg_id: str):
    # Заглушка: вызвать title_hook_tags.generate_meta
    return {"titles": [], "hooks": [], "hashtags": []}

@app.post("/api/job/{job_id}/render")
async def render_job(job_id: str, req: RenderRequest):
    # Заглушка: вызвать render.render_segments
    return {"result": "ok"}

@app.get("/api/job/{job_id}/result")
async def get_job_result(job_id: str):
    # Заглушка: вернуть пути к рендерам
    return {"outputs": []}

@app.get("/api/presets")
async def get_presets():
    presets_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'presets.json'))
    with open(presets_path, encoding="utf-8") as f:
        presets = json.load(f)
    return presets

@app.get("/api/job/{job_id}/highlights")
async def get_job_highlights(job_id: str):
    """
    Возвращает highlights.json для job_id или запускает детекцию, если файл отсутствует.
    """
    from .services import highlight, transcript
    MEDIA_WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'media', 'work'))
    job_dir = os.path.join(MEDIA_WORK, job_id)
    cache_json = os.path.join(job_dir, "highlights.json")
    if os.path.exists(cache_json):
        with open(cache_json, encoding='utf-8') as f:
            return json.load(f)
    # Попробовать найти необходимые данные для запуска детекции
    video_path = None
    transcript_result = None
    # Поиск видеофайла
    for fname in os.listdir(job_dir):
        if fname.endswith(('.mp4', '.mkv', '.mov', '.avi')):
            video_path = os.path.join(job_dir, fname)
            break
    # Поиск транскрипта
    transcript_json = os.path.join(job_dir, "transcript.json")
    if os.path.exists(transcript_json):
        with open(transcript_json, encoding='utf-8') as f:
            transcript_result = json.load(f)
    if not video_path or not transcript_result:
        raise HTTPException(status_code=404, detail="Video or transcript not found for this job")
    # Запуск детекции
    highlights = await highlight.detect_highlights(video_path, transcript_result, {"job_id": job_id})
    return highlights

# --- Error handlers ---
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return {"error": str(exc)}

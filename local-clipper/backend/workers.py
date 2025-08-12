"""
Asyncio task queue, progress manager, pipeline scheduler.
"""
import asyncio
import os
import json
import hashlib
from typing import Dict, Any
from .services import downloader, transcript, highlight, reframing, captions, render

WORK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'media', 'work'))
os.makedirs(WORK_DIR, exist_ok=True)

PIPELINE_STEPS = [
    "download",
    "audio_extract",
    "transcript",
    "highlights",
    "reframing",
    "previews",
    "captions",
    "ready"
]

async def save_status(job_id, status):
    job_dir = os.path.join(WORK_DIR, job_id)
    os.makedirs(job_dir, exist_ok=True)
    status_path = os.path.join(job_dir, "status.json")
    with open(status_path, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)

class JobQueue:
    def __init__(self, workers=2):
        self.queue = asyncio.Queue()
        self.progress: Dict[str, Any] = {}
        self.workers = workers

    async def worker(self):
        while True:
            job_id, job_data = await self.queue.get()
            try:
                status = {"status": "processing", "steps": []}
                self.progress[job_id] = status
                await save_status(job_id, status)
                # 1. Download
                status["steps"].append({"step": "download", "status": "started", "progress": 0})
                await save_status(job_id, status)
                # --- Новый: вызвать download синхронно через run_in_executor ---
                loop = asyncio.get_event_loop()
                def sync_download():
                    return downloader.download(job_data)
                source_path = await loop.run_in_executor(None, sync_download)
                status["steps"][-1]["status"] = "done"
                status["steps"][-1]["progress"] = 100
                await save_status(job_id, status)
                # 2. Audio extract
                status["steps"].append({"step": "audio_extract", "status": "started"})
                await save_status(job_id, status)
                audio_path = await downloader.extract_audio(source_path)
                status["steps"][-1]["status"] = "done"
                await save_status(job_id, status)
                # 3. Transcript
                status["steps"].append({"step": "transcript", "status": "started"})
                await save_status(job_id, status)
                transcript_result = await transcript.transcribe(audio_path, job_data)
                status["steps"].append({"lang": transcript_result.get("language"), "avg_confidence": transcript_result.get("avg_confidence")})
                status["steps"][-2]["status"] = "done"
                await save_status(job_id, status)
                # 4. Highlights
                status["steps"].append({"step": "highlights", "status": "started"})
                await save_status(job_id, status)
                highlights = await highlight.detect_highlights(source_path, transcript_result, job_data)
                status["steps"][-1]["status"] = "done"
                await save_status(job_id, status)
                # 5. Reframing
                status["steps"].append({"step": "reframing", "status": "started"})
                await save_status(job_id, status)
                await reframing.process_reframing(source_path, highlights, job_data)
                status["steps"].append({"step": "previews", "status": "started"})
                await save_status(job_id, status)
                await captions.generate_previews(source_path, highlights, job_data)
                status["steps"][-2]["status"] = "done"
                status["steps"][-1]["status"] = "done"
                await save_status(job_id, status)
                # 7. Captions
                status["steps"].append({"step": "captions", "status": "started"})
                await save_status(job_id, status)
                await captions.generate_captions(transcript_result, highlights, job_data)
                status["steps"][-1]["status"] = "done"
                await save_status(job_id, status)
                # 8. Ready
                status["status"] = "ready"
                await save_status(job_id, status)
            except Exception as e:
                status["status"] = "error"
                status["error"] = str(e)
                await save_status(job_id, status)
            self.queue.task_done()

    def start_workers(self):
        for _ in range(self.workers):
            asyncio.create_task(self.worker())

job_queue = JobQueue()
job_queue.start_workers()

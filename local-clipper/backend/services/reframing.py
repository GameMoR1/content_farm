"""
Auto-reframing for 9:16: face/subject detection (MediaPipe/YOLOv8n-face), track, smoothing, crop window, export tracks/{seg_id}.json.
"""
import os
import cv2
import numpy as np
import mediapipe as mp
import json
from typing import List, Dict

MEDIA_WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'media', 'work'))
os.makedirs(MEDIA_WORK, exist_ok=True)

mp_face = mp.solutions.face_detection

async def process_reframing(video_path, highlights, job_data):
    job_id = job_data["job_id"]
    job_dir = os.path.join(MEDIA_WORK, job_id)
    tracks_dir = os.path.join(job_dir, "tracks")
    os.makedirs(tracks_dir, exist_ok=True)
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = total_frames / fps
    for seg in highlights:
        seg_id = seg["id"]
        start, end = seg["start"], seg["end"]
        frames = []
        times = np.arange(start, end, 0.5)
        with mp_face.FaceDetection(model_selection=0, min_detection_confidence=0.5) as face_det:
            for t in times:
                cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
                ret, frame = cap.read()
                if not ret:
                    continue
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = face_det.process(rgb)
                if results.detections:
                    det = results.detections[0]
                    bbox = det.location_data.relative_bounding_box
                    cx = bbox.xmin + bbox.width / 2
                    cy = bbox.ymin + bbox.height / 2
                    size = max(bbox.width, bbox.height)
                else:
                    cx, cy, size = 0.5, 0.5, 0.5
                frames.append({"center_x": cx, "center_y": cy, "zoom": size, "t": t})
        # Сглаживание
        for k in ["center_x", "center_y", "zoom"]:
            arr = np.array([f[k] for f in frames])
            arr = np.convolve(arr, np.ones(3)/3, mode='same')
            for i, f in enumerate(frames):
                f[k] = float(arr[i])
        # Ограничение окна 9:16
        for f in frames:
            f["center_x"] = min(max(f["center_x"], 0.5 - 9/32), 0.5 + 9/32)
            f["center_y"] = min(max(f["center_y"], 0.5 - 0.5/2), 0.5 + 0.5/2)
            f["zoom"] = min(max(f["zoom"], 0.3), 0.8)
        # Экспорт
        out_path = os.path.join(tracks_dir, f"{seg_id}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(frames, f, ensure_ascii=False, indent=2)
    cap.release()

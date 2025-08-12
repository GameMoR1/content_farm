import os
import hashlib
import json
from pytubefix import YouTube

MEDIA_SOURCE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'media', 'source'))
os.makedirs(MEDIA_SOURCE, exist_ok=True)


def update_progress(job_id, progress):
    """Обновление прогресса скачивания в status.json"""
    from ..workers import WORK_DIR
    job_dir = os.path.join(WORK_DIR, job_id)
    status_path = os.path.join(job_dir, "status.json")
    if os.path.exists(status_path):
        try:
            with open(status_path, encoding="utf-8") as f:
                status = json.load(f)
            for step in status.get("steps", []):
                if step.get("step") == "download":
                    step["progress"] = progress
            with open(status_path, "w", encoding="utf-8") as f:
                json.dump(status, f, ensure_ascii=False, indent=2)
        except Exception:
            pass


def download(job_data):
    """
    Скачивает видео с YouTube через pytubefix, выбирает лучший прогрессивный поток mp4 (видео+звук).
    Обрабатывает ошибки (регион, возраст, DRM).
    Возвращает путь к скачанному видео.
    """
    if job_data.get("file_path"):
        return job_data["file_path"]

    url = job_data.get("url")
    job_id = job_data.get("job_id")

    if not url or not isinstance(url, str):
        raise ValueError("URL видео не указан или некорректен")

    sha1 = hashlib.sha1(url.encode()).hexdigest()
    out_path = os.path.join(MEDIA_SOURCE, f"{sha1}.mp4")

    if os.path.exists(out_path):
        if job_id:
            update_progress(job_id, 100)
        return out_path

    def on_progress(stream, chunk, bytes_remaining):
        if not job_id:
            return
        total = stream.filesize or 1
        downloaded = total - bytes_remaining
        percent = int(downloaded * 100 / total)
        if percent > 100:
            percent = 100
        update_progress(job_id, percent)

    try:
        yt = YouTube(url, on_progress_callback=on_progress)

        # Ищем прогрессивный mp4 (видео + аудио)
        video = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()

        # Если нет подходящего прогрессивного, пробуем комбинацию адаптивных (отдельное аудио и видео)
        if not video:
            video = yt.streams.filter(adaptive=True, only_video=True, file_extension='mp4').order_by('resolution').desc().first()
            audio = yt.streams.filter(adaptive=True, only_audio=True, file_extension='mp4').order_by('abr').desc().first()
            if not video or not audio:
                raise RuntimeError("Не найден подходящий поток для скачивания.")
            # Скачиваем отдельно и соединяем с помощью ffmpeg (здесь можно доработать, если нужно)

            # Для простоты пока ошибка, т.к. объединение не реализовано в этом коде
            raise RuntimeError("Найдено только раздельное аудио и видео. Объединение не реализовано.")

        video.download(output_path=MEDIA_SOURCE, filename=f"{sha1}.mp4")

        if job_id:
            update_progress(job_id, 100)

    except Exception as e:
        if job_id:
            update_progress(job_id, 0)
        raise RuntimeError(f"Ошибка при скачивании: {e}")

    if not os.path.exists(out_path):
        raise RuntimeError("Не удалось скачать видео или файл не найден.")

    return out_path


def extract_audio(video_path, sample_rate=16000):
    """
    Извлекает аудио из видео в WAV 16kHz моно для распознавания речи.
    Возвращает путь к аудиофайлу.
    """
    import subprocess

    audio_path = os.path.splitext(video_path)[0] + ".wav"
    if os.path.exists(audio_path):
        return audio_path

    cmd = [
        "ffmpeg", "-y", "-i", video_path,
        "-ac", "1",  # 1 канал (моно)
        "-ar", str(sample_rate),  # частота дискретизации
        "-vn",  # без видео
        audio_path
    ]

    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg error: {proc.stderr.decode(errors='ignore')}")

    return audio_path

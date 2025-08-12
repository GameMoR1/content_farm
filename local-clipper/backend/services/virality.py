"""
Heuristic Virality Score 0–100: keyword density, audio variation, scenes, duration, question/emotion words, readability.
"""
import numpy as np
import nltk
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from typing import List, Dict

def virality_score(segment: Dict, transcript: Dict, audio_features: Dict, scene_count: int) -> Dict:
    # Ключевые слова
    text = " ".join([w["word"] for w in segment.get("words", [])])
    words = nltk.word_tokenize(text)
    unique_words = set(words)
    keyword_density = len(unique_words) / (len(words) + 1e-6)
    # Аудио динамика
    audio_var = float(audio_features.get("rms_var", 0))
    # Количество сцен
    scenes = scene_count
    # Длительность
    duration = segment["end"] - segment["start"]
    # Вопросы/эмо слова
    question = int("?" in text)
    exclaim = int("!" in text)
    # Сентимент
    analyzer = SentimentIntensityAnalyzer()
    sentiment = analyzer.polarity_scores(text)["compound"]
    # Читаемость (упрощенно)
    readability = min(1.0, len(words) / (duration * 2 + 1e-6))
    # Итоговый скор
    score = (
        20 * keyword_density +
        20 * audio_var +
        20 * (scenes / 3) +
        20 * readability +
        10 * (question + exclaim) +
        10 * sentiment
    )
    score = max(0, min(100, int(score)))
    if score < 40:
        color = "red"
    elif score < 70:
        color = "yellow"
    else:
        color = "green"
    return {"score": score, "color": color}

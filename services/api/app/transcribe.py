from functools import lru_cache

from app.segmentation import Word, group_words
from app.settings import settings


@lru_cache(maxsize=1)
def whisper():
    from faster_whisper import WhisperModel

    return WhisperModel(settings.whisper_model, device="cpu", compute_type="int8")


def transcribe_audio(path: str) -> list[dict]:
    segments, _ = whisper().transcribe(path, word_timestamps=True, vad_filter=True, condition_on_previous_text=False)
    words: list[Word] = []
    for segment in segments:
        if segment.words:
            words.extend(Word(word.start, word.end, word.word) for word in segment.words)
        elif segment.text.strip():
            words.append(Word(segment.start, segment.end, segment.text.strip()))
    return group_words(words)


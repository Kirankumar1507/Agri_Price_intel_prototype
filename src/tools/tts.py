"""Text-to-Speech (TTS) using gTTS."""
from gtts import gTTS
import io
import os
from pathlib import Path
import hashlib

CACHE_DIR = Path(".cache/audio")

def get_audio_bytes(text: str, lang: str = "en") -> io.BytesIO:
    """Return an in-memory byte stream of the speech audio."""
    # Language mapping for gTTS
    gtts_lang = "kn" if lang == "kn" else ("hi" if lang == "hi" else "en")
    
    # Cache based on text hash
    text_hash = hashlib.md5(text.encode()).hexdigest()
    cache_path = CACHE_DIR / f"{text_hash}_{gtts_lang}.mp3"
    
    if cache_path.exists():
        with open(cache_path, "rb") as f:
            return io.BytesIO(f.read())

    # Generate
    tts = gTTS(text=text, lang=gtts_lang)
    fp = io.BytesIO()
    tts.write_to_fp(fp)
    fp.seek(0)
    
    # Save to cache
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "wb") as f:
        f.write(fp.getvalue())
        
    fp.seek(0)
    return fp

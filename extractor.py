import os
import json
import time
import hashlib
from pathlib import Path

from dotenv import load_dotenv

from prompt import SYSTEM_PROMPT, PROMPT_VERSION
from schema import Extraction

load_dotenv()  # đọc GEMINI_API_KEY / GEMINI_MODEL từ file .env (không commit)
CACHE_DIR = Path(__file__).parent / "cache"
DEFAULT_MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash")


class NoApiKey(Exception):
    pass


def _key(transcript: str, model: str) -> str:
    return hashlib.sha256((PROMPT_VERSION + model + transcript).encode("utf-8")).hexdigest()[:24]


def extract(transcript: str, api_key: str | None = None, model: str | None = None, use_cache: bool = True) -> dict:
    """Một lần gọi model cho mỗi cuộc họp. Kết quả được cache để tiết kiệm hạn mức free tier."""
    model = model or DEFAULT_MODEL
    CACHE_DIR.mkdir(exist_ok=True)
    path = CACHE_DIR / f"{_key(transcript, model)}.json"
    if use_cache and path.exists():
        return json.loads(path.read_text(encoding="utf-8"))

    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise NoApiKey("Chưa có GEMINI_API_KEY và kết quả chưa có trong cache.")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    last = None
    for attempt in range(3):
        try:
            resp = client.models.generate_content(
                model=model,
                contents="TRANSCRIPT:\n" + transcript,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=Extraction,
                    temperature=0,
                ),
            )
            data = json.loads(resp.text)
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return data
        except Exception as e:  # 429 / lỗi mạng: chờ rồi thử lại
            last = e
            time.sleep(15 * (attempt + 1))
    raise RuntimeError(f"Gọi model thất bại: {last}")

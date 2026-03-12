"""
Gemini AI client — async-first, non-blocking.
Uses asyncio.to_thread() so Gemini's synchronous SDK
doesn't freeze the Telegram bot event loop.
"""

import asyncio
import time
from collections import deque
from threading import Lock
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
import logging
from config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_FALLBACK_MODEL,
    GEMINI_MAX_CALLS_PER_MINUTE,
)

logger = logging.getLogger(__name__)

genai.configure(api_key=GEMINI_API_KEY)

_model_cache = {}
_rate_lock = Lock()
_request_times = deque()


class GeminiQuotaError(Exception):
    """Raised when Gemini rejects a request due to quota/rate limits."""


class GeminiAPIError(Exception):
    """Raised for other Gemini API failures."""


def _get_model(model_name: str):
    if not model_name:
        return None
    if model_name not in _model_cache:
        _model_cache[model_name] = genai.GenerativeModel(model_name)
    return _model_cache[model_name]


def _throttle():
    """Rate limiter — runs in thread pool, safe to use time.sleep here."""
    if GEMINI_MAX_CALLS_PER_MINUTE <= 0:
        return

    while True:
        with _rate_lock:
            now = time.time()
            while _request_times and now - _request_times[0] > 60:
                _request_times.popleft()

            if len(_request_times) < GEMINI_MAX_CALLS_PER_MINUTE:
                _request_times.append(now)
                return

            wait_for = max(0.05, 60 - (now - _request_times[0]))

        time.sleep(wait_for)


def _generate_sync(parts):
    """Synchronous Gemini call — runs inside a thread via asyncio.to_thread()."""
    models_to_try = []
    if GEMINI_MODEL:
        models_to_try.append(GEMINI_MODEL)
    if GEMINI_FALLBACK_MODEL and GEMINI_FALLBACK_MODEL not in models_to_try:
        models_to_try.append(GEMINI_FALLBACK_MODEL)

    last_quota_error = None
    last_api_error = None

    for model_name in models_to_try:
        model = _get_model(model_name)
        try:
            _throttle()
            response = model.generate_content(parts)
            text = getattr(response, "text", None)
            if not text and getattr(response, "candidates", None):
                fragments = []
                for candidate in response.candidates:
                    if not getattr(candidate, "content", None):
                        continue
                    for part in candidate.content.parts:
                        if getattr(part, "text", None):
                            fragments.append(part.text)
                text = "\n".join(fragments).strip() if fragments else None

            if not text:
                raise GeminiAPIError("Gemini returned an empty response.")
            return text
        except google_exceptions.ResourceExhausted as exc:
            last_quota_error = exc
            continue
        except google_exceptions.GoogleAPIError as exc:
            logger.warning(
                "Gemini API error using model %s: %s", model_name, exc.message
            )
            last_api_error = exc
            continue
        except (GeminiAPIError, GeminiQuotaError):
            raise
        except Exception as exc:
            raise GeminiAPIError(str(exc)) from exc

    if last_quota_error:
        raise GeminiQuotaError(
            "Gemini quota exceeded. Please wait a few seconds and try again."
        ) from last_quota_error

    if last_api_error:
        raise GeminiAPIError(str(last_api_error)) from last_api_error

    raise GeminiAPIError("Gemini failed for an unknown reason.")


# ── Sync wrappers (keep for backward compat) ──

def generate_text(prompt):
    """Generate text response from Gemini (sync — blocks event loop!)"""
    return _generate_sync(prompt)


def generate_with_image(prompt, image):
    """Generate response with image input (sync)"""
    return _generate_sync([prompt, image])


def generate_with_audio(prompt, audio_bytes, mime_type: str = "audio/ogg"):
    """Generate response with audio input (sync)"""
    audio_part = {"mime_type": mime_type, "data": audio_bytes}
    return _generate_sync([prompt, audio_part])


# ── ASYNC wrappers (non-blocking — use these!) ──

async def agenerate_text(prompt):
    """Generate text response from Gemini (async, non-blocking)."""
    return await asyncio.to_thread(_generate_sync, prompt)


async def agenerate_with_image(prompt, image):
    """Generate response with image input (async, non-blocking)."""
    return await asyncio.to_thread(_generate_sync, [prompt, image])


async def agenerate_with_audio(prompt, audio_bytes, mime_type: str = "audio/ogg"):
    """Generate response with audio input (async, non-blocking)."""
    audio_part = {"mime_type": mime_type, "data": audio_bytes}
    return await asyncio.to_thread(_generate_sync, [prompt, audio_part])
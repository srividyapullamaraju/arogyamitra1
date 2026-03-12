from PIL import Image
import io


def split_message(text, max_length=4000):
    """Split long messages into chunks"""
    if len(text) <= max_length:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_length:
            chunks.append(text)
            break

        split_pos = text.rfind('\n', 0, max_length)
        if split_pos == -1:
            split_pos = text.rfind(' ', 0, max_length)
        if split_pos == -1:
            split_pos = max_length

        chunks.append(text[:split_pos])
        text = text[split_pos:].lstrip()

    return chunks


async def download_photo(photo):
    """Download photo from Telegram and convert to PIL Image"""
    photo_file = await photo.get_file()
    photo_bytes = await photo_file.download_as_bytearray()
    return Image.open(io.BytesIO(photo_bytes))


async def download_document_image(document):
    """Download an image sent as a Telegram document and convert to PIL Image."""
    doc_file = await document.get_file()
    doc_bytes = await doc_file.download_as_bytearray()
    return Image.open(io.BytesIO(doc_bytes))


async def download_audio_bytes(file):
    """
    Download a Telegram voice/audio file and return its raw bytes.

    This works for both voice notes (update.message.voice) and audio files
    (update.message.audio).
    """
    tg_file = await file.get_file()
    data = await tg_file.download_as_bytearray()
    # Gemini expects a bytes-like object, not a bytearray
    return bytes(data)
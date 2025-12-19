import logging
import io
from google import genai
from google.genai import types
from bot.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

async def transcribe_voice(bot, file_id: str) -> str:
    if not GEMINI_API_KEY:
        logger.error("Gemini API Key is missing!")
        return ""

    try:
        # Downloading the file into memory
        file_io = io.BytesIO()
        file_info = await bot.get_file(file_id)
        await bot.download_file(file_info.file_path, destination=file_io)
        file_bytes = file_io.getvalue()

        client = genai.Client(api_key=GEMINI_API_KEY)

        parts = [
            types.Part(text="Transcribe this audio to text exactly as spoken. Do not add any markdown or explanations."),
            types.Part(inline_data=types.Blob(
                data=file_bytes, 
                mime_type="audio/ogg"
            ))
        ]

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=parts
        )
        
        text = response.text.strip() if response.text else ""
        logger.info(f"Gemini transcription: {text}")
        return text

    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return ""
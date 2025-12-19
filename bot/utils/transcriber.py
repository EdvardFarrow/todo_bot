import logging
import io
import google.generativeai as genai
from config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

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

        model = genai.GenerativeModel("gemini-2.5-flash")

        # prompt + audio
        response = model.generate_content([
            "Transcribe this audio to text exactly as spoken. Do not add any markdown or explanations.",
            {
                "mime_type": "audio/ogg",
                "data": file_bytes
            }
        ])
        
        text = response.text.strip()
        logger.info(f"Gemini transcription: {text}")
        return text

    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return ""
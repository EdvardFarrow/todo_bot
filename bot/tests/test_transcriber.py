from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from bot.utils.transcriber import transcribe_voice


# Successful transcription
@pytest.mark.asyncio
async def test_transcribe_voice_success():
    bot_mock = AsyncMock()
    file_info_mock = MagicMock()
    file_info_mock.file_path = "voice/test_audio.ogg"
    bot_mock.get_file.return_value = file_info_mock

    async def download_side_effect(file_path, destination):
        destination.write(b"fake_audio_content")

    bot_mock.download_file.side_effect = download_side_effect

    with patch("bot.utils.transcriber.genai.Client") as MockClient:
        client_instance = MockClient.return_value

        response_mock = MagicMock()
        response_mock.text = "Hello world"
        client_instance.models.generate_content.return_value = response_mock

        with patch("bot.utils.transcriber.GEMINI_API_KEY", "fake_key"):
            result = await transcribe_voice(bot_mock, "file_123")

    assert result == "Hello world"
    MockClient.assert_called_with(api_key="fake_key")


# Missing API Key
@pytest.mark.asyncio
async def test_transcribe_no_api_key():
    bot_mock = AsyncMock()

    with patch("bot.utils.transcriber.GEMINI_API_KEY", None):
        result = await transcribe_voice(bot_mock, "file_123")

    assert result == ""
    bot_mock.get_file.assert_not_awaited()


# Google API Error
@pytest.mark.asyncio
async def test_transcribe_genai_error():
    bot_mock = AsyncMock()
    bot_mock.get_file.return_value = MagicMock(file_path="path")

    with patch("bot.utils.transcriber.genai.Client") as MockClient:
        client_instance = MockClient.return_value
        client_instance.models.generate_content.side_effect = Exception("API Error")

        with patch("bot.utils.transcriber.GEMINI_API_KEY", "fake_key"):
            result = await transcribe_voice(bot_mock, "file_123")

    assert result == ""

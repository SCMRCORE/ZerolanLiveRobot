import base64
import os
from typing import Generator

from loguru import logger
from openai import OpenAI
from typeguard import typechecked
from zerolan.data.pipeline.asr import ASRQuery, ASRPrediction, ASRStreamQuery

from common.io.api import save_audio
from common.io.file_type import AudioFileType


class XiaomiASRPipeline:

    def __init__(self, api_key: str, base_url: str, model: str = "mimo-v2.5"):
        """
        Initialize Xiaomi ASR Pipeline using audio understanding capability.
        :param api_key: The API key for Xiaomi service.
        :param base_url: The base URL for Xiaomi API.
        :param model: The model ID for Xiaomi audio understanding (mimo-v2.5 or mimo-v2-omni).
        """
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model = model
        logger.info(f"[XiaomiASR] Initialized with model={model}, base_url={base_url}")

    @typechecked
    def predict(self, query: ASRQuery) -> ASRPrediction:
        """
        Transcribe audio using Xiaomi's audio understanding capability.
        :param query: ASR query containing audio path and metadata.
        :return: ASR prediction with transcript.
        """
        assert os.path.exists(query.audio_path), f"{query.audio_path} does not exist!"

        logger.info(f"[XiaomiASR] Processing audio: {query.audio_path}")
        audio_base64 = self._encode_audio(query.audio_path)
        mime_type = self._get_mime_type(query.media_type)
        audio_data = f"data:{mime_type};base64,{audio_base64}"

        logger.debug(f"[XiaomiASR] Audio size: {len(audio_base64)} bytes (base64)")

        completion = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_data
                            }
                        },
                        {
                            "type": "text",
                            "text": "请将这段音频的内容转录为文字，只输出转录结果，不要添加任何解释或评论。"
                        }
                    ]
                }
            ]
        )

        transcript = completion.choices[0].message.content or ""
        logger.info(f"[XiaomiASR] Transcription result: {transcript.strip()}")
        return ASRPrediction(transcript=transcript.strip())

    def stream_predict(self, query: ASRStreamQuery, chunk_size: int | None = None) -> Generator[
        ASRPrediction, None, None]:
        """
        Stream predict using Xiaomi audio understanding.
        :param query: ASR stream query containing audio data.
        :param chunk_size: Not used for Xiaomi API.
        :return: Generator yielding ASR prediction.
        """
        audio_path = save_audio(query.audio_data, AudioFileType.WAV, prefix="asr")
        yield self.predict(ASRQuery(
            audio_path=str(audio_path),
            media_type=query.media_type,
            sample_rate=query.sample_rate,
            channels=query.channels,
        ))

    @staticmethod
    def _encode_audio(audio_path: str) -> str:
        """
        Encode audio file to base64 string.
        :param audio_path: Path to audio file.
        :return: Base64 encoded string.
        """
        with open(audio_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')

    @staticmethod
    def _get_mime_type(media_type: str) -> str:
        """
        Map media type to MIME type.
        :param media_type: Audio file format (wav, mp3, etc.)
        :return: MIME type
        """
        type_map = {
            "wav": "audio/wav",
            "mp3": "audio/mpeg",
            "flac": "audio/flac",
            "m4a": "audio/mp4",
            "ogg": "audio/ogg",
        }
        return type_map.get(media_type.lower(), "audio/wav")

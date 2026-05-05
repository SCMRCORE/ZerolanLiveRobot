import base64
import os.path
import uuid
from http import HTTPStatus

import requests
from loguru import logger
from openai import OpenAI
from zerolan.data.pipeline.tts import TTSQuery, TTSPrediction, TTSStreamPrediction

from pipeline.base.base_sync import CommonModelPipeline
from pipeline.tts.baidu_tts import BaiduTTSPipeline
from pipeline.tts.config import TTSPipelineConfig, TTSModelIdEnum


class XiaomiTTSPipeline:
    def __init__(self, api_key: str, base_url: str, model_id: str, voice: str = "mimo_default"):
        self._client = OpenAI(api_key=api_key, base_url=base_url)
        self._model_id = model_id
        self._voice = voice
        logger.info(f"[XiaomiTTS] Initialized with model={model_id}, voice={voice}, base_url={base_url}")

    def predict(self, query: TTSQuery) -> TTSPrediction | None:
        audio_format = query.audio_type if query.audio_type else "wav"
        logger.info(f"[XiaomiTTS] Synthesizing: {query.text[:50]}..." if len(query.text) > 50 else f"[XiaomiTTS] Synthesizing: {query.text}")
        completion = self._client.chat.completions.create(
            model=self._model_id,
            messages=[
                {
                    "role": "assistant",
                    "content": query.text
                }
            ],
            audio={
                "format": audio_format,
                "voice": self._voice
            }
        )
        message = completion.choices[0].message
        audio_bytes = base64.b64decode(message.audio.data)
        logger.info(f"[XiaomiTTS] Audio generated: {len(audio_bytes)} bytes")
        return TTSPrediction(wave_data=audio_bytes, audio_type=audio_format)

    def stream_predict(self, query: TTSQuery, chunk_size: int | None = None):
        audio_format = "pcm16"
        completion = self._client.chat.completions.create(
            model=self._model_id,
            messages=[
                {
                    "role": "assistant",
                    "content": query.text
                }
            ],
            audio={
                "format": audio_format,
                "voice": self._voice
            },
            stream=True
        )
        idx = 0
        stream_id = str(uuid.uuid4())
        for chunk in completion:
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            audio = getattr(delta, "audio", None)
            if audio is not None:
                pcm_bytes = base64.b64decode(audio["data"])
                yield TTSStreamPrediction(
                    seq=idx,
                    id=stream_id,
                    is_final=False,
                    wave_data=pcm_bytes,
                    audio_type=audio_format
                )
                idx += 1
        yield TTSStreamPrediction(is_final=True, seq=idx + 1, audio_type=audio_format, wave_data=b'')


class TTSSyncPipeline(CommonModelPipeline):

    def __init__(self, config: TTSPipelineConfig):
        super().__init__(config)
        xiaomi_models = (
            TTSModelIdEnum.XiaomiMimoV2TTS,
            TTSModelIdEnum.XiaomiMimoV25TTS,
            TTSModelIdEnum.XiaomiMimoV25TTSVoiceClone,
            TTSModelIdEnum.XiaomiMimoV25TTSVoiceDesign
        )
        if config.model_id == TTSModelIdEnum.BaiduTTS and config.baidu_tts_config is not None:
            self.baidu = BaiduTTSPipeline(api_key=config.baidu_tts_config.api_key,
                                          secret_key=config.baidu_tts_config.secret_key)
            self.predict = self.baidu.predict
            self.stream_predict = self.baidu.stream_predict
        elif config.model_id in xiaomi_models and config.xiaomi_tts_config is not None:
            self.xiaomi = XiaomiTTSPipeline(
                api_key=config.xiaomi_tts_config.api_key,
                base_url=config.xiaomi_tts_config.base_url,
                model_id=config.model_id,
                voice=config.xiaomi_tts_config.voice
            )
            self.predict = self.xiaomi.predict
            self.stream_predict = self.xiaomi.stream_predict

    def predict(self, query: TTSQuery) -> TTSPrediction | None:
        assert isinstance(query, TTSQuery)
        if os.path.exists(query.refer_wav_path):
            query.refer_wav_path = os.path.abspath(query.refer_wav_path).replace("\\", "/")
        query_dict = self.parse_query(query)
        response = requests.post(url=self.predict_url, stream=True, json=query_dict)
        if response.status_code == HTTPStatus.OK:
            prediction = TTSPrediction(wave_data=response.content, audio_type=query.audio_type)
            return prediction
        else:
            logger.error(response.content)
            response.raise_for_status()

    def stream_predict(self, query: TTSQuery, chunk_size: int | None = None):
        assert isinstance(query, TTSQuery)
        if os.path.exists(query.refer_wav_path):
            query.refer_wav_path = os.path.abspath(query.refer_wav_path).replace("\\", "/")
        query_dict = self.parse_query(query)
        response = requests.post(url=self.stream_predict_url, stream=True,
                                 json=query_dict)
        response.raise_for_status()
        last = 0
        id = str(uuid.uuid4())
        for idx, chunk in enumerate(response.iter_content(chunk_size=1024)):
            last = idx
            yield TTSStreamPrediction(seq=idx,
                                      id=id,
                                      is_final=False,
                                      wave_data=chunk,
                                      audio_type=query.audio_type)
        yield TTSStreamPrediction(is_final=True, seq=last + 1, audio_type=query.audio_type, wave_data=b'')

    def parse_query(self, query: any) -> dict:
        return super().parse_query(query)

from pydantic import Field, BaseModel

from common.enumerator import BaseEnum
from common.utils.enum_util import enum_to_markdown
from pipeline.base.base_sync import AbstractPipelineConfig


#######
# ASR #
#######

class AudioFormatEnum(BaseEnum):
    Float32: str = "float32"


class ASRModelIdEnum(BaseEnum):
    Paraformer = "iic/speech_paraformer_asr_nat-zh-cn-16k-common-vocab8358-tensorflow1"
    KotobaWhisper = 'kotoba-tech/kotoba-whisper-v2.0'
    BaiduASR = "BaiduASR"
    WhisperASR = "WhisperASR"
    XiaomiMimoASR = "mimo-v2.5"


class BaiduASRConfig(BaseModel):
    api_key: str = Field(default="", description="The API key for Baidu ASR service.")
    secret_key: str = Field(default="", description="The secret key for Baidu ASR service.")


class WhisperASRConfig(BaseModel):
    api_key: str = Field(default="", description="The API key for OpenAI/Whisper ASR service.")
    api_url: str = Field(default="https://api.openai.com/v1/audio/transcriptions",
                         description="The API URL for Whisper ASR service. Default: https://api.openai.com/v1/audio/transcriptions")
    model: str = Field(default="whisper-1", description="The model ID to use. Currently only whisper-1 is available.")
    language: str | None = Field(default=None, description="The language of the input audio. ISO-639-1 format. Optional but improves accuracy.")
    prompt: str | None = Field(default=None, description="Optional text to guide the model's style or continue a previous audio segment.")
    temperature: float = Field(default=0.0, description="Sampling temperature between 0 and 1. Higher values make output more random.")
    response_format: str = Field(default="json", description="The format of the transcript output. Options: json, text, srt, verbose_json, vtt")


class XiaomiASRConfig(BaseModel):
    api_key: str = Field(default="", description="The API key for Xiaomi ASR service.")
    base_url: str = Field(default="https://api.xiaomimimo.com/v1", description="The base URL for Xiaomi API.")
    model: str = Field(default="mimo-v2.5", description="The model ID for Xiaomi audio understanding.")


class ASRPipelineConfig(AbstractPipelineConfig):
    sample_rate: int = Field(16000, description="The sample rate for audio input.")
    channels: int = Field(1, description="The number of audio channels.")
    format: AudioFormatEnum = Field(AudioFormatEnum.Float32,
                                    description=f"The format of the audio data. {enum_to_markdown(AudioFormatEnum)}")
    model_id: ASRModelIdEnum = Field(default=ASRModelIdEnum.Paraformer,
                                     description=f"The ID of the model used for ASR. \n{enum_to_markdown(ASRModelIdEnum)}")
    predict_url: str = Field(default="http://127.0.0.1:11000/asr/predict",
                             description="The URL for ASR prediction requests.")
    stream_predict_url: str = Field(default="http://127.0.0.1:11000/asr/stream-predict",
                                    description="The URL for streaming ASR prediction requests.")
    baidu_asr_config: BaiduASRConfig = Field(default=BaiduASRConfig(), description="Baidu ASR config."
                                                                                   f"Only edit it when you set `model_id` to `{ASRModelIdEnum.BaiduASR.value}`.\n"
                                                                                   f"For more details please see the [documents](https://cloud.baidu.com/doc/SPEECH/s/qlcirqhz0).")
    whisper_asr_config: WhisperASRConfig = Field(default=WhisperASRConfig(), description="Whisper ASR config. "
                                                                                        f"Only edit it when you set `model_id` to `{ASRModelIdEnum.WhisperASR.value}`.\n"
                                                                                        f"For more details please see the [documents](https://zhizengzeng.com/docs/audio).")
    xiaomi_asr_config: XiaomiASRConfig = Field(default=XiaomiASRConfig(), description="Xiaomi ASR config. "
                                                                                     f"Only edit it when you set `model_id` to `{ASRModelIdEnum.XiaomiMimoASR.value}`.\n"
                                                                                     f"Uses Xiaomi's audio understanding capability for transcription.")

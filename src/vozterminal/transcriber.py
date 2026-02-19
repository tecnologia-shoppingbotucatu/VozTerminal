"""Transcrição de áudio via Groq API (primário) e OpenAI Whisper (fallback)."""

import io
import wave
import logging

logger = logging.getLogger("vozterminal.transcriber")

GROQ_MODEL = "whisper-large-v3-turbo"
OPENAI_MODEL = "whisper-1"


def pcm_to_wav(pcm_data: bytes, sample_rate: int = 16000) -> io.BytesIO:
    """Converte PCM 16-bit mono para WAV em memória."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    buf.seek(0)
    buf.name = "audio.wav"  # APIs precisam de extensão no nome
    return buf


class Transcriber:
    """Transcreve áudio usando Groq API com fallback para OpenAI."""

    def __init__(
        self,
        groq_api_key: str | None = None,
        openai_api_key: str | None = None,
        language: str = "pt",
        prompt_hint: str = "",
    ):
        self._groq = None
        self._openai = None
        self._language = language
        self._prompt_hint = prompt_hint

        if groq_api_key:
            from groq import Groq
            self._groq = Groq(api_key=groq_api_key)

        if openai_api_key:
            from openai import OpenAI
            self._openai = OpenAI(api_key=openai_api_key)

        if not self._groq and not self._openai:
            raise ValueError("Pelo menos uma API key (Groq ou OpenAI) deve ser configurada.")

    def transcribe(self, pcm_data: bytes) -> str | None:
        """
        Transcreve áudio PCM. Tenta Groq primeiro, depois OpenAI.

        Returns:
            Texto transcrito ou None se falhar/vazio.
        """
        wav_buf = pcm_to_wav(pcm_data)

        if self._groq:
            try:
                result = self._transcribe_groq(wav_buf)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Groq falhou: {e}")
                wav_buf.seek(0)

        if self._openai:
            try:
                result = self._transcribe_openai(wav_buf)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"OpenAI falhou: {e}")

        logger.error("Todas as APIs de transcrição falharam.")
        return None

    def _transcribe_groq(self, wav_buf: io.BytesIO) -> str | None:
        transcription = self._groq.audio.transcriptions.create(
            file=wav_buf,
            model=GROQ_MODEL,
            language=self._language,
            response_format="text",
            temperature=0.0,
            prompt=self._prompt_hint or None,
        )
        text = transcription.strip() if isinstance(transcription, str) else transcription.text.strip()
        return text if text else None

    def _transcribe_openai(self, wav_buf: io.BytesIO) -> str | None:
        transcription = self._openai.audio.transcriptions.create(
            file=wav_buf,
            model=OPENAI_MODEL,
            language=self._language,
            response_format="text",
            temperature=0.0,
            prompt=self._prompt_hint or None,
        )
        text = transcription.strip() if isinstance(transcription, str) else transcription.text.strip()
        return text if text else None

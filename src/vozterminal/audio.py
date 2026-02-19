"""Captura de áudio do microfone com detecção de atividade de voz (VAD).

Usa janela deslizante (sliding window) conforme padrão oficial do webrtcvad:
- Trigger: 90% dos frames na janela são fala → inicia gravação
- Detrigger: 90% dos frames na janela são silêncio → para gravação
Isso elimina falsos positivos de ruído de fundo.
"""

import array
import collections
import logging
import math
import threading

import pyaudio
import webrtcvad

logger = logging.getLogger("vozterminal.audio")

# Constantes de áudio compatíveis com webrtcvad
SAMPLE_RATE = 16000
FRAME_DURATION_MS = 30
FRAME_SIZE = int(SAMPLE_RATE * FRAME_DURATION_MS / 1000)  # 480 samples

# Parâmetros de VAD
PADDING_DURATION_MS = 300  # janela deslizante para trigger/detrigger
MAX_SEGMENT_SECONDS = 15
MIN_SEGMENT_SECONDS = 1.0

# Energia mínima (RMS) para considerar fala real
MIN_RMS_THRESHOLD = 500

# Derivados
NUM_PADDING_FRAMES = int(PADDING_DURATION_MS / FRAME_DURATION_MS)  # 10 frames
MAX_FRAMES = int(MAX_SEGMENT_SECONDS * 1000 / FRAME_DURATION_MS)
MIN_FRAMES = int(MIN_SEGMENT_SECONDS * 1000 / FRAME_DURATION_MS)

# Proporção de frames voiced/unvoiced para trigger/detrigger
TRIGGER_RATIO = 0.9   # 90% voiced para começar a gravar
DETRIGGER_RATIO = 0.9  # 90% unvoiced para parar de gravar


def _compute_rms(pcm_data: bytes) -> float:
    """Calcula RMS (Root Mean Square) do áudio PCM 16-bit."""
    if len(pcm_data) < 2:
        return 0.0
    samples = array.array("h", pcm_data)
    sum_squares = sum(s * s for s in samples)
    return math.sqrt(sum_squares / len(samples))


class AudioCapture:
    """Captura áudio e emite segmentos usando janela deslizante do webrtcvad."""

    def __init__(
        self,
        on_segment: callable,
        vad_aggressiveness: int = 3,
        silence_threshold_ms: int = 1000,
        device_index: int | None = None,
        min_rms: float = MIN_RMS_THRESHOLD,
    ):
        self._on_segment = on_segment
        self._device_index = device_index
        self._vad = webrtcvad.Vad(vad_aggressiveness)
        self._min_rms = min_rms
        self._pa: pyaudio.PyAudio | None = None
        self._stream: pyaudio.Stream | None = None
        self._is_recording = False
        self._lock = threading.Lock()

        # Janela deslizante: (frame_bytes, is_speech)
        self._ring_buffer: collections.deque = collections.deque(maxlen=NUM_PADDING_FRAMES)
        # Buffer de segmento com fala
        self._voiced_frames: list[bytes] = []
        # Estado: triggered = estamos gravando fala
        self._triggered = False

    def start(self) -> None:
        """Inicia captura de áudio."""
        with self._lock:
            if self._is_recording:
                return
            self._pa = pyaudio.PyAudio()
            self._stream = self._pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=SAMPLE_RATE,
                input=True,
                input_device_index=self._device_index,
                frames_per_buffer=FRAME_SIZE,
                stream_callback=self._audio_callback,
            )
            self._is_recording = True
            self._reset_state()
            self._stream.start_stream()
            logger.info("Captura de áudio iniciada")

    def stop(self) -> None:
        """Para captura. Envia segmento pendente se houver."""
        with self._lock:
            if not self._is_recording:
                return
            self._is_recording = False
            if self._voiced_frames and len(self._voiced_frames) >= MIN_FRAMES:
                self._emit_segment()
            if self._stream:
                self._stream.stop_stream()
                self._stream.close()
                self._stream = None
            if self._pa:
                self._pa.terminate()
                self._pa = None
            logger.info("Captura de áudio parada")

    def _audio_callback(self, in_data: bytes, frame_count, time_info, status) -> tuple:
        """Callback do PyAudio com janela deslizante para trigger/detrigger."""
        if not self._is_recording:
            return (None, pyaudio.paComplete)

        try:
            is_speech = self._vad.is_speech(in_data, SAMPLE_RATE)
        except Exception:
            return (None, pyaudio.paContinue)

        if not self._triggered:
            # Ainda não estamos gravando. Acumula na janela deslizante.
            self._ring_buffer.append((in_data, is_speech))
            num_voiced = sum(1 for _, speech in self._ring_buffer if speech)

            # Trigger: 90% dos frames na janela são fala
            if num_voiced > TRIGGER_RATIO * self._ring_buffer.maxlen:
                self._triggered = True
                # Inclui todos os frames da janela como início do segmento
                for frame, _ in self._ring_buffer:
                    self._voiced_frames.append(frame)
                self._ring_buffer.clear()
        else:
            # Estamos gravando fala
            self._voiced_frames.append(in_data)
            self._ring_buffer.append((in_data, is_speech))
            num_unvoiced = sum(1 for _, speech in self._ring_buffer if not speech)

            # Detrigger: 90% dos frames na janela são silêncio
            if num_unvoiced > DETRIGGER_RATIO * self._ring_buffer.maxlen:
                self._triggered = False
                if len(self._voiced_frames) >= MIN_FRAMES:
                    self._emit_segment()
                self._reset_state()

            # Segurança: força envio se segmento muito longo
            elif len(self._voiced_frames) >= MAX_FRAMES:
                self._emit_segment()
                self._reset_state()

        return (None, pyaudio.paContinue)

    def _emit_segment(self) -> None:
        """Concatena frames, verifica energia mínima, e chama callback."""
        pcm_data = b"".join(self._voiced_frames)
        duration = len(pcm_data) / (SAMPLE_RATE * 2)

        # Filtro de energia: rejeita segmentos com volume muito baixo
        rms = _compute_rms(pcm_data)
        if rms < self._min_rms:
            logger.debug(f"Segmento descartado por RMS baixo ({rms:.0f} < {self._min_rms}): {duration:.1f}s")
            return

        logger.info(f"Segmento emitido: {duration:.1f}s, RMS={rms:.0f}")
        threading.Thread(
            target=self._on_segment,
            args=(pcm_data,),
            daemon=True,
        ).start()

    def _reset_state(self) -> None:
        self._voiced_frames = []
        self._ring_buffer.clear()
        self._triggered = False

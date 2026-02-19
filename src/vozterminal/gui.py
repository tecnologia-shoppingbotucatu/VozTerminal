"""Interface gráfica do VozTerminal usando CustomTkinter."""

import logging
import threading
import sys

import customtkinter as ctk

from vozterminal import __version__
from vozterminal.config import Config, CONFIG_DIR, CONFIG_FILE

logger = logging.getLogger("vozterminal.gui")


def _get_audio_devices() -> list[tuple[int, str]]:
    """Lista dispositivos de entrada de áudio disponíveis."""
    try:
        import pyaudio
        pa = pyaudio.PyAudio()
        devices = []
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if info["maxInputChannels"] > 0:
                devices.append((i, info["name"]))
        pa.terminate()
        return devices
    except Exception:
        return []


class VozTerminalGUI(ctk.CTk):
    """Janela principal do VozTerminal."""

    def __init__(self):
        super().__init__()

        # Configuração da janela
        self.title("VozTerminal")
        self.geometry("720x580")
        self.minsize(600, 500)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Estado
        self._config = Config.load()
        self._config.ensure_dirs()
        self._daemon = None
        self._is_dictating = False
        self._log_handler = None

        # Construir interface
        self._create_header()
        self._create_tabs()

        # Hotkey global F9 funciona mesmo sem clicar no botão
        self._global_hotkey = None
        self._start_global_hotkey()

        # Ao fechar a janela
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _start_global_hotkey(self):
        """Registra hotkey global que funciona como o botão Iniciar/Parar."""
        from vozterminal.hotkey import HotkeyListener
        self._global_hotkey = HotkeyListener(
            hotkey_str=self._config.hotkey,
            on_activate=lambda: self.after(0, self._toggle_dictation),
        )
        self._global_hotkey.start()

    # ── Header ──────────────────────────────────────────────

    def _create_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=15, pady=(15, 5))

        ctk.CTkLabel(
            header,
            text="VozTerminal",
            font=ctk.CTkFont(size=24, weight="bold"),
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text=f"v{__version__}",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        ).pack(side="left", padx=(8, 0), pady=(8, 0))

    # ── Tabs ────────────────────────────────────────────────

    def _create_tabs(self):
        self._tabview = ctk.CTkTabview(self, width=690, height=480)
        self._tabview.pack(fill="both", expand=True, padx=15, pady=(5, 15))

        self._tabview.add("Ditado")
        self._tabview.add("Configurações")
        self._tabview.add("Sobre")

        self._tabview.set("Ditado")

        self._build_dictation_tab()
        self._build_settings_tab()
        self._build_about_tab()

    # ── Aba Ditado ──────────────────────────────────────────

    def _build_dictation_tab(self):
        tab = self._tabview.tab("Ditado")
        tab.grid_columnconfigure(0, weight=1)

        # Status
        self._status_frame = ctk.CTkFrame(tab)
        self._status_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        self._status_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self._status_frame,
            text="Status:",
            font=ctk.CTkFont(size=14, weight="bold"),
        ).grid(row=0, column=0, padx=10, pady=10)

        self._status_label = ctk.CTkLabel(
            self._status_frame,
            text="Parado",
            font=ctk.CTkFont(size=14),
            text_color="#ff6b6b",
        )
        self._status_label.grid(row=0, column=1, padx=5, pady=10, sticky="w")

        self._hotkey_label = ctk.CTkLabel(
            self._status_frame,
            text=f"Hotkey: {self._config.hotkey.upper()}",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self._hotkey_label.grid(row=0, column=2, padx=10, pady=10)

        # Botão toggle
        self._toggle_btn = ctk.CTkButton(
            tab,
            text="Iniciar Ditado",
            font=ctk.CTkFont(size=18, weight="bold"),
            height=60,
            fg_color="#2ecc71",
            hover_color="#27ae60",
            command=self._toggle_dictation,
        )
        self._toggle_btn.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        # Log de transcrições
        ctk.CTkLabel(
            tab,
            text="Log de Transcrições:",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
        ).grid(row=2, column=0, sticky="w", padx=12, pady=(10, 2))

        self._log_text = ctk.CTkTextbox(
            tab,
            height=250,
            font=ctk.CTkFont(family="monospace", size=12),
            state="disabled",
        )
        self._log_text.grid(row=3, column=0, sticky="nsew", padx=10, pady=(0, 10))
        tab.grid_rowconfigure(3, weight=1)

        # Botão limpar log
        ctk.CTkButton(
            tab,
            text="Limpar Log",
            width=120,
            fg_color="gray",
            hover_color="#555",
            command=self._clear_log,
        ).grid(row=4, column=0, sticky="e", padx=10, pady=(0, 10))

    # ── Aba Configurações ───────────────────────────────────

    def _build_settings_tab(self):
        tab = self._tabview.tab("Configurações")

        # Scrollable frame para todas as configurações
        scroll = ctk.CTkScrollableFrame(tab, width=650)
        scroll.pack(fill="both", expand=True, padx=5, pady=5)
        scroll.grid_columnconfigure(1, weight=1)

        row = 0

        # ── Seção: API Keys ──
        ctk.CTkLabel(
            scroll,
            text="API Keys",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=row, column=0, columnspan=3, sticky="w", padx=10, pady=(10, 5))
        row += 1

        # Groq API Key
        ctk.CTkLabel(scroll, text="Groq API Key:").grid(
            row=row, column=0, sticky="w", padx=10, pady=5
        )
        self._groq_key_entry = ctk.CTkEntry(scroll, show="*", width=350)
        self._groq_key_entry.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        if self._config.groq_api_key:
            self._groq_key_entry.insert(0, self._config.groq_api_key)

        self._groq_show_btn = ctk.CTkButton(
            scroll, text="Mostrar", width=70,
            command=lambda: self._toggle_show(self._groq_key_entry, self._groq_show_btn),
        )
        self._groq_show_btn.grid(row=row, column=2, padx=5, pady=5)
        row += 1

        # OpenAI API Key
        ctk.CTkLabel(scroll, text="OpenAI API Key:").grid(
            row=row, column=0, sticky="w", padx=10, pady=5
        )
        self._openai_key_entry = ctk.CTkEntry(scroll, show="*", width=350)
        self._openai_key_entry.grid(row=row, column=1, sticky="ew", padx=5, pady=5)
        if self._config.openai_api_key:
            self._openai_key_entry.insert(0, self._config.openai_api_key)

        self._openai_show_btn = ctk.CTkButton(
            scroll, text="Mostrar", width=70,
            command=lambda: self._toggle_show(self._openai_key_entry, self._openai_show_btn),
        )
        self._openai_show_btn.grid(row=row, column=2, padx=5, pady=5)
        row += 1

        # ── Seção: Áudio ──
        ctk.CTkLabel(
            scroll,
            text="Áudio",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=row, column=0, columnspan=3, sticky="w", padx=10, pady=(20, 5))
        row += 1

        # Idioma
        ctk.CTkLabel(scroll, text="Idioma:").grid(
            row=row, column=0, sticky="w", padx=10, pady=5
        )
        self._language_menu = ctk.CTkOptionMenu(
            scroll, values=["pt", "en", "es", "fr", "de", "it"], width=200,
        )
        self._language_menu.set(self._config.language)
        self._language_menu.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1

        # Dispositivo de áudio
        ctk.CTkLabel(scroll, text="Microfone:").grid(
            row=row, column=0, sticky="w", padx=10, pady=5
        )
        devices = _get_audio_devices()
        device_names = ["Padrão do Sistema"] + [f"[{idx}] {name}" for idx, name in devices]
        self._device_map = {0: None}  # "Padrão" → None
        for i, (idx, name) in enumerate(devices):
            self._device_map[i + 1] = idx

        self._device_menu = ctk.CTkOptionMenu(scroll, values=device_names, width=350)
        # Selecionar dispositivo atual
        if self._config.audio_device_index is not None:
            for label_idx, dev_idx in self._device_map.items():
                if dev_idx == self._config.audio_device_index:
                    self._device_menu.set(device_names[label_idx])
                    break
        else:
            self._device_menu.set(device_names[0])
        self._device_menu.grid(row=row, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        row += 1

        # VAD Aggressiveness
        ctk.CTkLabel(scroll, text="Sensibilidade VAD:").grid(
            row=row, column=0, sticky="w", padx=10, pady=5
        )
        vad_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        vad_frame.grid(row=row, column=1, sticky="w", padx=5, pady=5)

        self._vad_label = ctk.CTkLabel(vad_frame, text=str(self._config.vad_aggressiveness))
        self._vad_slider = ctk.CTkSlider(
            vad_frame, from_=0, to=3, number_of_steps=3, width=200,
            command=lambda v: self._vad_label.configure(text=str(int(v))),
        )
        self._vad_slider.set(self._config.vad_aggressiveness)
        self._vad_slider.pack(side="left")
        self._vad_label.pack(side="left", padx=(10, 0))

        ctk.CTkLabel(scroll, text="(0=baixa, 3=alta)", text_color="gray").grid(
            row=row, column=2, sticky="w", padx=5, pady=5
        )
        row += 1

        # ── Seção: Inserção ──
        ctk.CTkLabel(
            scroll,
            text="Inserção de Texto",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=row, column=0, columnspan=3, sticky="w", padx=10, pady=(20, 5))
        row += 1

        # Hotkey
        ctk.CTkLabel(scroll, text="Hotkey:").grid(
            row=row, column=0, sticky="w", padx=10, pady=5
        )
        hotkey_values = [f"F{i}" for i in range(1, 13)]
        self._hotkey_menu = ctk.CTkOptionMenu(scroll, values=hotkey_values, width=200)
        self._hotkey_menu.set(self._config.hotkey.upper())
        self._hotkey_menu.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1

        # Delay de digitação
        ctk.CTkLabel(scroll, text="Delay digitação (ms):").grid(
            row=row, column=0, sticky="w", padx=10, pady=5
        )
        delay_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        delay_frame.grid(row=row, column=1, sticky="w", padx=5, pady=5)

        self._delay_label = ctk.CTkLabel(delay_frame, text=str(self._config.typing_delay_ms))
        self._delay_slider = ctk.CTkSlider(
            delay_frame, from_=5, to=50, number_of_steps=45, width=200,
            command=lambda v: self._delay_label.configure(text=str(int(v))),
        )
        self._delay_slider.set(self._config.typing_delay_ms)
        self._delay_slider.pack(side="left")
        self._delay_label.pack(side="left", padx=(10, 0))
        row += 1

        # Auto-capitalizar
        ctk.CTkLabel(scroll, text="Auto-capitalizar:").grid(
            row=row, column=0, sticky="w", padx=10, pady=5
        )
        self._capitalize_switch = ctk.CTkSwitch(scroll, text="")
        if self._config.auto_capitalize:
            self._capitalize_switch.select()
        self._capitalize_switch.grid(row=row, column=1, sticky="w", padx=5, pady=5)
        row += 1

        # ── Botão Salvar ──
        self._save_btn = ctk.CTkButton(
            scroll,
            text="Salvar Configurações",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=45,
            fg_color="#3498db",
            hover_color="#2980b9",
            command=self._save_settings,
        )
        self._save_btn.grid(row=row, column=0, columnspan=3, sticky="ew", padx=10, pady=20)

        # Label de feedback
        self._save_feedback = ctk.CTkLabel(scroll, text="", text_color="#2ecc71")
        self._save_feedback.grid(row=row + 1, column=0, columnspan=3, pady=(0, 10))

    # ── Aba Sobre ───────────────────────────────────────────

    def _build_about_tab(self):
        tab = self._tabview.tab("Sobre")
        tab.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            tab,
            text="VozTerminal",
            font=ctk.CTkFont(size=28, weight="bold"),
        ).grid(row=0, column=0, pady=(40, 5))

        ctk.CTkLabel(
            tab,
            text=f"Versão {__version__}",
            font=ctk.CTkFont(size=14),
            text_color="gray",
        ).grid(row=1, column=0, pady=(0, 20))

        ctk.CTkLabel(
            tab,
            text="Ditado por voz para terminais Linux",
            font=ctk.CTkFont(size=16),
        ).grid(row=2, column=0, pady=5)

        info_text = (
            "Transcrição via Groq API (Whisper) com fallback OpenAI.\n"
            "Detecção de voz com webrtcvad + filtro de energia RMS.\n"
            "Inserção via xdotool na janela ativa.\n\n"
            "Desenvolvido por Tiago Cruz\n"
            "Shopping Botucatu - Tecnologia"
        )
        ctk.CTkLabel(
            tab,
            text=info_text,
            font=ctk.CTkFont(size=13),
            text_color="gray",
            justify="center",
        ).grid(row=3, column=0, pady=10, padx=20)

        ctk.CTkLabel(
            tab,
            text="Pré-requisitos: xdotool, portaudio19-dev",
            font=ctk.CTkFont(size=11),
            text_color="#666",
        ).grid(row=4, column=0, pady=(20, 5))

    # ── Ações ───────────────────────────────────────────────

    def _toggle_show(self, entry: ctk.CTkEntry, btn: ctk.CTkButton):
        """Alterna visibilidade de campo de senha."""
        if entry.cget("show") == "*":
            entry.configure(show="")
            btn.configure(text="Ocultar")
        else:
            entry.configure(show="*")
            btn.configure(text="Mostrar")

    def _save_settings(self):
        """Salva todas as configurações no arquivo."""
        # Coleta valores
        self._config.groq_api_key = self._groq_key_entry.get().strip() or None
        self._config.openai_api_key = self._openai_key_entry.get().strip() or None
        self._config.language = self._language_menu.get()
        self._config.hotkey = self._hotkey_menu.get().lower()
        self._config.vad_aggressiveness = int(self._vad_slider.get())
        self._config.typing_delay_ms = int(self._delay_slider.get())
        self._config.auto_capitalize = self._capitalize_switch.get() == 1

        # Dispositivo de áudio
        selected = self._device_menu.get()
        if selected == "Padrão do Sistema":
            self._config.audio_device_index = None
        else:
            for label_idx, dev_idx in self._device_map.items():
                if label_idx > 0:
                    devices = _get_audio_devices()
                    if label_idx - 1 < len(devices):
                        idx, name = devices[label_idx - 1]
                        expected = f"[{idx}] {name}"
                        if selected == expected:
                            self._config.audio_device_index = idx
                            break

        # Salva com API keys
        self._config.save(save_keys=True)

        # Atualiza hotkey label
        self._hotkey_label.configure(text=f"Hotkey: {self._config.hotkey.upper()}")

        # Feedback visual
        self._save_feedback.configure(text="Configurações salvas com sucesso!")
        self.after(3000, lambda: self._save_feedback.configure(text=""))

    def _toggle_dictation(self):
        """Inicia ou para o ditado."""
        if self._is_dictating:
            self._stop_dictation()
        else:
            self._start_dictation()

    def _start_dictation(self):
        """Inicia o daemon de ditado."""
        # Recarrega config para pegar valores mais recentes
        self._config = Config.load()

        if not self._config.groq_api_key and not self._config.openai_api_key:
            self._append_log("[ERRO] Configure uma API Key antes de iniciar o ditado.\n")
            self._tabview.set("Configurações")
            return

        try:
            # Configura logging para capturar no textbox
            self._setup_gui_logging()

            from vozterminal.daemon import VozTerminalDaemon
            self._daemon = VozTerminalDaemon(self._config)

            # Para hotkey global da GUI (daemon terá o seu próprio)
            if self._global_hotkey:
                self._global_hotkey.stop()

            # Inicia hotkey do daemon e ativa ditado
            self._daemon._hotkey.start()
            self._daemon._is_running = True
            self._daemon._is_active = True
            self._daemon._audio.start()

            self._is_dictating = True
            self._update_gui_active()
            self._append_log("[INFO] Ditado iniciado. Fale agora!\n")
            self._append_log(f"[INFO] Hotkey: {self._config.hotkey.upper()} para toggle\n")

            # Inicia polling para sincronizar GUI com estado do daemon (F9)
            self._start_state_polling()

        except Exception as e:
            self._append_log(f"[ERRO] Falha ao iniciar: {e}\n")
            logger.exception("Erro ao iniciar ditado")

    def _start_state_polling(self):
        """Inicia polling a cada 200ms para sincronizar GUI com F9."""
        self._poll_state()

    def _poll_state(self):
        """Verifica estado do daemon e atualiza GUI se mudou."""
        if not self._daemon:
            return

        daemon_active = self._daemon._is_active

        # Estado mudou? (F9 foi pressionado)
        if daemon_active and not self._is_dictating:
            self._is_dictating = True
            self._update_gui_active()
        elif not daemon_active and self._is_dictating:
            self._is_dictating = False
            self._update_gui_stopped()

        # Continua polling enquanto daemon existir
        if self._daemon:
            self.after(200, self._poll_state)

    def _update_gui_active(self):
        """Atualiza GUI para estado 'ouvindo'."""
        self._toggle_btn.configure(
            text="Parar Ditado",
            fg_color="#e74c3c",
            hover_color="#c0392b",
        )
        self._status_label.configure(text="Ouvindo...", text_color="#2ecc71")

    def _update_gui_stopped(self):
        """Atualiza GUI para estado 'parado'."""
        self._toggle_btn.configure(
            text="Iniciar Ditado",
            fg_color="#2ecc71",
            hover_color="#27ae60",
        )
        self._status_label.configure(text="Parado", text_color="#ff6b6b")

    def _stop_dictation(self):
        """Para o daemon de ditado."""
        try:
            if self._daemon:
                self._daemon._is_active = False
                self._daemon._audio.stop()
                self._daemon._hotkey.stop()
                self._daemon._is_running = False
                self._daemon = None

            self._is_dictating = False
            self._update_gui_stopped()
            self._append_log("[INFO] Ditado parado.\n")

            self._teardown_gui_logging()

            # Reativa hotkey global da GUI
            self._start_global_hotkey()

        except Exception as e:
            self._append_log(f"[ERRO] Falha ao parar: {e}\n")

    def _append_log(self, text: str):
        """Adiciona texto ao log (thread-safe via after)."""
        def _do():
            self._log_text.configure(state="normal")
            self._log_text.insert("end", text)
            self._log_text.see("end")
            self._log_text.configure(state="disabled")
        # Agenda no main thread do tkinter
        self.after(0, _do)

    def _clear_log(self):
        """Limpa o log."""
        self._log_text.configure(state="normal")
        self._log_text.delete("1.0", "end")
        self._log_text.configure(state="disabled")

    def _setup_gui_logging(self):
        """Configura handler de logging que redireciona para o textbox."""
        self._log_handler = _GUILogHandler(self._append_log)
        self._log_handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
        )
        logging.getLogger("vozterminal").addHandler(self._log_handler)
        logging.getLogger("vozterminal").setLevel(logging.INFO)

    def _teardown_gui_logging(self):
        """Remove handler de logging da GUI."""
        if self._log_handler:
            logging.getLogger("vozterminal").removeHandler(self._log_handler)
            self._log_handler = None

    def _on_close(self):
        """Cleanup ao fechar a janela."""
        if self._is_dictating:
            self._stop_dictation()
        if self._global_hotkey:
            self._global_hotkey.stop()
        self.destroy()


class _GUILogHandler(logging.Handler):
    """Handler de logging que envia para callback da GUI."""

    def __init__(self, append_fn: callable):
        super().__init__()
        self._append = append_fn

    def emit(self, record):
        try:
            msg = self.format(record) + "\n"
            self._append(msg)
        except Exception:
            pass


def main():
    """Entry point para a GUI."""
    app = VozTerminalGUI()
    app.mainloop()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoCaption VEC - Standalone App
Chạy độc lập, không cần DaVinci Resolve.
Giao diện: tkinter (có sẵn trong Python, không cần cài thêm).
"""

import sys
import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# ─── UTF-8 stdout ────────────────────────────────────────────
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# ─── i18n ────────────────────────────────────────────────────
STRINGS = {
    "en": {
        "title":           "AutoCaption VEC",
        "tab_main":        "Generate",
        "tab_log":         "Log",
        "input_file":      "Input File",
        "browse":          "Browse...",
        "output_folder":   "Output Folder",
        "src_lang":        "Source Language",
        "model":           "Whisper Model",
        "output_files":    "Output Files",
        "trans_lang":      "Translation Language",
        "one_file":        "1 File (Original)",
        "two_files":       "2 Files (Original + Translation)",
        "start":           "▶  Generate Subtitles",
        "cancel":          "■  Cancel",
        "auto":            "Auto-detect",
        "status_ready":    "Ready.",
        "status_running":  "Processing… please wait.",
        "status_done":     "Done!",
        "status_cancel":   "Cancelled.",
        "err_no_input":    "Please select an input file.",
        "err_no_output":   "Please select an output folder.",
        "err_no_whisper":  "faster-whisper is not installed.\nRun: pip install faster-whisper",
        "err_no_argos":    "argostranslate is not installed.\nRun: pip install argostranslate",
        "err_no_speech":   "No speech detected in file.",
        "err_file_not_found": "Input file not found.",
        "done_msg":        "Subtitle file(s) saved to:\n{paths}",
        "lang_vi":         "Vietnamese",
        "lang_en":         "English",
        "lang_zh":         "Chinese",
        "open_folder":     "Open Output Folder",
    },
    "vi": {
        "title":           "AutoCaption VEC",
        "tab_main":        "Tạo phụ đề",
        "tab_log":         "Log",
        "input_file":      "File đầu vào",
        "browse":          "Chọn file...",
        "output_folder":   "Thư mục lưu",
        "src_lang":        "Ngôn ngữ gốc",
        "model":           "Model Whisper",
        "output_files":    "File xuất",
        "trans_lang":      "Ngôn ngữ dịch",
        "one_file":        "1 File (Gốc)",
        "two_files":       "2 File (Gốc + Dịch)",
        "start":           "▶  Tạo phụ đề",
        "cancel":          "■  Hủy",
        "auto":            "Tự nhận diện",
        "status_ready":    "Sẵn sàng.",
        "status_running":  "Đang xử lý… vui lòng chờ.",
        "status_done":     "Hoàn thành!",
        "status_cancel":   "Đã hủy.",
        "err_no_input":    "Vui lòng chọn file đầu vào.",
        "err_no_output":   "Vui lòng chọn thư mục lưu.",
        "err_no_whisper":  "Chưa cài faster-whisper.\nChạy: pip install faster-whisper",
        "err_no_argos":    "Chưa cài argostranslate.\nChạy: pip install argostranslate",
        "err_no_speech":   "Không phát hiện giọng nói trong file.",
        "err_file_not_found": "Không tìm thấy file đầu vào.",
        "done_msg":        "Đã lưu file phụ đề tại:\n{paths}",
        "lang_vi":         "Tiếng Việt",
        "lang_en":         "Tiếng Anh",
        "lang_zh":         "Tiếng Trung",
        "open_folder":     "Mở thư mục",
    },
    "zh": {
        "title":           "AutoCaption VEC",
        "tab_main":        "生成字幕",
        "tab_log":         "日志",
        "input_file":      "输入文件",
        "browse":          "浏览...",
        "output_folder":   "输出文件夹",
        "src_lang":        "源语言",
        "model":           "Whisper 模型",
        "output_files":    "输出文件",
        "trans_lang":      "翻译语言",
        "one_file":        "1 个文件（原文）",
        "two_files":       "2 个文件（原文 + 翻译）",
        "start":           "▶  生成字幕",
        "cancel":          "■  取消",
        "auto":            "自动检测",
        "status_ready":    "就绪。",
        "status_running":  "正在处理，请稍候…",
        "status_done":     "完成！",
        "status_cancel":   "已取消。",
        "err_no_input":    "请选择输入文件。",
        "err_no_output":   "请选择输出文件夹。",
        "err_no_whisper":  "未安装 faster-whisper。\n运行: pip install faster-whisper",
        "err_no_argos":    "未安装 argostranslate。\n运行: pip install argostranslate",
        "err_no_speech":   "文件中未检测到语音。",
        "err_file_not_found": "未找到输入文件。",
        "done_msg":        "字幕文件已保存至:\n{paths}",
        "lang_vi":         "越南语",
        "lang_en":         "英语",
        "lang_zh":         "中文",
        "open_folder":     "打开文件夹",
    },
}

LANG_CODES = {"vi": "vi", "en": "en", "zh": "zh"}
MODEL_SIZES = ["tiny", "base", "small", "medium", "large-v3"]
LANG_CODE_MAP = {"zh": "zh"}


def normalize_lang(code):
    return LANG_CODE_MAP.get(code, code) if code else code


def format_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


# ─── CORE LOGIC ──────────────────────────────────────────────

def transcribe(input_path, language, model_size, log_fn, cancel_event):
    """Chạy faster-whisper, trả về list segment dict và ngôn ngữ đã phát hiện."""
    from faster_whisper import WhisperModel
    log_fn(f"Loading model '{model_size}'…")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    log_fn(f"Processing: {input_path}")
    segments_iter, info = model.transcribe(
        input_path,
        language=language,
        beam_size=5,
        vad_filter=True,
    )
    detected_lang = normalize_lang(language) if language else normalize_lang(info.language)
    if not language:
        log_fn(f"Detected language: {info.language} ({info.language_probability:.2f})")
    results = []
    for seg in segments_iter:
        if cancel_event.is_set():
            return None, detected_lang
        text = seg.text.strip()
        if not text:
            continue
        start = format_timestamp(seg.start)
        end = format_timestamp(seg.end)
        results.append({"start": start, "end": end, "text": text})
        log_fn(f"[{start} --> {end}] {text}")
    return results, detected_lang


def build_srt(segments):
    lines = []
    for i, seg in enumerate(segments, 1):
        lines += [str(i), f"{seg['start']} --> {seg['end']}", seg["text"], ""]
    return "\n".join(lines)


def ensure_argos_package(src, tgt, log_fn, try_pivot=True):
    import argostranslate.package
    import argostranslate.translate

    def package_installed(from_code, to_code):
        installed = argostranslate.translate.get_installed_languages()
        from_lang = next((l for l in installed if l.code == from_code), None)
        to_lang = next((l for l in installed if l.code == to_code), None)
        return from_lang and to_lang and from_lang.get_translation(to_lang)

    def find_package(from_code, to_code):
        return next(
            (p for p in argostranslate.package.get_available_packages()
             if p.from_code == from_code and p.to_code == to_code),
            None
        )

    if package_installed(src, tgt):
        return True

    log_fn(f"Downloading translation package {src} → {tgt}…")
    argostranslate.package.update_package_index()
    pkg = find_package(src, tgt)
    if pkg:
        argostranslate.package.install_from_path(pkg.download())
        log_fn(f"Package {src} → {tgt} installed.")
        return True

    if try_pivot and src != "en" and tgt != "en":
        log_fn(f"No direct package for {src} → {tgt}. Attempting pivot via English.")
        first = ensure_argos_package(src, "en", log_fn, try_pivot=False)
        second = ensure_argos_package("en", tgt, log_fn, try_pivot=False)
        return first and second

    log_fn(f"ERROR: No package found for {src} → {tgt}")
    return False


def translate_segments(segments, src_lang, tgt_lang, log_fn, cancel_event, progress_fn=None):
    import argostranslate.translate
    translated = []
    total = len(segments) if segments else 0
    for idx, seg in enumerate(segments, start=1):
        if cancel_event.is_set():
            return None
        try:
            text = argostranslate.translate.translate(seg["text"], src_lang, tgt_lang)
        except Exception as e:
            log_fn(f"WARNING: translation failed for segment: {e}")
            text = seg["text"]
        translated.append({**seg, "text": text})
        log_fn(f"[{seg['start']} --> {seg['end']}] {text}")
        if progress_fn and total:
            # report progress between 60% and 90% during translation
            percent = 60 + int((idx / total) * 30)
            try:
                progress_fn(percent)
            except Exception:
                pass
    if progress_fn:
        try:
            progress_fn(90)
        except Exception:
            pass
    return translated


def save_srt(path, srt_text, log_fn):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(srt_text)
        log_fn(f"Saved: {path}")
        return True
    except Exception as e:
        log_fn(f"ERROR saving {path}: {e}")
        return False


# ─── GUI ─────────────────────────────────────────────────────

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self._ui_lang = "vi"  # ngôn ngữ giao diện mặc định
        self._cancel_event = threading.Event()
        self._running = False

        self._bg_color = "#0b1220"
        self._panel_color = "#101827"
        self._card_color = "#111827"
        self._field_color = "#141c2d"
        self._button_color = "#2563eb"
        self._button_hover = "#1d4ed8"
        self._fg_color = "#e6eef6"

        self._build_ui()
        self._refresh_lang()

    # ── build ─────────────────────────────────────────────────
    def _build_ui(self):
        self.resizable(False, False)
        self.configure(bg=self._bg_color, padx=12, pady=12)
        self.attributes("-alpha", 0.98)

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Dark.TLabel",
                        background=self._panel_color,
                        foreground=self._fg_color)
        style.configure("Dark.TEntry",
                        fieldbackground=self._field_color,
                        background=self._field_color,
                        foreground=self._fg_color,
                        padding=6)
        style.map("Dark.TEntry",
                  fieldbackground=[("focus", self._field_color)],
                  foreground=[("focus", self._fg_color)],
                  selectbackground=[("focus", "#334155")],
                  selectforeground=[("focus", self._fg_color)])
        style.configure("Dark.TCombobox",
                        fieldbackground=self._field_color,
                        background=self._field_color,
                        foreground=self._fg_color,
                        arrowcolor=self._fg_color,
                        padding=6)
        style.map("Dark.TCombobox",
                  fieldbackground=[("readonly", self._field_color)],
                  background=[("readonly", self._field_color)],
                  foreground=[("readonly", self._fg_color)])
        style.configure("Rounded.TButton",
                        background=self._button_color,
                        foreground=self._fg_color,
                        borderwidth=0,
                        relief="flat",
                        padding=(12, 8))
        style.map("Rounded.TButton",
                  background=[("active", self._button_hover), ("pressed", "#1e40af")],
                  foreground=[("active", self._fg_color)])
        style.configure("TProgressbar",
                        background=self._button_color,
                        troughcolor=self._field_color)
        style.configure("Card.TFrame",
                        background=self._card_color)
        style.configure("Section.TLabel",
                        background=self._panel_color,
                        foreground=self._fg_color,
                        font=(None, 11, "bold"))
        style.configure("SectionNum.TLabel",
                        background="#2563eb",
                        foreground="white",
                        font=(None, 9, "bold"),
                        padding=(6, 4))

        top = tk.Frame(self, bg=self._panel_color)
        top.pack(fill="x", pady=(0, 10))
        title = tk.Label(top, text="AutoSubs", bg=self._panel_color,
                         fg=self._fg_color, font=(None, 14, "bold"))
        title.pack(side="left")
        self._ui_lang_var = tk.StringVar(value="vi")
        for code, label in [("vi", "Việt"), ("en", "EN"), ("zh", "中文")]:
            tk.Radiobutton(
                top, text=label, variable=self._ui_lang_var,
                value=code, command=self._on_ui_lang_change,
                bg=self._panel_color, fg=self._fg_color,
                selectcolor=self._panel_color,
                activebackground=self._panel_color,
                activeforeground=self._fg_color,
                borderwidth=0,
                highlightthickness=0,
            ).pack(side="left", padx=6)

        content = tk.Frame(self, bg=self._bg_color)
        content.pack(fill="both", expand=True)

        self._left_panel = tk.Frame(content, bg=self._panel_color)
        self._left_panel.pack(side="left", fill="both", expand=True, padx=(0, 8))
        self._right_panel = tk.Frame(content, bg=self._panel_color, width=320)
        self._right_panel.pack(side="left", fill="both", expand=False)

        self._build_main_tab()
        self._build_log_tab()

        self._status_var = tk.StringVar()
        tk.Label(self, textvariable=self._status_var,
                 anchor="w", relief="flat", bg=self._panel_color, fg=self._fg_color,
                 padx=8, bd=0, highlightthickness=1, highlightbackground="#334155"
                 ).pack(fill="x", pady=(10, 0))

    def _build_main_tab(self):
        f = self._left_panel
        f.configure(bg=self._panel_color)
        COL_W = 38

        entry_style = {
            "fieldbackground": self._field_color,
            "background": self._field_color,
            "foreground": self._fg_color,
            "insertbackground": self._fg_color,
            "padding": 8,
        }
        button_style = {
            "style": "Rounded.TButton",
        }

        # Input file
        self._lbl_input = tk.Label(f, anchor="w", bg=self._panel_color, fg=self._fg_color)
        self._lbl_input.grid(row=0, column=0, sticky="w", pady=4)
        self._input_var = tk.StringVar()
        ttk.Entry(f, textvariable=self._input_var, width=COL_W, style="Dark.TEntry").grid(row=0, column=1, padx=6)
        self._btn_browse_input = ttk.Button(f, command=self._browse_input, text="Choose file", **button_style)
        self._btn_browse_input.grid(row=0, column=2)

        # Output folder
        self._lbl_output = tk.Label(f, anchor="w", bg=self._panel_color, fg=self._fg_color)
        self._lbl_output.grid(row=1, column=0, sticky="w", pady=4)
        self._output_var = tk.StringVar()
        ttk.Entry(f, textvariable=self._output_var, width=COL_W, style="Dark.TEntry").grid(row=1, column=1, padx=6)
        self._btn_browse_output = ttk.Button(f, command=self._browse_output, text="Choose folder", **button_style)
        self._btn_browse_output.grid(row=1, column=2)

        category = tk.Frame(f, bg=self._card_color, bd=0, padx=16, pady=16)
        category.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        category.grid_columnconfigure(0, weight=1)
        self._lbl_src_lang = tk.Label(category, text="Source language", bg=self._card_color, fg=self._fg_color)
        self._lbl_src_lang.grid(row=0, column=0, sticky="w")
        self._src_lang_var = tk.StringVar()
        self._cmb_src_lang = ttk.Combobox(category, textvariable=self._src_lang_var,
                                           state="readonly", width=COL_W - 2,
                                           style="Dark.TCombobox")
        self._cmb_src_lang.grid(row=1, column=0, pady=(6, 0), sticky="ew")

        category2 = tk.Frame(f, bg=self._card_color, bd=0, padx=16, pady=16)
        category2.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        category2.grid_columnconfigure(0, weight=1)
        self._lbl_model = tk.Label(category2, text="Whisper model", bg=self._card_color, fg=self._fg_color)
        self._lbl_model.grid(row=0, column=0, sticky="w")
        self._model_var = tk.StringVar(value="medium")
        self._cmb_model = ttk.Combobox(category2, textvariable=self._model_var,
                                        values=MODEL_SIZES, state="readonly", width=COL_W - 2,
                                        style="Dark.TCombobox")
        self._cmb_model.grid(row=1, column=0, pady=(6, 0), sticky="ew")
        self._cmb_model.current(3)

        category3 = tk.Frame(f, bg=self._card_color, bd=0, padx=16, pady=16)
        category3.grid(row=4, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        category3.grid_columnconfigure(0, weight=1)
        self._lbl_out_files = tk.Label(category3, text="Output file", bg=self._card_color, fg=self._fg_color)
        self._lbl_out_files.grid(row=0, column=0, sticky="w")
        self._out_files_var = tk.StringVar()
        self._cmb_out_files = ttk.Combobox(category3, textvariable=self._out_files_var,
                                            state="readonly", width=COL_W - 2,
                                            style="Dark.TCombobox")
        self._cmb_out_files.grid(row=1, column=0, pady=(6, 0), sticky="ew")
        self._cmb_out_files.bind("<<ComboboxSelected>>", self._on_out_files_change)

        category4 = tk.Frame(f, bg=self._card_color, bd=0, padx=16, pady=16)
        category4.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(12, 0))
        category4.grid_columnconfigure(0, weight=1)
        self._lbl_trans = tk.Label(category4, text="Translation language", bg=self._card_color, fg=self._fg_color)
        self._lbl_trans.grid(row=0, column=0, sticky="w")
        self._trans_var = tk.StringVar()
        self._cmb_trans = ttk.Combobox(category4, textvariable=self._trans_var,
                                        state="disabled", width=COL_W - 2,
                                        style="Dark.TCombobox")
        self._cmb_trans.grid(row=1, column=0, pady=(6, 0), sticky="ew")

        # Progress bar with percentage label
        self._progress = ttk.Progressbar(f, mode="determinate", length=320, maximum=100)
        self._progress.grid(row=6, column=0, columnspan=3, pady=(14, 4), sticky="ew")
        self._progress_label = tk.Label(f, text="0%", anchor="e", bg=self._panel_color, fg=self._fg_color)
        self._progress_label.grid(row=7, column=0, columnspan=3, pady=(4, 0), sticky="e")

        # Buttons
        btn_frame = tk.Frame(f, bg=self._panel_color)
        btn_frame.grid(row=8, column=0, columnspan=3, pady=12, sticky="ew")
        self._btn_start = ttk.Button(btn_frame, text="Generate",
                                     command=self._on_start,
                                     style="Rounded.TButton")
        self._btn_start.pack(side="left", expand=True, fill="x", padx=(0, 6))
        self._btn_cancel = ttk.Button(btn_frame, text="Cancel",
                                      command=self._on_cancel,
                                      state="disabled",
                                      style="Rounded.TButton")
        self._btn_cancel.pack(side="left", expand=True, fill="x", padx=(0, 6))
        self._btn_open = ttk.Button(btn_frame, text="Open folder",
                                    command=self._open_output_folder,
                                    style="Rounded.TButton")
        self._btn_open.pack(side="left", expand=True, fill="x")

    def _build_log_tab(self):
        f = self._right_panel
        f.configure(bg=self._panel_color)
        panel = tk.Frame(f, bg=self._card_color, bd=0, padx=16, pady=16)
        panel.pack(fill="both", expand=True)
        tk.Label(panel, text="Subtitles", bg=self._card_color, fg=self._fg_color,
                 font=(None, 12, "bold")).pack(anchor="w")
        self._subtitle_text = scrolledtext.ScrolledText(
            panel, state="disabled",
            font=("Consolas", 10), bg=self._field_color, fg=self._fg_color,
            insertbackground=self._fg_color, wrap="word", spacing3=4,
            bd=0, highlightthickness=0, height=22
        )
        self._subtitle_text.pack(fill="both", expand=True, pady=(10, 0))
        self._subtitle_text.config(state="normal")
        self._subtitle_text.insert("end", "Your subtitles will appear here when finished transcribing")
        self._subtitle_text.config(state="disabled")

        self._log_text = self._subtitle_text

    # ── language refresh ──────────────────────────────────────
    def _refresh_lang(self):
        s = STRINGS[self._ui_lang]
        self.title(s["title"])
        # notebook tabs removed; using fixed split pane

        self._lbl_input.config(text=s["input_file"])
        self._btn_browse_input.config(text=s["browse"])
        self._lbl_output.config(text=s["output_folder"])
        self._btn_browse_output.config(text=s["browse"])
        self._lbl_src_lang.config(text=s["src_lang"])
        self._lbl_model.config(text=s["model"])
        self._lbl_out_files.config(text=s["output_files"])
        self._lbl_trans.config(text=s["trans_lang"])
        self._btn_start.config(text=s["start"])
        self._btn_cancel.config(text=s["cancel"])
        self._btn_open.config(text=s["open_folder"])

        # Source lang options (thêm auto-detect)
        src_options = [s["auto"], s["lang_vi"], s["lang_en"], s["lang_zh"]]
        self._cmb_src_lang.config(values=src_options)
        if not self._src_lang_var.get() or self._src_lang_var.get() not in src_options:
            self._cmb_src_lang.current(0)

        # Output files options
        out_options = [s["one_file"], s["two_files"]]
        self._cmb_out_files.config(values=out_options)
        cur_out = getattr(self, "_out_files_idx", 0)
        self._cmb_out_files.current(cur_out)
        self._out_files_var.set(out_options[cur_out])

        # Trans lang options
        trans_options = [s["lang_en"], s["lang_vi"], s["lang_zh"]]
        self._cmb_trans.config(values=trans_options)
        cur_trans = getattr(self, "_trans_idx", 0)
        self._cmb_trans.current(cur_trans)
        self._trans_var.set(trans_options[cur_trans])

        if not self._status_var.get():
            self._status_var.set(s["status_ready"])

    # ── progress update (thread-safe)
    def _update_progress(self, percent):
        def _do():
            if percent is None:
                # unknown length: pulse
                try:
                    self._progress.config(mode="indeterminate")
                    self._progress.start(12)
                except Exception:
                    pass
                self._progress_label.config(text="")
            else:
                try:
                    self._progress.stop()
                except Exception:
                    pass
                self._progress.config(mode="determinate")
                self._progress['value'] = max(0, min(100, int(percent)))
                self._progress_label.config(text=f"{int(self._progress['value'])}%")
        self.after(0, _do)

    def _on_ui_lang_change(self):
        self._ui_lang = self._ui_lang_var.get()
        self._refresh_lang()

    def _on_out_files_change(self, _=None):
        s = STRINGS[self._ui_lang]
        two_files = s["two_files"]
        is_two = self._out_files_var.get() == two_files
        self._out_files_idx = 1 if is_two else 0
        self._cmb_trans.config(state="readonly" if is_two else "disabled")

    # ── browse ────────────────────────────────────────────────
    def _browse_input(self):
        path = filedialog.askopenfilename(
            filetypes=[("Media Files", "*.mp4 *.mov *.mkv *.wav *.mp3 *.m4a *.avi"),
                       ("All Files", "*.*")]
        )
        if path:
            self._input_var.set(path)
            # Auto-set output folder to same dir as input
            if not self._output_var.get():
                self._output_var.set(os.path.dirname(path))

    def _browse_output(self):
        path = filedialog.askdirectory()
        if path:
            self._output_var.set(path)

    def _open_output_folder(self):
        folder = self._output_var.get()
        if folder and os.path.isdir(folder):
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                os.system(f'open "{folder}"')
            else:
                os.system(f'xdg-open "{folder}"')

    # ── get settings ──────────────────────────────────────────
    def _get_src_lang_code(self):
        s = STRINGS[self._ui_lang]
        mapping = {
            s["lang_vi"]: "vi",
            s["lang_en"]: "en",
            s["lang_zh"]: "zh",
            s["auto"]: None,
        }
        return mapping.get(self._src_lang_var.get())

    def _get_trans_lang_code(self):
        s = STRINGS[self._ui_lang]
        mapping = {
            s["lang_vi"]: "vi",
            s["lang_en"]: "en",
            s["lang_zh"]: "zh",
        }
        return mapping.get(self._trans_var.get(), "en")

    def _is_two_files(self):
        return self._out_files_var.get() == STRINGS[self._ui_lang]["two_files"]

    # ── log ───────────────────────────────────────────────────
    def _log(self, msg):
        def _do():
            self._log_text.config(state="normal")
            self._log_text.insert("end", msg + "\n")
            self._log_text.see("end")
            self._log_text.config(state="disabled")
        self.after(0, _do)

    def _set_status(self, key):
        self.after(0, lambda: self._status_var.set(STRINGS[self._ui_lang][key]))

    # ── start / cancel ────────────────────────────────────────
    def _on_start(self):
        s = STRINGS[self._ui_lang]
        input_path = self._input_var.get().strip()
        output_folder = self._output_var.get().strip()

        if not input_path:
            messagebox.showwarning(s["title"], s["err_no_input"]); return
        if not output_folder:
            messagebox.showwarning(s["title"], s["err_no_output"]); return

        try:
            import faster_whisper  # noqa: F401
        except ImportError:
            messagebox.showerror(s["title"], s["err_no_whisper"]); return

        if self._is_two_files():
            try:
                import argostranslate  # noqa: F401
            except ImportError:
                messagebox.showerror(s["title"], s["err_no_argos"]); return

        self._cancel_event.clear()
        self._running = True
        self._btn_start.config(state="disabled")
        self._btn_cancel.config(state="normal")
        self._update_progress(None)
        self._set_status("status_running")
        # focus log pane on start
        try:
            self._log_text.focus_set()
        except Exception:
            pass

        thread = threading.Thread(target=self._worker, daemon=True)
        thread.start()

    def _on_cancel(self):
        self._cancel_event.set()
        self._set_status("status_cancel")

    def _finish(self, success, paths=None):
        def _do():
            # update to final state on success, otherwise clear
            self._running = False
            self._btn_start.config(state="normal")
            self._btn_cancel.config(state="disabled")
            s = STRINGS[self._ui_lang]
            if success and paths:
                try:
                    self._update_progress(100)
                except Exception:
                    pass
                self._set_status("status_done")
                messagebox.showinfo(
                    s["title"],
                    s["done_msg"].format(paths="\n".join(paths))
                )
                try:
                    self.focus_set()
                except Exception:
                    pass
            elif not self._cancel_event.is_set():
                try:
                    self._update_progress(0)
                except Exception:
                    pass
                self._status_var.set(s["status_ready"])
        self.after(0, _do)

    # ── worker (background thread) ────────────────────────────
    def _worker(self):
        s = STRINGS[self._ui_lang]
        input_path   = self._input_var.get().strip()
        output_folder = self._output_var.get().strip()
        src_lang     = self._get_src_lang_code()
        model_size   = self._model_var.get()
        two_files    = self._is_two_files()
        trans_lang   = self._get_trans_lang_code() if two_files else None

        # Kiểm tra file
        if not os.path.isfile(input_path):
            self._log(s["err_file_not_found"])
            messagebox.showerror(s["title"], s["err_file_not_found"])
            self._finish(False)
            return

        # Transcribe
        try:
            segments, detected_lang = transcribe(
                input_path, src_lang, model_size,
                self._log, self._cancel_event
            )
        except Exception as e:
            self._log(f"ERROR: {e}")
            self._finish(False)
            return

        # transcribe done — update progress
        try:
            self._update_progress(40)
        except Exception:
            pass

        if self._cancel_event.is_set():
            self._finish(False)
            return
        if not segments:
            self._log(s["err_no_speech"])
            messagebox.showwarning(s["title"], s["err_no_speech"])
            self._finish(False)
            return

        # Lưu file gốc
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        srt_original = os.path.join(output_folder, base_name + ".srt")
        if not save_srt(srt_original, build_srt(segments), self._log):
            self._finish(False)
            return

        # saved original
        try:
            self._update_progress(60)
        except Exception:
            pass

        saved_paths = [srt_original]

        # Dịch và lưu file thứ 2
        if two_files and trans_lang:
            detected = src_lang if src_lang else detected_lang
            detected = normalize_lang(detected)
            target = normalize_lang(trans_lang)
            if detected == target:
                self._log("Source and target languages are the same — skipping translation.")
                saved_paths.append(srt_original)
            else:
                try:
                    pkg_ok = ensure_argos_package(detected, target, self._log)
                except Exception as e:
                    self._log(f"ERROR installing translation package: {e}")
                    pkg_ok = False

                if pkg_ok and not self._cancel_event.is_set():
                    try:
                        if detected != "en" and target != "en":
                            # translate through English if direct package is unavailable
                            self._log(f"Translating via English: {detected} -> en -> {target}")
                            eng_segments = translate_segments(
                                segments, detected, "en", self._log, self._cancel_event,
                                progress_fn=self._update_progress
                            )
                            if eng_segments is None:
                                trans_segments = None
                            else:
                                trans_segments = translate_segments(
                                    eng_segments, "en", target, self._log, self._cancel_event,
                                    progress_fn=self._update_progress
                                )
                        else:
                            trans_segments = translate_segments(
                                segments, detected, target, self._log, self._cancel_event,
                                progress_fn=self._update_progress
                            )
                    except Exception as e:
                        self._log(f"ERROR during translation: {e}")
                        trans_segments = None

                    if trans_segments and not self._cancel_event.is_set():
                        srt_trans = os.path.join(
                            output_folder, f"{base_name}_{trans_lang}.srt"
                        )
                        if save_srt(srt_trans, build_srt(trans_segments), self._log):
                            saved_paths.append(srt_trans)
                            try:
                                self._update_progress(100)
                            except Exception:
                                pass

        if self._cancel_event.is_set():
            self._finish(False)
            return

        self._finish(True, saved_paths)


# ─── ENTRY POINT ─────────────────────────────────────────────

if __name__ == "__main__":
    app = App()
    app.mainloop()
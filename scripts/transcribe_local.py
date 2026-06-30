#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
transcribe_local.py
Create SRT subtitles using Whisper running locally (faster-whisper).
File 2 (if requested) is a REAL TRANSLATION of File 1, done with Argos Translate
(fully local/offline machine translation, no Google API, no Error 500).

Usage:
    python transcribe_local.py <input> <output_srt> [language] [model_size] [target_language] [output_files]

target_language: ISO code of translation target (vi/en/zh), required if output_files=2
output_files:    1 = only original SRT, 2 = original + translated SRT
"""

import sys
import os

# Configure UTF-8 output to avoid UnicodeEncodeError on Windows
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


def format_timestamp(seconds: float) -> str:
    """Convert seconds to SRT format: HH:MM:SS,mmm"""
    if seconds < 0:
        seconds = 0
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int(round((seconds - int(seconds)) * 1000))
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def save_srt_file(output_path, srt_lines):
    """Save SRT content to file"""
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(srt_lines))
        return True
    except Exception as e:
        print(f"ERROR: Cannot write SRT file: {e}")
        return False


# Một số ngôn ngữ Whisper trả về mã khác với Argos Translate, map lại cho khớp.
_LANG_CODE_MAP = {
    "zh": "zh",   # Argos dùng "zh" cho tiếng Trung giản thể
}


def _normalize_lang(code):
    if not code:
        return code
    return _LANG_CODE_MAP.get(code, code)


def ensure_argos_package(source_lang, target_lang):
    """Tải gói ngôn ngữ Argos Translate nếu chưa có (cần internet lần đầu)."""
    import argostranslate.package
    import argostranslate.translate

    installed_languages = argostranslate.translate.get_installed_languages()
    from_lang = next((l for l in installed_languages if l.code == source_lang), None)
    to_lang = next((l for l in installed_languages if l.code == target_lang), None)

    if from_lang and to_lang and from_lang.get_translation(to_lang):
        return True

    print(f"Đang tải gói dịch {source_lang} -> {target_lang} (chỉ cần internet lần đầu)...")
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()
    package_to_install = next(
        (p for p in available_packages if p.from_code == source_lang and p.to_code == target_lang),
        None
    )
    if not package_to_install:
        print(f"ERROR: Không tìm thấy gói dịch {source_lang} -> {target_lang} trong Argos Translate.")
        return False

    argostranslate.package.install_from_path(package_to_install.download())
    print(f"OK: Đã cài gói dịch {source_lang} -> {target_lang}.")
    return True


def translate_text(text, source_lang, target_lang):
    """Dịch một đoạn text bằng Argos Translate (local)."""
    import argostranslate.translate
    try:
        return argostranslate.translate.translate(text, source_lang, target_lang)
    except Exception as e:
        print(f"WARNING: Dịch thất bại cho đoạn '{text[:30]}...': {e}")
        return text  # fallback: giữ nguyên text gốc nếu dịch lỗi


def main():
    if len(sys.argv) < 3:
        print("Usage: python transcribe_local.py <input_media_file> <output_srt_file> [language] [model_size] [target_language] [output_files]")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]
    language = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] else None
    model_size = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else "medium"
    target_language = sys.argv[5] if len(sys.argv) > 5 and sys.argv[5] else None
    output_files = int(sys.argv[6]) if len(sys.argv) > 6 and sys.argv[6] else 1

    print(f"DEBUG: language={language}, model_size={model_size}, target_language={target_language}, output_files={output_files}")

    if not os.path.isfile(input_path):
        print(f"ERROR: Input file not found: {input_path}")
        sys.exit(2)

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("ERROR: faster-whisper not installed. Run: pip install -r requirements.txt")
        sys.exit(3)

    print(f"Loading Whisper model '{model_size}' (first time may take a few minutes)...")
    model = WhisperModel(model_size, device="cpu", compute_type="int8")

    print(f"Processing audio: {input_path}")
    print("Note: Running on CPU may take some time, please wait...")

    segments, info = model.transcribe(
        input_path,
        language=language,
        beam_size=5,
        vad_filter=True,
    )

    detected_lang = _normalize_lang(info.language)
    print(f"Detected language: {detected_lang} (confidence {info.language_probability:.2f})")

    # Lưu lại từng segment (text gốc + timestamp) để dùng cho cả 2 file.
    segment_list = []
    srt_lines = []
    index = 1
    for segment in segments:
        start = format_timestamp(segment.start)
        end = format_timestamp(segment.end)
        text = segment.text.strip()
        if not text:
            continue
        segment_list.append({"start": start, "end": end, "text": text})
        srt_lines.append(str(index))
        srt_lines.append(f"{start} --> {end}")
        srt_lines.append(text)
        srt_lines.append("")
        index += 1
        print(f"[{start} --> {end}] {text}")

    if index == 1:
        print("ERROR: No speech detected in file.")
        sys.exit(4)

    # Lưu File 1 (ngôn ngữ gốc)
    if not save_srt_file(output_path, srt_lines):
        sys.exit(5)
    print(f"OK: Subtitle file created at {output_path}")

    # Lưu File 2 (bản dịch thật sang target_language)
    if output_files == 2 and target_language:
        target_norm = _normalize_lang(target_language)

        if target_norm == detected_lang:
            print(f"Ngôn ngữ đích trùng với ngôn ngữ gốc ({detected_lang}), bỏ qua dịch, dùng lại nội dung gốc.")
            translated_lines = srt_lines
        else:
            try:
                import argostranslate.translate  # noqa: F401
            except ImportError:
                print("ERROR: Chưa cài argostranslate. Chạy: pip install argostranslate")
                sys.exit(6)

            pkg_ok = ensure_argos_package(detected_lang, target_norm)
            if not pkg_ok:
                print(f"ERROR: Không thể dịch sang '{target_norm}' vì thiếu gói ngôn ngữ. "
                      f"File 2 sẽ KHÔNG được tạo.")
                sys.exit(7)

            print(f"Đang dịch {len(segment_list)} đoạn từ '{detected_lang}' sang '{target_norm}'...")
            translated_lines = []
            t_index = 1
            for seg in segment_list:
                translated_text = translate_text(seg["text"], detected_lang, target_norm)
                translated_lines.append(str(t_index))
                translated_lines.append(f"{seg['start']} --> {seg['end']}")
                translated_lines.append(translated_text)
                translated_lines.append("")
                print(f"[{seg['start']} --> {seg['end']}] {translated_text}")
                t_index += 1

        base_path, ext = os.path.splitext(output_path)
        translated_path = f"{base_path}_{target_language}{ext}"

        if not save_srt_file(translated_path, translated_lines):
            sys.exit(5)

        print(f"OK: Translated subtitle file created at {translated_path}")

    sys.exit(0)


if __name__ == "__main__":
    main()

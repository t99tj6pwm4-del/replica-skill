#!/usr/bin/env python3
"""Whisper transcription with word-level timestamps (faster-whisper, runs on CPU).

    python3 scripts/transcribe.py <audio-or-video> <out.json>

Model: WHISPER_MODEL env var (default small.en). English only.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import die, rel, resolve, save_json  # noqa: E402


def transcribe(src: Path) -> dict:
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        die("faster-whisper is not installed. Run: bash scripts/setup.sh")
    model = WhisperModel(os.environ.get("WHISPER_MODEL", "small.en"), device="cpu", compute_type="int8")
    # decode with ffmpeg ourselves: works for any audio/video file and any PyAV version
    import subprocess
    import numpy as np
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    segments, _ = model.transcribe(
        np.frombuffer(pcm, dtype=np.float32), language="en", word_timestamps=True, vad_filter=True,
        condition_on_previous_text=False,
    )
    out = {"source": rel(src), "segments": [], "words": []}
    for seg in segments:
        if seg.no_speech_prob > 0.8:
            continue
        out["segments"].append({"start": round(seg.start, 2), "end": round(seg.end, 2), "text": seg.text.strip()})
        for w in seg.words or []:
            text = w.word.strip()
            if text and w.probability >= 0.08 and w.end - w.start >= 0.04:  # drop Whisper "ghost" words
                out["words"].append({"text": text, "start": round(w.start, 3), "end": round(w.end, 3)})
    out["text"] = " ".join(s["text"] for s in out["segments"])
    return out


if __name__ == "__main__":
    if len(sys.argv) != 3:
        die("usage: transcribe.py <audio-or-video> <out.json>")
    result = transcribe(resolve(sys.argv[1]))
    save_json(resolve(sys.argv[2]), result)
    print(f"{len(result['words'])} words -> {sys.argv[2]}")
    print(result["text"][:600])

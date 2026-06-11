"""Assemble the Shadow-Omega Copilot certificate demo video.

Builds from generated PNG frames and local SAPI narration without screen
recording or desktop input.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).parent
OUT = HERE / "certificate_out"
FINAL = HERE / "shadow-omega-copilot-certificate-demo.mp4"
SILENT = HERE / "_certificate_silent.mp4"
NARRATION = HERE / "narration-copilot-certificate.wav"
CONCAT = HERE / "certificate-concat.txt"

SCENES = [
    ("00_title.png", 7.0),
    ("01_gap_closed.png", 11.0),
    ("02_fixture.png", 12.0),
    ("03_mcp_surface.png", 12.0),
    ("04_vote_matrix.png", 13.0),
    ("05_closed_loop.png", 14.0),
    ("06_rule_export.png", 11.0),
    ("07_judge_lens.png", 11.0),
    ("08_close.png", 9.0),
]


def run(cmd: list[str], label: str) -> None:
    print(f"[{label}] {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout[-2000:])
        print(result.stderr[-4000:])
        sys.exit(result.returncode)
    print(f"[{label}] OK")


def main() -> None:
    missing = [name for name, _ in SCENES if not (OUT / name).exists()]
    if missing:
        print(f"[ERROR] Missing frames: {missing}")
        print("Run: python demo/video/generate-copilot-certificate-frames.py")
        sys.exit(1)

    lines: list[str] = []
    for name, duration in SCENES:
        lines.append(f"file '{(OUT / name).as_posix()}'")
        lines.append(f"duration {duration}")
    lines.append(f"file '{(OUT / SCENES[-1][0]).as_posix()}'")
    CONCAT.write_text("\n".join(lines), encoding="utf-8")

    run([
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0", "-i", str(CONCAT),
        "-fps_mode", "cfr", "-r", "30",
        "-vf", "scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2",
        "-pix_fmt", "yuv420p",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        str(SILENT),
    ], "encode-video")

    if NARRATION.exists():
        run([
            "ffmpeg", "-y",
            "-i", str(SILENT),
            "-i", str(NARRATION),
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "128k",
            str(FINAL),
        ], "mux-audio")
        SILENT.unlink(missing_ok=True)
    else:
        SILENT.replace(FINAL)
        print("[warn] narration missing; wrote silent video")

    size_mb = FINAL.stat().st_size / 1024 / 1024
    total_s = sum(duration for _, duration in SCENES)
    print(f"[done] {FINAL}")
    print(f"       scenes: {len(SCENES)} | visual duration: {total_s:.0f}s | size: {size_mb:.1f} MB")


if __name__ == "__main__":
    main()

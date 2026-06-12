# 05.05.26

import logging
import subprocess
from pathlib import Path
from typing import Tuple

from VibraVid.utils.os import os_manager
from VibraVid.setup import get_ffprobe_path
from VibraVid.setup import get_mp4dump_path



logger = logging.getLogger(__name__)
_MP4DUMP_SCAN_BYTES = 1 * 1024 * 1024  # 1 MB


def _ffprobe_streams(ffprobe: str, file_path: str) -> Tuple[bool, str]:
    """Return (ok, message). ok=True means at least one decodable stream."""
    try:
        result = subprocess.run(
            [
                ffprobe,
                "-v",
                "error",
                "-show_streams",
                file_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return False, "ffprobe timed out"
    
    except Exception as exc:
        return False, f"ffprobe failed to launch: {exc}"

    output = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0:
        return False, f"ffprobe exit={result.returncode}: {output.strip()[:200]}"

    streams: list[dict[str, str]] = []
    current: dict[str, str] = {}
    for line in output.splitlines():
        line = line.strip()
        if line == "[STREAM]":
            current = {}
        elif line == "[/STREAM]":
            streams.append(current)
            current = {}
        elif "=" in line:
            key, _, value = line.partition("=")
            current[key.strip()] = value.strip()

    if not streams:
        return False, "ffprobe reported no streams"

    media_streams = [s for s in streams if s.get("codec_type", "") in {"video", "audio", "subtitle"}]
    if not media_streams:
        codec_names = ", ".join(s.get("codec_name", "?") for s in streams) or "(none)"
        return False, f"no audio/video stream (codec_type=data only): {codec_names}"

    bad = [s for s in media_streams if s.get("codec_name", "unknown") in {"unknown", "none", ""}]
    if bad:
        return False, "ffprobe still reports unknown codec — file likely encrypted"

    summary = ", ".join(f"{s.get('codec_type','?')}={s.get('codec_name','?')}" for s in media_streams)
    return True, summary


def _mp4dump_clean(mp4dump: str, file_path: str) -> Tuple[bool, str]:
    """
    Best-effort encryption-residue scan with Bento4's mp4dump.
    """
    try:
        with open(file_path, "rb") as fh:
            head = fh.read(_MP4DUMP_SCAN_BYTES)

        with os_manager.temp_binary_file(head, suffix=".mp4") as tmp_path:
            result = subprocess.run(
                [mp4dump, "--verbosity", "0", tmp_path],
                capture_output=True,
                timeout=5,
            )

    except Exception as exc:
        return True, f"mp4dump failed to launch: {exc} (skipped)"

    if result.returncode != 0:
        return True, "mp4dump non-zero exit (skipped)"

    text = ""
    for enc in ("utf-8", "utf-16", "utf-16-le", "latin-1"):
        try:
            text = result.stdout.decode(enc).lstrip("\ufeff")
            break
        except UnicodeDecodeError:
            continue
    if not text:
        return True, "mp4dump produced no decodable output (skipped)"

    flagged = [
        marker
        for marker in ("[encv]", "[enca]", "[sinf]", "[saiz]", "[saio]", "[senc]")
        if marker in text.lower()
    ]
    if flagged:
        return False, f"residual encryption boxes: {','.join(flagged)}"
    return True, "no residual encryption boxes"


def _scan_mp4_boxes_for_encryption(file_path: str, max_bytes: int = 4 * 1024 * 1024) -> Tuple[bool, str]:
    """
    Lightweight, dependency-free scan: read up to *max_bytes* of the file and
    look for fully-decrypted hallmarks (no [encv]/[enca]/[sinf]/[saiz]/[saio]/[senc]
    boxes inside moov/moof) without invoking external tools.
    """
    try:
        with open(file_path, "rb") as fh:
            data = fh.read(max_bytes)
    except Exception as exc:
        return True, f"box scan skipped: {exc}"

    if not data:
        return True, "box scan skipped: empty"

    encryption_types = {b"encv", b"enca", b"sinf", b"saiz", b"saio", b"senc"}
    found = set()
    pos = 0
    end = len(data)
    while pos + 8 <= end:
        size = int.from_bytes(data[pos:pos + 4], "big")
        type_ = data[pos + 4:pos + 8]
        
        if size == 1:
            if pos + 16 > end:
                break
            size = int.from_bytes(data[pos + 8:pos + 16], "big")
        
        if size <= 0:
            break

        if type_ in encryption_types:
            found.add(type_.decode("ascii"))

        pos += size

    if not found:
        for marker in encryption_types:
            if marker in data:
                found.add(marker.decode("ascii"))

    if found:
        return False, f"residual encryption boxes detected: {','.join(sorted(found))}"
    return True, "no residual encryption boxes (built-in scan)"


def verify_decrypted_media(file_path) -> Tuple[bool, str]:
    """
    Verify that *file_path* is a playable, fully decrypted media file.
    """
    p = Path(file_path)
    if not p.exists():
        return False, "output file missing"
    
    if p.stat().st_size == 0:
        return False, "output file is empty"

        
    ffprobe_path = get_ffprobe_path()
    mp4dump_path = get_mp4dump_path()

    ok, ffprobe_msg = _ffprobe_streams(ffprobe_path, str(p))
    if not ok:
        return False, ffprobe_msg

    mp4dump_msg = ""
    if mp4dump_path:
        clean, mp4dump_msg = _mp4dump_clean(mp4dump_path, str(p))
        if not clean:
            return False, f"{ffprobe_msg}; {mp4dump_msg}"
        if "skipped" not in mp4dump_msg:
            return True, f"{ffprobe_msg}; {mp4dump_msg}"

    # Fallback: built-in box scanner
    clean, scan_msg = _scan_mp4_boxes_for_encryption(str(p))
    if not clean:
        return False, f"{ffprobe_msg}; {scan_msg}"
    
    detail = scan_msg if not mp4dump_msg else f"{mp4dump_msg}; {scan_msg}"
    return True, f"{ffprobe_msg}; {detail}"
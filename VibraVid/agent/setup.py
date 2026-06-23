import os
import platform
import shutil
import tarfile
import tempfile
import zipfile
from pathlib import Path
from typing import Optional, Tuple

from VibraVid.utils.http_client import create_client, get_headers


FFMPEG_STATIC_URLS = {
    ("linux", "x64"): "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
    ("linux", "arm64"): "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz",
    ("darwin", "x64"): "https://evermeet.cx/ffmpeg/getrelease/zip",
    ("darwin", "arm64"): "https://evermeet.cx/ffmpeg/getrelease/zip",
}

FFPROBE_STATIC_URLS = {
    ("linux", "x64"): "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz",
    ("linux", "arm64"): "https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz",
    ("darwin", "x64"): "https://evermeet.cx/ffprobe/getrelease/zip",
    ("darwin", "arm64"): "https://evermeet.cx/ffprobe/getrelease/zip",
}


def _detect_system() -> str:
    return platform.system().lower()


def _detect_arch() -> str:
    machine = platform.machine().lower()
    return {"amd64": "x64", "x86_64": "x64", "arm64": "arm64", "aarch64": "arm64"}.get(machine, "x64")


def get_binary_dir() -> str:
    system = _detect_system()
    home = os.path.expanduser("~")
    if system == "windows":
        return os.path.join(os.path.splitdrive(home)[0] + os.path.sep, "binary")
    elif system == "darwin":
        return os.path.join(home, "Applications", "binary")
    else:
        return os.path.join(home, ".local", "bin", "binary")


def check_dependencies() -> Tuple[bool, Optional[str]]:
    """Check if FFmpeg and FFprobe are available.

    Returns:
        (ok, missing_path) - ok=True if both exist, missing_path is the path of the first missing binary.
    """
    binary_dir = get_binary_dir()
    for binary in ("ffmpeg", "ffprobe"):
        path = os.path.join(binary_dir, binary)
        if not os.path.isfile(path) or os.path.getsize(path) == 0:
            return False, path
    return True, None


def _download_and_extract(url: str, extract_dir: str, binary_name: str) -> Optional[str]:
    """Download archive from url, extract, and return path to binary_name inside extract_dir."""
    with create_client(headers=get_headers(), timeout=300, follow_redirects=True) as client:
        response = client.get(url)
        response.raise_for_status()
        content = response.content

    if url.endswith(".tar.xz") or url.endswith(".tar.gz"):
        with tempfile.NamedTemporaryFile(suffix=".tar.xz", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            with tarfile.open(tmp_path, "r:*") as tar:
                tar.extractall(extract_dir)
        finally:
            os.unlink(tmp_path)
    elif url.endswith(".zip"):
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            with zipfile.ZipFile(tmp_path, "r") as zf:
                zf.extractall(extract_dir)
        finally:
            os.unlink(tmp_path)
    else:
        with open(os.path.join(extract_dir, binary_name), "wb") as f:
            f.write(content)
        return os.path.join(extract_dir, binary_name)

    for root, _, files in os.walk(extract_dir):
        if binary_name in files:
            return os.path.join(root, binary_name)
    return None


def setup_ffmpeg(quiet: bool = True) -> dict:
    """Download FFmpeg and FFprobe to the binary directory.

    Returns:
        dict with 'success' bool, 'installed' list, 'error' optional.
    """
    system = _detect_system()
    arch = _detect_arch()
    binary_dir = get_binary_dir()
    os.makedirs(binary_dir, exist_ok=True)

    installed = []

    if system not in ("linux", "darwin"):
        return {
            "success": False,
            "installed": installed,
            "error": f"Auto-setup not supported on {system}. Install FFmpeg manually: https://ffmpeg.org/download.html"
        }

    for binary in ("ffmpeg", "ffprobe"):
        target = os.path.join(binary_dir, binary)
        if os.path.isfile(target) and os.path.getsize(target) > 0:
            installed.append(binary)
            continue

        url_map = FFMPEG_STATIC_URLS if binary == "ffmpeg" else FFPROBE_STATIC_URLS
        url = url_map.get((system, arch))
        if not url:
            return {
                "success": False,
                "installed": installed,
                "error": f"No static URL for {binary} on {system}/{arch}"
            }

        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                bin_path = _download_and_extract(url, tmpdir, binary)
                if not bin_path:
                    return {
                        "success": False,
                        "installed": installed,
                        "error": f"Binary '{binary}' not found in archive from {url}"
                    }
                shutil.copy2(bin_path, target)
                if system != "windows":
                    os.chmod(target, 0o755)
                installed.append(binary)
        except Exception as e:
            return {
                "success": False,
                "installed": installed,
                "error": f"Failed to download {binary}: {e}"
            }

    return {"success": True, "installed": installed, "error": None}

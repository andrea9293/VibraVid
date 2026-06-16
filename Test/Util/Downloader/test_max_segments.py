# 16.06.26
# ruff: noqa: E402

import sys
from pathlib import Path


workspace_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(workspace_root))


from VibraVid.core.ui.tracker import context_tracker
from VibraVid.core.downloader.hls import HLS_Downloader
from VibraVid.core.downloader._generic import Generic_Downloader


# ── Tiny assert harness (script-style, like the other Util tests) ────────────
_results = {"pass": 0, "fail": 0}


def check(name: str, got, expected) -> None:
    ok = got == expected
    _results["pass" if ok else "fail"] += 1
    status = "[PASS]" if ok else "[FAIL]"
    print(f"{status} {name}")
    if not ok:
        print(f"        expected: {expected!r}")
        print(f"        got:      {got!r}")


def reset_ctx():
    context_tracker.max_segments = None
    context_tracker.max_time = None


# ─────────────────────────────────────────────────────────────────────────────
def run_hls_tests():
    print("\n" + "=" * 70)
    print("max_segments / max_time propagation - HLS_Downloader")
    print("=" * 70)

    # Explicit constructor arg always wins over context_tracker.
    reset_ctx()
    context_tracker.max_segments = 9
    d = HLS_Downloader(m3u8_url="https://example/playlist.m3u8", max_segments=3)
    check("explicit max_segments wins over context", d.max_segments, 3)

    # No explicit arg -> falls back to the CLI-wide value on context_tracker.
    reset_ctx()
    context_tracker.max_segments = 7
    d = HLS_Downloader(m3u8_url="https://example/playlist.m3u8")
    check("max_segments falls back to context", d.max_segments, 7)

    # Nothing set anywhere -> None (download everything).
    reset_ctx()
    d = HLS_Downloader(m3u8_url="https://example/playlist.m3u8")
    check("max_segments None when unset", d.max_segments, None)

    # max_time falls back and is parsed to seconds.
    reset_ctx()
    context_tracker.max_time = "00:00:30"
    d = HLS_Downloader(m3u8_url="https://example/playlist.m3u8")
    check("max_time falls back and parses to seconds", d.max_time, 30.0)


def run_generic_tests():
    print("\n" + "=" * 70)
    print("max_segments / max_time propagation - Generic_Downloader")
    print("=" * 70)

    reset_ctx()
    context_tracker.max_segments = 4
    d = Generic_Downloader(sources=[{"url": "https://example/file.mp4", "protocol": "mp4"}])
    check("Generic max_segments falls back to context", d.max_segments, 4)

    reset_ctx()
    d = Generic_Downloader(sources=[{"url": "https://example/file.mp4", "protocol": "mp4"}], max_segments=2)
    check("Generic explicit max_segments wins", d.max_segments, 2)


if __name__ == "__main__":
    try:
        run_hls_tests()
        run_generic_tests()
    finally:
        reset_ctx()

    print("\n" + "=" * 80)
    print(f"RESULTS: {_results['pass']} passed, {_results['fail']} failed")
    print("=" * 80)
    sys.exit(1 if _results["fail"] else 0)
# 16.06.26
# ruff: noqa: E402

import sys
from pathlib import Path


workspace_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(workspace_root))


import VibraVid.services._base.tv_display_manager as tdm


# ── Tiny assert harness (script-style, like the Selector tests) ──────────────
_results = {"pass": 0, "fail": 0}


def check(name: str, got, expected) -> None:
    ok = got == expected
    _results["pass" if ok else "fail"] += 1
    status = "[PASS]" if ok else "[FAIL]"
    print(f"{status} {name}")
    if not ok:
        print(f"        expected: {expected!r}")
        print(f"        got:      {got!r}")


def episode(fmt: str, **kwargs):
    """Render an episode path with EPISODE_FORMAT = fmt, return (path_components, filename)."""
    tdm.EPISODE_FORMAT = fmt
    series = kwargs.pop("series", "Naruto")
    year = kwargs.pop("year", None)
    season = kwargs.pop("season", 1)
    ep = kwargs.pop("episode", 5)
    ep_name = kwargs.pop("name", "Il Test")
    return tdm.map_episode_path(series, year, season, ep, ep_name, **kwargs)


def movie(fmt: str, title="Inception", year=None):
    tdm.MOVIE_FORMAT = fmt
    return tdm.map_movie_path(title, year)


# ── TMDB stubbing (keep tests offline / deterministic) ───────────────────────
def stub_tmdb_found():
    tdm.tmdb_client.get_type_and_id_by_slug_year = lambda *a, **k: {"type": "tv", "id": 999}
    tdm.tmdb_client.get_imdb_id = lambda *a, **k: "tt1234567"
    tdm.tmdb_client.get_original_title = lambda *a, **k: "Original Name"
    tdm.tmdb_client.get_original_language = lambda *a, **k: "ja"


def stub_tmdb_not_found():
    tdm.tmdb_client.get_type_and_id_by_slug_year = lambda *a, **k: None


# ─────────────────────────────────────────────────────────────────────────────
def run_episode_basic_tests():
    print("\n" + "=" * 70)
    print("EPISODE FORMAT - basics & padding")
    print("=" * 70)

    pc, fn = episode("%(series_name)/S%(season:02d)/%(episode_name) S%(season:02d)E%(episode:02d)", season=2, episode=1)
    check("default format", (pc, fn), (["Naruto", "S02"], "Il Test S02E01"))

    pc, fn = episode("%(series_name)/Season %(season:02d)/%(series_name) - S%(season:02d)E%(episode:02d) - %(episode_name)", season=2, episode=1)
    check("Sonarr-style 'Season 02' folder", (pc, fn), (["Naruto", "Season 02"], "Naruto - S02E01 - Il Test"))

    pc, fn = episode("%(series_name)/S%(season:d)/E%(episode:03d)", season=3, episode=7)
    check("padding variants :d and :03d", (pc, fn), (["Naruto", "S3"], "E007"))

    pc, fn = episode("%(series_name) (%(series_year))/%(episode_name)", year="2002", episode=1)
    check("series_year present", (pc, fn), (["Naruto (2002)"], "Il Test"))

    pc, fn = episode("%(series_name) (%(series_year))/%(episode_name)", year=None)
    check("series_year absent strips parens", (pc, fn), (["Naruto"], "Il Test"))


def run_absolute_tests():
    print("\n" + "=" * 70)
    print("EPISODE FORMAT - %(absolute) anime numbering")
    print("=" * 70)

    pc, fn = episode("%(series_name)/%(episode_name) E%(absolute:03d)", absolute_number=42)
    check("absolute padded :03d", (pc, fn), (["Naruto"], "Il Test E042"))

    pc, fn = episode("%(series_name)/%(episode_name) E%(absolute:d)", absolute_number=7)
    check("absolute no padding :d", (pc, fn), (["Naruto"], "Il Test E7"))

    pc, fn = episode("%(series_name)/%(episode_name) [%(absolute:03d)]")
    check("absolute missing -> token+wrapper stripped", (pc, fn), (["Naruto"], "Il Test"))


def run_strip_tests():
    print("\n" + "=" * 70)
    print("EPISODE FORMAT - unknown-token strip & media-token preservation")
    print("=" * 70)

    pc, fn = episode("%(series_name)/%(episode_name) [%(bogus)] S%(season:02d)E%(episode:02d)")
    check("unknown token + wrapper removed", (pc, fn), (["Naruto"], "Il Test S01E05"))

    pc, fn = episode("%(series_name)/%(episode_name) S%(season:02d)E%(episode:02d) [%(quality)-%(video_codec)]")
    check(
        "media tokens preserved for _finalize",
        (pc, fn),
        (["Naruto"], "Il Test S01E05 [%(quality)-%(video_codec)]"),
    )

    pc, fn = episode("%(series_name)/%(episode_name) S%(season:02d)E%(episode:02d) %(language) %(audio_codec)")
    check(
        "language & audio_codec preserved",
        (pc, fn),
        (["Naruto"], "Il Test S01E05 %(language) %(audio_codec)"),
    )

    pc, fn = episode("%(series_name)/%(episode_name)", name=None)
    check("missing episode_name token stripped", (pc, fn), (["Naruto"], ""))


def run_tmdb_tests():
    print("\n" + "=" * 70)
    print("EPISODE/MOVIE FORMAT - TMDB tokens (stubbed)")
    print("=" * 70)

    stub_tmdb_found()
    pc, fn = episode("%(series_name) [%(imdb_id)] (%(tmdb_id))/%(episode_name) {%(original_title)} %(original_language)", episode=1)
    check(
        "TMDB tokens resolved",
        (pc, fn),
        (["Naruto [tt1234567] (999)"], "Il Test {Original Name} ja"),
    )

    stub_tmdb_not_found()
    pc, fn = episode("%(series_name) [%(imdb_id)]/%(episode_name) (%(tmdb_id))", episode=1)
    check(
        "TMDB not found -> tokens+wrappers stripped",
        (pc, fn),
        (["Naruto"], "Il Test"),
    )


def run_movie_tests():
    print("\n" + "=" * 70)
    print("MOVIE FORMAT")
    print("=" * 70)

    pc, fn = movie("%(title_name) (%(title_year))/%(title_name) (%(title_year))", year="2010")
    check("default movie format", (pc, fn), (["Inception (2010)"], "Inception (2010)"))

    pc, fn = movie("%(title_name) (%(title_year))", year=None)
    check("movie year absent strips parens", (pc, fn), ([], "Inception"))


if __name__ == "__main__":
    run_episode_basic_tests()
    run_absolute_tests()
    run_strip_tests()
    run_tmdb_tests()
    run_movie_tests()

    print("\n" + "=" * 80)
    print(f"RESULTS: {_results['pass']} passed, {_results['fail']} failed")
    print("=" * 80)
    sys.exit(1 if _results["fail"] else 0)
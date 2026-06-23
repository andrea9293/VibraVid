import argparse
import sys
import subprocess
from VibraVid.services._base import load_search_functions
from VibraVid.agent.job_manager import JobManager
from VibraVid.agent.output import output_json


EXAMPLES = """examples:
  vibravid-agent download --provider streamingcommunity --query "Breaking Bad" --id 34974 --season 1 --episode "1-5"
  vibravid-agent download --provider streamingcommunity --query "The Matrix" --video best
  vibravid-agent download --url "https://example.com/video.m3u8" --header "Referer: https://example.com"
  vibravid-agent download --provider 0 --query "Inception" --background
  vibravid-agent download --url "https://..." --license-url "https://..." --key aaaa:bbbb --drm widevine"""


def register(subparsers):
    parser = subparsers.add_parser(
        "download",
        help="Download media",
        description="Download media by provider, title, or direct URL",
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    group_media = parser.add_argument_group("media identification")
    group_media.add_argument("--provider", "-p", help="Provider name or index")
    group_media.add_argument("--query", "-q", help="Title to search for on the provider")
    group_media.add_argument("--id", help="Media ID from search results (to select when multiple results match)")
    group_media.add_argument("--url", help="Direct URL to download (bypasses provider search)")

    group_select = parser.add_argument_group("content selection")
    group_select.add_argument("--season", help="Season selection (e.g., '1', '1-3', '*')")
    group_select.add_argument("--episode", help="Episode selection (e.g., '1', '1-5', '*')")
    group_select.add_argument("--year", help="Year filter (e.g., '2020' or '1990-2015')")

    group_tracks = parser.add_argument_group("track preferences")
    group_tracks.add_argument("--video", "-sv", help="Video track filter (best, 1080, 720, ...)")
    group_tracks.add_argument("--audio", "-sa", help="Audio track filter (ita|eng, ...)")
    group_tracks.add_argument("--subtitle", "-ss", help="Subtitle track filter (ita|eng, ...)")
    group_tracks.add_argument("--extension", help="Output container (mkv, mp4)")

    group_direct = parser.add_argument_group("direct URL options")
    group_direct.add_argument("--header", action="append", help="HTTP header (repeatable)")
    group_direct.add_argument("--license-url", help="DRM license server URL")
    group_direct.add_argument("--key", action="append", help="Decryption key KID:KEY (repeatable)")
    group_direct.add_argument("--drm", choices=["widevine", "playready", "auto"], default="auto", help="DRM system")

    group_exec = parser.add_argument_group("execution")
    group_exec.add_argument("--background", action="store_true", help="Run in background")
    group_exec.add_argument("--use-proxy", action="store_true", help="Use configured proxy")


def _resolve_provider(search_functions, provider_key):
    if provider_key.isdigit():
        for func in search_functions.values():
            if str(func.indice) == provider_key:
                return func
    for func in search_functions.values():
        if func.module_name.lower() == provider_key.lower():
            return func
    return None


def _apply_track_overrides(args):
    from VibraVid.utils import config_manager
    if args.video:
        config_manager.config.set_key("DOWNLOAD", "select_video", args.video)
    if args.audio:
        config_manager.config.set_key("DOWNLOAD", "select_audio", args.audio)
    if args.subtitle:
        config_manager.config.set_key("DOWNLOAD", "select_subtitle", args.subtitle)
    if args.extension:
        config_manager.config.set_key("PROCESS", "extension", args.extension)
    if args.use_proxy:
        config_manager.config.set_key("REQUESTS", "use_proxy", True)


def _build_selections(args):
    selections = {}
    if args.season is not None:
        selections["season"] = args.season
    if args.episode is not None:
        selections["episode"] = args.episode
    if args.year is not None:
        selections["year"] = args.year
    return selections


def _find_item_by_id(database, target_id):
    if not database or not hasattr(database, "media_list") or not database.media_list:
        return None
    if target_id is None:
        return database.media_list[0]
    for item in database.media_list:
        if str(getattr(item, "id", "")) == str(target_id):
            return item
    return None


def _download_direct_url(args):
    from VibraVid.cli.command.download import handle_direct_download

    class _Args:
        pass
    fake = _Args()
    fake.down = args.url
    fake.output = None
    fake.headers = args.header or []
    fake.license_url = args.license_url
    fake.license_headers = []
    fake.key = args.key or []
    fake.drm = args.drm or "auto"
    fake.max_segments = None
    fake.max_time = None

    handle_direct_download(fake)


def execute(args):
    try:
        _apply_track_overrides(args)

        if args.url:
            if args.background:
                job_manager = JobManager()
                job_id = job_manager.create_job(
                    command=["vibravid-agent", "download", "--url", args.url],
                    title=args.url[:64],
                    output_path="pending"
                )
                process = subprocess.Popen(
                    [sys.executable, "agent.py", "download", "--url", args.url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                job_manager.update_job(job_id, pid=process.pid)
                output_json(True, data={"job_id": job_id, "status": "started", "pid": process.pid})
                return

            _download_direct_url(args)
            output_json(True, data={"status": "completed"})
            return

        if not args.provider:
            output_json(False, error="Provide --url or --provider with --query / --id")
            return

        search_functions = load_search_functions()
        search_func = _resolve_provider(search_functions, str(args.provider))
        if search_func is None:
            output_json(False, error=f"Provider not found: {args.provider}")
            return

        query = args.query or args.id
        if not query:
            output_json(False, error="Provide --query (title) or --id")
            return

        database = search_func(query, get_onlyDatabase=True)
        if not database or not hasattr(database, "media_list") or not database.media_list:
            output_json(False, error=f"No results for: {query}")
            return

        media_item = _find_item_by_id(database, args.id)
        if media_item is None:
            ids = [str(getattr(i, "id", "")) for i in database.media_list]
            output_json(False, error=f"ID not found: {args.id}. Available IDs: {ids}")
            return

        item_dict = media_item.__dict__.copy() if hasattr(media_item, "__dict__") else {}
        selections = _build_selections(args)
        title = getattr(media_item, "name", None) or query

        if args.background:
            job_manager = JobManager()
            cmd_parts = [sys.executable, "agent.py", "download",
                         "--provider", search_func.module_name, "--query", query]
            if args.id:
                cmd_parts.extend(["--id", args.id])
            if args.season:
                cmd_parts.extend(["--season", args.season])
            if args.episode:
                cmd_parts.extend(["--episode", args.episode])
            if args.year:
                cmd_parts.extend(["--year", args.year])
            job_id = job_manager.create_job(command=cmd_parts, title=title, output_path="pending")
            process = subprocess.Popen(cmd_parts, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            job_manager.update_job(job_id, pid=process.pid)
            output_json(True, data={"job_id": job_id, "status": "started", "pid": process.pid, "title": title})
            return

        search_func(direct_item=item_dict, selections=selections)

        output_json(True, data={
            "status": "completed",
            "provider": search_func.module_name,
            "id": str(getattr(media_item, "id", "")),
            "title": title,
        })

    except SystemExit:
        raise
    except Exception as e:
        output_json(False, error=str(e))

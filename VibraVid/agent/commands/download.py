import os
import sys
import subprocess
from VibraVid.agent.job_manager import JobManager
from VibraVid.agent.output import output_json


def register(subparsers):
    """Register download command."""
    parser = subparsers.add_parser("download", help="Download media")

    # Provider-based download
    parser.add_argument("--provider", "-p", help="Provider name or index")
    parser.add_argument("--id", help="Media ID to download")

    # Direct URL download
    parser.add_argument("--url", help="Direct URL to download")

    # Selection options
    parser.add_argument("--season", help="Season selection (e.g., '1', '1-3', '*')")
    parser.add_argument("--episode", help="Episode selection (e.g., '1', '1-5', '*')")
    parser.add_argument("--year", help="Year filter")

    # Track selection
    parser.add_argument("--video", "-sv", help="Video track filter (e.g., 'best', '1080')")
    parser.add_argument("--audio", "-sa", help="Audio track filter (e.g., 'ita|eng')")
    parser.add_argument("--subtitle", "-ss", help="Subtitle track filter (e.g., 'ita|eng')")
    parser.add_argument("--extension", help="Output container (mkv, mp4)")

    # Direct download options
    parser.add_argument("--header", action="append", help="HTTP header (repeatable)")
    parser.add_argument("--license-url", help="DRM license server URL")
    parser.add_argument("--key", action="append", help="Decryption key KID:KEY (repeatable)")
    parser.add_argument("--drm", choices=["widevine", "playready", "auto"], default="auto", help="DRM system")
    parser.add_argument("--max-segments", type=int, help="Limit to N segments")
    parser.add_argument("--max-time", help="Limit duration (HH:MM:SS or seconds)")

    # Execution options
    parser.add_argument("--background", action="store_true", help="Run in background")
    parser.add_argument("--use-proxy", action="store_true", help="Use configured proxy")


def execute(args):
    """Execute download command."""
    try:
        cmd = [sys.executable, "-m", "VibraVid"]

        if args.url:
            cmd.extend(["--down", args.url])
            if args.header:
                for h in args.header:
                    cmd.extend(["--headers", h])
            if args.license_url:
                cmd.extend(["--license-url", args.license_url])
            if args.key:
                for k in args.key:
                    cmd.extend(["--key", k])
            cmd.extend(["--drm", args.drm])
            if args.max_segments:
                cmd.extend(["--max-segments", str(args.max_segments)])
            if args.max_time:
                cmd.extend(["--max-time", args.max_time])
        elif args.provider and args.id:
            cmd.extend(["--site", args.provider, "--search", args.id, "--auto-first"])
            if args.season:
                cmd.extend(["--season", args.season])
            if args.episode:
                cmd.extend(["--episode", args.episode])
            if args.year:
                cmd.extend(["--year", args.year])
        else:
            output_json(False, error="Either --url or (--provider and --id) required")
            return

        if args.video:
            cmd.extend(["-sv", args.video])
        if args.audio:
            cmd.extend(["-sa", args.audio])
        if args.subtitle:
            cmd.extend(["-ss", args.subtitle])
        if args.extension:
            cmd.extend(["--extension", args.extension])
        if args.use_proxy:
            cmd.append("--use_proxy")

        cmd.extend(["--close-console", "true"])

        if args.background:
            job_manager = JobManager()
            job_id = job_manager.create_job(
                command=cmd,
                title=args.url or args.id or "download",
                output_path="pending"
            )

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

            job_manager.update_job(job_id, pid=process.pid)

            output_json(True, data={
                "job_id": job_id,
                "status": "started",
                "pid": process.pid
            })
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                output_json(True, data={
                    "status": "completed",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                })
            else:
                output_json(False, error=f"Download failed: {result.stderr}")

    except Exception as e:
        output_json(False, error=str(e))

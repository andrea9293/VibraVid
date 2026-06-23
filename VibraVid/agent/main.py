import os
import sys


def _suppress_stdout():
    sys.stdout.flush()
    sys.stdout = open(os.devnull, 'w')


def _restore_stdout(original):
    sys.stdout.close()
    sys.stdout = original


def main():
    """Main entry point for vibravid-agent CLI."""
    _stdout = sys.stdout

    _suppress_stdout()

    import argparse
    from VibraVid.agent.commands import providers, search, download, status, cancel, config, setup
    from VibraVid.agent.output import output_json
    from VibraVid.agent.setup import check_dependencies, setup_ffmpeg, get_binary_dir
    from VibraVid.upload.version import __version__, __title__

    _restore_stdout(_stdout)

    parser = argparse.ArgumentParser(
        prog="vibravid-agent",
        description="VibraVid Agent CLI - download media via structured JSON output.",
        epilog="Run 'vibravid-agent <command> --help' for details on each command.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{__title__} {__version__}"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        title="commands",
        description="Available commands:",
    )

    providers.register(subparsers)
    search.register(subparsers)
    download.register(subparsers)
    status.register(subparsers)
    cancel.register(subparsers)
    config.register(subparsers)
    setup.register(subparsers)

    args = parser.parse_args()

    if args.command != "setup":
        ok, missing = check_dependencies()
        if not ok:
            sys.stderr.write(
                f"First run: downloading FFmpeg/FFprobe to {get_binary_dir()}...\n"
            )
            sys.stderr.flush()
            result = setup_ffmpeg()
            if not result["success"]:
                output_json(False, error=result.get("error"), data=result)
                sys.exit(1)
            sys.stderr.write(f"Installed: {', '.join(result.get('installed', []))}\n")
            sys.stderr.flush()

    _suppress_stdout()

    try:
        commands = {
            "providers": providers.execute,
            "search": search.execute,
            "download": download.execute,
            "status": status.execute,
            "cancel": cancel.execute,
            "config": config.execute,
            "setup": setup.execute,
        }

        commands[args.command](args)

    except SystemExit:
        raise
    except Exception as e:
        output_json(False, error=str(e))

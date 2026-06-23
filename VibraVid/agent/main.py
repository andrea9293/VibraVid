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
    from VibraVid.agent.commands import providers, search, download, status, cancel, config
    from VibraVid.agent.output import output_json
    from VibraVid.upload.version import __version__, __title__

    _restore_stdout(_stdout)

    parser = argparse.ArgumentParser(
        prog="vibravid-agent",
        description="VibraVid CLI for AI agents - structured JSON output"
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{__title__} {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    providers.register(subparsers)
    search.register(subparsers)
    download.register(subparsers)
    status.register(subparsers)
    cancel.register(subparsers)
    config.register(subparsers)

    args = parser.parse_args()

    _suppress_stdout()

    try:
        commands = {
            "providers": providers.execute,
            "search": search.execute,
            "download": download.execute,
            "status": status.execute,
            "cancel": cancel.execute,
            "config": config.execute,
        }

        commands[args.command](args)

    except SystemExit:
        raise
    except Exception as e:
        output_json(False, error=str(e))

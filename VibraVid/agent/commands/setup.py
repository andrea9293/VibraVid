import argparse

from VibraVid.agent.setup import check_dependencies, setup_ffmpeg, get_binary_dir
from VibraVid.agent.output import output_json

SETUP_EXAMPLES = """examples:
  vibravid-agent setup"""


def register(subparsers):
    parser = subparsers.add_parser(
        "setup",
        help="Download FFmpeg/FFprobe dependencies",
        description="Download and install FFmpeg and FFprobe to the local binary directory. Runs automatically on first use.",
        epilog=SETUP_EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )


def execute(args):
    try:
        binary_dir = get_binary_dir()
        ok, missing = check_dependencies()
        if ok:
            output_json(True, data={
                "message": "All dependencies already installed",
                "binary_dir": binary_dir
            })
            return

        result = setup_ffmpeg()
        result["binary_dir"] = binary_dir
        if not result["success"]:
            output_json(False, error=result.get("error"), data=result)
            return
        output_json(True, data=result)
    except Exception as e:
        output_json(False, error=str(e))

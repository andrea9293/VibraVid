import argparse

from VibraVid.utils import config_manager
from VibraVid.agent.output import output_json

CONFIG_EXAMPLES = """examples:
  vibravid-agent config
  vibravid-agent config --get DOWNLOAD.thread_count
  vibravid-agent config --set DOWNLOAD.thread_count=20
  vibravid-agent config --dependencies"""


def register(subparsers):
    parser = subparsers.add_parser(
        "config",
        help="Show or modify configuration",
        description="View or change VibraVid configuration. Without arguments, shows the full config.",
        epilog=CONFIG_EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--get", help="Get value: SECTION.KEY (e.g., DOWNLOAD.thread_count)")
    parser.add_argument("--set", help="Set value: SECTION.KEY=VALUE")
    parser.add_argument("--dependencies", action="store_true", help="Show binary dependency paths")


def execute(args):
    """Execute config command."""
    try:
        if args.dependencies:
            from VibraVid.setup.system import (
                get_ffmpeg_path, get_ffprobe_path, get_bento4_decrypt_path,
                get_wvd_path, get_prd_path
            )

            deps = {
                "ffmpeg": get_ffmpeg_path(),
                "ffprobe": get_ffprobe_path(),
                "bento4": get_bento4_decrypt_path(),
                "widevine_device": get_wvd_path(),
                "playready_device": get_prd_path()
            }

            output_json(True, data={"dependencies": deps})

        elif args.get:
            parts = args.get.split(".")
            if len(parts) != 2:
                output_json(False, error="Invalid format. Use SECTION.KEY")
                return

            section, key = parts
            value = config_manager.config.get(section, key, None)
            output_json(True, data={"key": args.get, "value": value})

        elif args.set:
            if "=" not in args.set:
                output_json(False, error="Invalid format. Use SECTION.KEY=VALUE")
                return

            key_part, value_part = args.set.split("=", 1)
            parts = key_part.split(".")
            if len(parts) != 2:
                output_json(False, error="Invalid format. Use SECTION.KEY=VALUE")
                return

            section, key = parts

            try:
                import json
                value = json.loads(value_part)
            except Exception:
                value = value_part

            config_manager.config.set_key(section, key, value)
            config_manager.save_config()

            output_json(True, data={"key": key_part, "value": value})

        else:
            output_json(True, data={"config": config_manager.config._config_dict})

    except Exception as e:
        output_json(False, error=str(e))

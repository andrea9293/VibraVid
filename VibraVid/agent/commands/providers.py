import argparse

from VibraVid.services._base import load_search_functions
from VibraVid.agent.output import output_json

PROVIDERS_EXAMPLES = """examples:
  vibravid-agent providers
  vibravid-agent providers --available"""


def register(subparsers):
    parser = subparsers.add_parser(
        "providers",
        help="List available providers",
        description="List all installed streaming providers with their index, name, and content category.",
        epilog=PROVIDERS_EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--available", action="store_true", help="Only show available providers")


def execute(args):
    """Execute providers command."""
    try:
        search_functions = load_search_functions()
        providers = []

        for func in search_functions.values():
            category = (func.use_for or "").lower()
            providers.append({
                "index": func.indice,
                "name": func.module_name,
                "category": category,
                "available": True
            })

        if args.available:
            providers = [p for p in providers if p["available"]]

        output_json(True, data={"providers": providers})
    except Exception as e:
        output_json(False, error=str(e))

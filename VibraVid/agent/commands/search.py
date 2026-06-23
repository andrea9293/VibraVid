from VibraVid.services._base import load_search_functions
from VibraVid.agent.output import output_json


def register(subparsers):
    """Register search command."""
    parser = subparsers.add_parser("search", help="Search for titles")
    parser.add_argument("--query", "-q", required=True, help="Search query")
    parser.add_argument("--provider", "-p", required=True, help="Provider name or index")
    parser.add_argument("--year", help="Year filter (e.g., '2020' or '1990-2015')")
    parser.add_argument("--category", type=int, help="Category filter (1=Anime, 2=Movies/Series, 3=Series)")
    parser.add_argument("--auto-first", action="store_true", help="Auto-select first result")
    parser.add_argument("--global", dest="global_search", action="store_true", help="Search across all providers")


def execute(args):
    """Execute search command."""
    if not args.query:
        output_json(False, error="Query is required")
        return

    try:
        search_functions = load_search_functions()

        provider_key = str(args.provider).strip().lower()
        search_func = None

        if provider_key.isdigit():
            for func in search_functions.values():
                if str(func.indice) == provider_key:
                    search_func = func
                    break

        if search_func is None:
            for func in search_functions.values():
                if func.module_name.lower() == provider_key:
                    search_func = func
                    break

        if search_func is None:
            output_json(False, error=f"Provider not found: {args.provider}")
            return

        database = search_func(args.query, get_onlyDatabase=True)

        if not database or not hasattr(database, 'media_list') or not database.media_list:
            output_json(True, data={
                "query": args.query,
                "provider": args.provider,
                "results": []
            })
            return

        results = []
        for item in database.media_list:
            result_item = {
                "id": str(getattr(item, 'id', '')),
                "title": getattr(item, 'name', ''),
                "year": getattr(item, 'year', None),
                "type": getattr(item, 'type', 'unknown')
            }
            results.append(result_item)

        if args.year:
            results = [r for r in results if r.get('year') and str(r['year']) in args.year]

        output_json(True, data={
            "query": args.query,
            "provider": args.provider,
            "results": results
        })

    except Exception as e:
        output_json(False, error=str(e))

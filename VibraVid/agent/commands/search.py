from VibraVid.services._base import load_search_functions
from VibraVid.agent.output import output_json


CATEGORY_MAP = {
    1: "anime",
    2: "film_serie",
    3: "serie",
    4: "movie",
}


def register(subparsers):
    """Register search command."""
    parser = subparsers.add_parser("search", help="Search for titles")
    parser.add_argument("--query", "-q", required=True, help="Search query")
    parser.add_argument("--provider", "-p", help="Provider name or index (optional with --global)")
    parser.add_argument("--year", help="Year filter (e.g., '2020' or '1990-2015')")
    parser.add_argument("--category", type=int, help="Category filter (1=Anime, 2=Movies/Series, 3=Series)")
    parser.add_argument("--auto-first", action="store_true", help="Auto-select first result")
    parser.add_argument("--global", dest="global_search", action="store_true", help="Search across all providers")


def _resolve_provider(search_functions, provider_key):
    if provider_key.isdigit():
        for func in search_functions.values():
            if str(func.indice) == provider_key:
                return func
    for func in search_functions.values():
        if func.module_name.lower() == provider_key:
            return func
    return None


def _format_item(item, source_provider):
    return {
        "id": str(getattr(item, 'id', '')),
        "title": getattr(item, 'name', ''),
        "year": getattr(item, 'year', None),
        "type": getattr(item, 'type', 'unknown'),
        "provider": source_provider,
    }


def _matches_year(item, year_filter):
    if not year_filter:
        return True
    item_year = getattr(item, 'year', None)
    if item_year is None:
        return False
    item_year_str = str(item_year)
    if "-" in year_filter:
        try:
            lo, hi = year_filter.split("-", 1)
            return int(lo) <= int(item_year) <= int(hi)
        except ValueError:
            return item_year_str in year_filter
    return item_year_str in year_filter


def _search_one_provider(search_func, query, year_filter):
    database = search_func(query, get_onlyDatabase=True)
    if not database or not hasattr(database, 'media_list') or not database.media_list:
        return []
    return [
        item for item in database.media_list
        if _matches_year(item, year_filter)
    ]


def execute(args):
    """Execute search command."""
    if not args.query:
        output_json(False, error="Query is required")
        return

    try:
        search_functions = load_search_functions()
        results = []
        providers_searched = []

        if args.global_search or not args.provider:
            target_providers = list(search_functions.values())

            if args.category and args.category in CATEGORY_MAP:
                wanted = CATEGORY_MAP[args.category]
                target_providers = [
                    f for f in target_providers
                    if (getattr(f, '_use_for') or '').lower() == wanted
                ]

            for func in target_providers:
                try:
                    items = _search_one_provider(func, args.query, args.year)
                    for item in items:
                        results.append(_format_item(item, func.module_name))
                    providers_searched.append(func.module_name)
                except Exception:
                    continue

            output_json(True, data={
                "query": args.query,
                "mode": "global",
                "providers_searched": providers_searched,
                "results": results,
            })
            return

        provider_key = str(args.provider).strip().lower()
        search_func = _resolve_provider(search_functions, provider_key)

        if search_func is None:
            output_json(False, error=f"Provider not found: {args.provider}")
            return

        items = _search_one_provider(search_func, args.query, args.year)

        for item in items:
            results.append(_format_item(item, search_func.module_name))

        output_json(True, data={
            "query": args.query,
            "mode": "single",
            "provider": search_func.module_name,
            "results": results,
        })

    except Exception as e:
        output_json(False, error=str(e))

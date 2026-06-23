import sys
import json
from datetime import datetime, timezone
from typing import Any, Optional

from VibraVid.upload.version import __version__


def output_json(
    success: bool,
    data: Optional[Any] = None,
    error: Optional[str] = None,
    exit_on_call: bool = True
) -> dict:
    result = {
        "success": success,
        "data": data,
        "error": error,
        "metadata": {
            "version": __version__,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        }
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))

    if exit_on_call:
        sys.exit(0 if success else 1)

    return result

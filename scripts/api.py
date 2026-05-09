"""CLI: launch the retrieval-menu API server on 127.0.0.1:7117."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from medbrain.api.server import main


if __name__ == "__main__":
    main()

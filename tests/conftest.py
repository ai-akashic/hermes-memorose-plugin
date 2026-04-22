from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

HERMES_ROOT = Path("/Users/dylan/future/akashic/hermes-agent")
if str(HERMES_ROOT) not in sys.path:
    sys.path.insert(0, str(HERMES_ROOT))

MEMOROSE_SDK_ROOT = Path("/Users/dylan/future/akashic/memorose-sdk/python")
if str(MEMOROSE_SDK_ROOT) not in sys.path:
    sys.path.insert(0, str(MEMOROSE_SDK_ROOT))

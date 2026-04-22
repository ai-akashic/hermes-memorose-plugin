from __future__ import annotations

import json

try:
    from .config import load_memorose_config
    from .service import MemoroseService
except ImportError:
    from config import load_memorose_config
    from service import MemoroseService


def memorose_command(args) -> None:
    if getattr(args, "memorose_command", None) != "status":
        print("Usage: hermes memorose status")
        return
    cfg = load_memorose_config(args.hermes_home)
    service = MemoroseService(cfg, args.user_id, args.session_id)
    print(json.dumps(service.get_status(), indent=2))


def register_cli(subparser) -> None:
    subs = subparser.add_subparsers(dest="memorose_command")
    status = subs.add_parser("status", help="Show Memorose status")
    status.add_argument("--hermes-home", required=True)
    status.add_argument("--user-id", required=True)
    status.add_argument("--session-id", required=True)
    subparser.set_defaults(func=memorose_command)

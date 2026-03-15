from __future__ import annotations

import argparse
import json
import time

from app.worker import run_preview_job, run_render_job


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Video AI Studio worker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("serve")

    preview = subparsers.add_parser("preview")
    preview.add_argument("project_id")

    render = subparsers.add_parser("render")
    render.add_argument("project_id")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "serve":
        print(json.dumps({"status": "worker-ready", "mode": "mock-polling"}, indent=2), flush=True)
        try:
            while True:
                time.sleep(30)
                print(json.dumps({"status": "worker-heartbeat"}, indent=2), flush=True)
        except KeyboardInterrupt:
            return
    elif args.command == "preview":
        result = run_preview_job(args.project_id)
    else:
        result = run_render_job(args.project_id)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

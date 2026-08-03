"""Minimal JSON/HTTP reward server with explicit model placement."""

from __future__ import annotations

import argparse
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

try:
    from .reward_client import LocalRewardClient
except ImportError:  # Support direct execution from this directory.
    from reward_client import LocalRewardClient


def make_handler(client, auth_token: str | None, max_batch_size: int):
    model_lock = threading.Lock()

    class RewardHandler(BaseHTTPRequestHandler):
        server_version = "IwindReward/1"

        def _json(self, status: int, value: dict) -> None:
            body = json.dumps(value).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            if self.path == "/health":
                self._json(200, {"status": "ok"})
            else:
                self._json(404, {"error": "not found"})

        def do_POST(self) -> None:
            if self.path != "/score":
                self._json(404, {"error": "not found"})
                return
            if auth_token and self.headers.get("Authorization") != f"Bearer {auth_token}":
                self._json(401, {"error": "unauthorized"})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                prompts = payload["prompts"]
                completions = payload["completions"]
                if not isinstance(prompts, list) or len(prompts) > max_batch_size:
                    raise ValueError(f"Batch must be a list with at most {max_batch_size} items")
                with model_lock:
                    scores = client.score(prompts, completions, payload.get("metadata"))
                self._json(200, {"scores": scores})
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                self._json(400, {"error": str(error)})

        def log_message(self, format, *args):
            return

    return RewardHandler


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--device", required=True, help="Explicit device such as cuda:0 or cpu; 'rank' is allowed under a launcher")
    parser.add_argument("--max-length", type=int, default=2048)
    parser.add_argument("--max-batch-size", type=int, default=64)
    parser.add_argument("--adapter", choices=("scalar_logits", "quantile_mean"), default="scalar_logits")
    parser.add_argument("--auth-token-env", default="IWIND_REWARD_TOKEN")
    args = parser.parse_args()
    client = LocalRewardClient(args.model, args.max_length, device=args.device, adapter=args.adapter)
    handler = make_handler(client, os.environ.get(args.auth_token_env), args.max_batch_size)
    ThreadingHTTPServer((args.host, args.port), handler).serve_forever()


if __name__ == "__main__":
    main()

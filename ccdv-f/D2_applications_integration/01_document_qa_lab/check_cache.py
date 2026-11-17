"""Verify Claude cache creation and reuse through the running D2 app."""

import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen
from uuid import uuid4


SAMPLE = Path(__file__).with_name("samples") / "checkout-incident.md"
QUESTIONS = ["What triggered the rollback?", "When was availability restored?"]


def request(url: str, data: bytes | None = None, headers: dict | None = None):
    return urlopen(Request(url, data=data, headers=headers or {}), timeout=90)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    args = parser.parse_args()
    base = args.base_url.rstrip("/")
    with request(f"{base}/api/config") as response:
        config = json.load(response)
    if config["mode"] != "claude":
        raise SystemExit("Start the app with D2_PROVIDER=claude to measure API token usage.")

    # Vary the fixture between runs so the first question measures a cold prefix.
    document = SAMPLE.read_bytes() + f"\n\nCache exercise marker {uuid4().hex}\n".encode()
    with request(f"{base}/api/sessions", document, {
        "Content-Type": "text/plain", "X-Document-Name": SAMPLE.name,
    }) as response:
        session = json.load(response)

    usage = []
    print(f"{config['model']} | prompt {config['prompt_version']} | session {session['id']}")
    for question in QUESTIONS:
        data = json.dumps({"question": question}).encode()
        url = f"{base}/api/sessions/{session['id']}/questions"
        with request(url, data, {"Content-Type": "application/json"}) as response:
            for line in response:
                event = json.loads(line)
                if event["event"] == "error":
                    raise SystemExit(event["message"])
                if event["event"] == "done":
                    usage.append(event["turn"]["usage"])
                    print(f"{question} {json.dumps(usage[-1], sort_keys=True)}")
                    break
            else:
                raise SystemExit("Answer stream ended without a completion event.")

    first, second = usage
    if not first or not second or not first["cache_creation_input_tokens"] or not second["cache_read_input_tokens"]:
        raise SystemExit("Cache reuse was not verified. Check the printed token values.")
    print(f"Verified a cache hit on the second question ({second['cache_read_input_tokens']} cached input tokens).")


if __name__ == "__main__":
    main()

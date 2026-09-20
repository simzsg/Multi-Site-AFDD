import json
from pathlib import Path

from redis import Redis


def replay_jsonl(path: str | Path, *, client: Redis, stream: str) -> None:
    with open(path) as source:
        for line in source:
            payload = json.loads(line)
            client.xadd(stream, {"payload": json.dumps(payload)})

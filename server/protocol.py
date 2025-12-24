import json
from typing import Any, Dict

def encode_message(obj: Dict[str, Any]) -> bytes:
    return (json.dumps(obj, ensure_ascii=False) + "\n").encode("utf-8")

def decode_message(line: bytes) -> Dict[str, Any]:
    return json.loads(line.decode("utf-8"))

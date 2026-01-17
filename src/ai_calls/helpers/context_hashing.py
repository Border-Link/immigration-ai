import hashlib
import json
from typing import Any, Dict


def compute_context_hash(context_bundle: Dict[str, Any]) -> str:
    """
    Compute SHA-256 hash of context bundle for deterministic audits.

    Uses canonicalized JSON (sorted keys, no whitespace).
    """
    canonical_json = json.dumps(context_bundle, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


"""
src/security/audit.py
Tamper-evident, append-only Merkle hash chain audit ledger.
Every log entry is cryptographically linked to the previous one.
Tampering with any entry breaks chain verification.
"""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


@dataclass
class AuditEntry:
    """A single, immutable audit record."""
    timestamp:    str    # ISO 8601 UTC
    user_id:      str
    client_ip:    str
    action:       str
    input_sha256:  str   # SHA-256 of input raster bytes (or "N/A")
    output_sha256: str   # SHA-256 of output raster bytes (or "N/A")
    prev_hash:    str    # hash of previous entry (genesis = "0"*64)
    entry_hash:   str    # SHA-256(prev_hash + all fields)

    def to_dict(self) -> dict:
        return asdict(self)


class AuditLedger:
    """
    Append-only JSONL audit ledger with Merkle hash chain.

    Chain construction:
        entry_hash = SHA-256(prev_hash + JSON(all entry fields except entry_hash))

    Tamper detection:
        verify_chain() recomputes every hash in O(N) and returns False on
        any mismatch.

    Thread safety:
        Not thread-safe. Use a per-request lock or a dedicated audit
        microservice with a message queue in concurrent deployments.
    """

    GENESIS_HASH = "0" * 64  # Sentinel for the first entry

    def __init__(self, ledger_path: Path) -> None:
        self._path = ledger_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._last_hash = self._compute_current_tail()

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def log(
        self,
        user_id: str,
        client_ip: str,
        action: str,
        input_bytes: Optional[bytes] = None,
        output_bytes: Optional[bytes] = None,
    ) -> AuditEntry:
        """
        Append a new tamper-evident entry to the ledger.

        Args:
            user_id:      Authenticated user identifier (sub claim from JWT).
            client_ip:    Validated client IP address.
            action:       Human-readable action string (e.g., "register_image").
            input_bytes:  Raw bytes of the input artifact (or None).
            output_bytes: Raw bytes of the output artifact (or None).

        Returns:
            The fully constructed AuditEntry with Merkle hash.
        """
        ts = datetime.now(timezone.utc).isoformat()
        in_hash  = _sha256(input_bytes)  if input_bytes  else "N/A"
        out_hash = _sha256(output_bytes) if output_bytes else "N/A"

        # Build payload dict (everything except entry_hash)
        payload = {
            "timestamp":     ts,
            "user_id":       user_id,
            "client_ip":     client_ip,
            "action":        action,
            "input_sha256":  in_hash,
            "output_sha256": out_hash,
            "prev_hash":     self._last_hash,
        }

        # entry_hash = SHA-256(prev_hash || canonical JSON of payload)
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        entry_hash = hashlib.sha256(
            (self._last_hash + canonical).encode()
        ).hexdigest()

        entry = AuditEntry(**payload, entry_hash=entry_hash)

        # Atomically append to JSONL ledger
        with open(self._path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.to_dict()) + "\n")

        self._last_hash = entry_hash
        return entry

    def verify_chain(self) -> bool:
        """
        Re-derive every entry_hash in the ledger and verify the chain.
        Returns True only if the entire chain is intact (no tampering).
        """
        prev_hash = self.GENESIS_HASH
        try:
            entries = self._load_all()
        except Exception:
            return False

        for raw in entries:
            entry = dict(raw)
            stored_hash = entry.pop("entry_hash")

            # Recompute: same formula as log()
            canonical = json.dumps(
                {k: entry[k] for k in sorted(entry)},
                separators=(",", ":"),
            )
            recomputed = hashlib.sha256(
                (prev_hash + canonical).encode()
            ).hexdigest()

            if recomputed != stored_hash:
                return False
            if entry.get("prev_hash") != prev_hash:
                return False

            prev_hash = stored_hash

        return True

    def get_entries(self, limit: int = 100) -> list[AuditEntry]:
        """Return the most recent `limit` entries."""
        raw = self._load_all()
        return [AuditEntry(**r) for r in raw[-limit:]]

    def chain_length(self) -> int:
        """Return the total number of entries in the ledger."""
        return len(self._load_all())

    # -----------------------------------------------------------------------
    # Internal helpers
    # -----------------------------------------------------------------------

    def _load_all(self) -> list[dict]:
        if not self._path.exists():
            return []
        with open(self._path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]

    def _compute_current_tail(self) -> str:
        """Read the last entry_hash to resume the chain after restart."""
        entries = self._load_all()
        if not entries:
            return self.GENESIS_HASH
        return entries[-1].get("entry_hash", self.GENESIS_HASH)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

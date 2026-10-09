import hashlib
import json
import logging
import os
import time
from typing import Dict, Any, List, Optional, Tuple
from threading import Lock

logger = logging.getLogger("audit.immutable")

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


class AuditBlock:
    """
    Represents an immutable, cryptographically chained audit record.
    Any modification to previous blocks breaks the SHA-256 hash chain.
    """

    def __init__(
        self,
        index: int,
        timestamp_ns: int,
        tenant_id: str,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        payload: Dict[str, Any],
        previous_hash: str,
        current_hash: Optional[str] = None,
    ):
        self.index = index
        self.timestamp_ns = timestamp_ns
        self.tenant_id = tenant_id
        self.actor_id = actor_id
        self.action = action
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.payload = payload
        self.previous_hash = previous_hash
        self.current_hash = current_hash or self.compute_hash()

    def compute_hash(self) -> str:
        """
        Calculates SHA-256 hash over all canonical block fields.
        Uses deterministic JSON serialization with sorted keys.
        """
        canonical_payload = json.dumps(self.payload, sort_keys=True, separators=(",", ":"))
        header = (
            f"{self.index}|{self.timestamp_ns}|{self.tenant_id}|{self.actor_id}|"
            f"{self.action}|{self.resource_type}|{self.resource_id}|"
            f"{canonical_payload}|{self.previous_hash}"
        )
        return hashlib.sha256(header.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "timestamp_ns": self.timestamp_ns,
            "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(self.timestamp_ns / 1e9)),
            "tenant_id": self.tenant_id,
            "actor_id": self.actor_id,
            "action": self.action,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "payload": self.payload,
            "previous_hash": self.previous_hash,
            "current_hash": self.current_hash,
        }


class ImmutableAuditLogger:
    """
    Append-only cryptographically chained audit ledger.
    Enforces compliance with SOC 2 CC8.1 and IEC 62443 SR 7.6 audit trail requirements.
    """

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path
        self._chain: List[AuditBlock] = []
        self._lock = Lock()
        self._init_genesis()

    def _init_genesis(self):
        """Initializes Block 0 with fixed Genesis hash."""
        genesis = AuditBlock(
            index=0,
            timestamp_ns=1700000000000000000,
            tenant_id="system-root",
            actor_id="system",
            action="GENESIS_INITIALIZE",
            resource_type="LEDGER",
            resource_id="root",
            payload={"message": "AegisTwin Cryptographic Audit Ledger Initialized"},
            previous_hash=GENESIS_HASH,
        )
        self._chain.append(genesis)

    def log(
        self,
        tenant_id: str,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> AuditBlock:
        """
        Appends an event to the ledger, binding it to the previous block's SHA-256 digest.
        Thread-safe under concurrent execution.
        """
        payload = payload or {}
        now_ns = time.time_ns()

        with self._lock:
            last_block = self._chain[-1]
            new_index = len(self._chain)
            block = AuditBlock(
                index=new_index,
                timestamp_ns=now_ns,
                tenant_id=tenant_id,
                actor_id=actor_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                payload=payload,
                previous_hash=last_block.current_hash,
            )
            self._chain.append(block)

            # Persist to disk if path configured
            if self.storage_path:
                try:
                    os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
                    with open(self.storage_path, "a", encoding="utf-8") as f:
                        f.write(json.dumps(block.to_dict()) + "\n")
                except Exception as e:
                    logger.error(f"[Audit] Failed appending to disk ledger: {e}")

        logger.debug(f"[Audit] Appended block {block.index} ({action}) Hash: {block.current_hash[:12]}...")
        return block

    def verify_chain_integrity(self) -> Tuple[bool, Optional[str], Optional[int]]:
        """
        Cryptographically crawls the entire chain from genesis to head.
        Returns:
            (is_valid, error_message, tampered_block_index)
        """
        with self._lock:
            if not self._chain:
                return False, "Audit chain is empty", 0

            # 1. Verify Genesis
            if self._chain[0].previous_hash != GENESIS_HASH:
                return False, "Genesis block previous_hash tampered", 0

            for i in range(1, len(self._chain)):
                prev = self._chain[i - 1]
                curr = self._chain[i]

                # Check index continuity
                if curr.index != i:
                    return False, f"Broken sequence: block {i} has index {curr.index}", i

                # Check previous hash link
                if curr.previous_hash != prev.current_hash:
                    return (
                        False,
                        f"Hash link broken at block {i}: expected {prev.current_hash}, got {curr.previous_hash}",
                        i,
                    )

                # Check recomputed block digest
                expected_hash = curr.compute_hash()
                if curr.current_hash != expected_hash:
                    return (
                        False,
                        f"Block {i} payload or metadata tampered: recomputed hash does not match block header",
                        i,
                    )

        return True, "Cryptographic audit chain valid and untampered", None

    def get_entries(
        self,
        tenant_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """Returns paginated audit records, optionally filtered by tenant."""
        with self._lock:
            chain_copy = list(self._chain)

        if tenant_id and tenant_id != "system-root":
            chain_copy = [b for b in chain_copy if b.tenant_id == tenant_id]

        # Return latest entries first (descending)
        chain_copy.reverse()
        sliced = chain_copy[offset : offset + limit]
        return [b.to_dict() for b in sliced]

    @property
    def total_blocks(self) -> int:
        return len(self._chain)


# Global singleton Immutable Audit Logger
audit_logger = ImmutableAuditLogger()

"""Offline-first synchronization primitives for low-connectivity field workflows."""
from __future__ import annotations
import hashlib,json
from dataclasses import dataclass
from datetime import datetime,timezone

PROTOCOL_VERSION="1.0"

@dataclass(frozen=True)
class SyncEnvelope:
    device_id:str
    batch_id:str
    created_at:str
    protocol_version:str
    operations:tuple[dict,...]
    checksum:str

def make_envelope(device_id,batch_id,operations,created_at=None):
    ts=created_at or datetime.now(timezone.utc).isoformat()
    canonical=json.dumps(list(operations),sort_keys=True,separators=(",",":"),default=str)
    return SyncEnvelope(device_id,batch_id,ts,PROTOCOL_VERSION,tuple(operations),hashlib.sha256(canonical.encode()).hexdigest())

def verify_envelope(envelope:SyncEnvelope)->bool:
    canonical=json.dumps(list(envelope.operations),sort_keys=True,separators=(",",":"),default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()==envelope.checksum

def merge_operations(existing_ids:set[str],operations:list[dict]):
    accepted=[]; duplicates=[]
    for op in operations:
        oid=str(op.get("operation_id","")).strip()
        if not oid: raise ValueError("operation_id is required")
        if oid in existing_ids or any(x.get("operation_id")==oid for x in accepted): duplicates.append(oid)
        else: accepted.append(op)
    return accepted,duplicates

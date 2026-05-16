"""Simple in-memory audit log for admin actions (extend to DB later)."""

from datetime import datetime
from typing import List, Optional

_audit_log: List[dict] = []
_MAX_ENTRIES = 500


def log_action(
    admin_id: int,
    admin_phone: str,
    action: str,
    target: Optional[str] = None,
    details: Optional[dict] = None,
):
    _audit_log.insert(0, {
        "admin_id": admin_id,
        "admin_phone": admin_phone,
        "action": action,
        "target": target,
        "details": details or {},
        "created_at": datetime.utcnow().isoformat(),
    })
    if len(_audit_log) > _MAX_ENTRIES:
        _audit_log.pop()


def get_recent(limit: int = 50) -> List[dict]:
    return _audit_log[:limit]

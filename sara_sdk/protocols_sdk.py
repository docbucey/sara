"""SDK Protocols: convenience wrappers for each protocol lane."""
from __future__ import annotations

from typing import Any, Dict, Optional

from sara_sdk.dispatch_sdk import dispatch_sdk_protocol


def device_protocol(action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return dispatch_sdk_protocol("device", action, payload)


def arms_protocol(action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return dispatch_sdk_protocol("arm", action, payload)


def server_protocol(action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return dispatch_sdk_protocol("server", action, payload)


def ide_protocol(action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return dispatch_sdk_protocol("ide", action, payload)
